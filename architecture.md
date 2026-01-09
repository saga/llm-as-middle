# 架构设计 - Confluence Intelligent Agent

## 概述

这是一个基于LangGraph的智能MCP Server，与传统的工具提供者不同，它接收用户的自然语言问题，自主编排完整的工作流，返回最终结果。

## 核心理念

### 传统MCP Server
```
用户 → Copilot → 调用search工具 → 返回结果
                → 调用get_page工具 → 返回结果
                → Copilot整合回答
```

### Intelligent Agent (本项目)
```
用户 → Copilot → ask_confluence("API认证最佳实践是什么?")
                ↓
        Agent自主执行：
        1. LLM分析意图 → 生成搜索查询
        2. 搜索Confluence → 获取页面列表
        3. 批量获取页面 → 完整内容
        4. 保存到S3 → 归档备份
        5. LLM总结 → 生成答案
                ↓
         返回完整答案 + 引用 + S3链接
```

## 技术架构

### 1. MCP Server层
- **FastMCP**: 提供MCP协议服务器
- **SSE Transport**: Server-Sent Events传输
- **单一工具**: `ask_confluence(user_prompt: str)` - 接收自然语言问题

### 2. Agent层 (LangGraph)

#### State定义 (agent/state.py)
```python
class AgentState(TypedDict):
    user_prompt: str           # 用户输入
    search_query: str          # 生成的搜索查询
    search_results: list       # 搜索结果
    page_links: list           # 页面ID列表
    pages_content: list        # 完整页面内容
    s3_urls: list              # S3存储URL
    summary: str               # 内容总结
    final_response: str        # 最终响应
    messages: list             # LLM对话历史
    errors: list               # 错误记录
```

#### 工作流图 (agent/graph.py)
```
START
  ↓
analyze_prompt_node (分析用户意图)
  ↓
search_confluence_node (搜索Confluence)
  ↓
fetch_pages_node (批量获取页面)
  ↓
save_to_s3_node (保存到S3)
  ↓
summarize_node (LLM总结生成答案)
  ↓
END
```

#### 节点实现 (agent/nodes.py)

##### Node 1: analyze_prompt_node
**输入**: user_prompt
**处理**: 
- 使用LLM（GPT-4）分析用户问题
- 生成优化的Confluence CQL搜索查询
- 考虑时间过滤、space限制等
**输出**: search_query
**示例**:
```
用户问题: "最新的API文档在哪？"
生成查询: 'type=page AND space=DEV AND text ~ "API" AND lastModified > startOfMonth("-1M")'
```

##### Node 2: search_confluence_node
**输入**: search_query
**处理**:
- 调用Confluence MCP的confluence_search工具
- 通过OpenAI SDK + LiteLLM代理调用
- 提取页面ID列表
**输出**: search_results, page_links
**限制**: SEARCH_LIMIT环境变量（默认10）

##### Node 3: fetch_pages_node
**输入**: page_links
**处理**:
- 并发调用confluence_get_page获取每个页面
- 请求markdown格式 + 完整元数据
- 错误处理：部分失败不影响其他页面
**输出**: pages_content
**优化**: 使用asyncio并发提高速度

##### Node 4: save_to_s3_node
**输入**: pages_content
**处理**:
- 为每个页面创建JSON文件
- 上传到S3，路径：`confluence-docs/{timestamp}/{page_id}_{title}.json`
- 添加元数据：page-id, title, timestamp
**输出**: s3_urls
**配置**: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET

##### Node 5: summarize_node
**输入**: user_prompt, pages_content
**处理**:
- 构建包含用户问题和所有页面摘要的上下文
- 调用LLM生成针对性回答
- 包含页面引用（标题+URL）
- 附加S3备份链接
**输出**: summary, final_response
**提示词策略**: 
- 要求直接回答问题
- 引用具体页面作为依据
- 说明不完全匹配的情况

### 3. 客户端层

#### Confluence客户端 (clients/confluence.py)
**方式**: OpenAI SDK + LiteLLM Proxy
**工具**:
- `search_pages(query, limit, spaces_filter)` → confluence_search
- `get_page(page_id, ...)` → confluence_get_page

**流程**:
```python
client = AsyncOpenAI(
    api_key=LITELLM_API_KEY,
    base_url=LITELLM_BASE_URL
)

# LiteLLM会将这个调用桥接到Confluence MCP Server
response = await client.chat.completions.create(
    model=CONFLUENCE_MODEL,
    messages=[...],
    tools=[tool_definition]
)
```

#### 备选方案 (clients/confluence_mcp_direct.py)
**方式**: 直接MCP客户端连接
**用途**: 如果不使用LiteLLM，直接连接Confluence MCP

### 4. 外部依赖

#### Confluence MCP Server (sooperset/mcp-atlassian)
**工具**:
- `confluence_search`: 搜索Confluence页面
- `confluence_get_page`: 获取页面内容

**部署**: 独立服务，通过LiteLLM暴露为OpenAI兼容API

#### LiteLLM Proxy
**作用**: 
- 桥接OpenAI SDK调用到MCP Server
- 统一API格式
- 处理认证和路由

**配置**:
```yaml
model_list:
  - model_name: confluence-mcp
    litellm_params:
      model: mcp/confluence
      mcp_server_url: http://confluence-mcp:8080/sse
```

#### LLM服务 (GPT-4)
**用途**:
- 意图分析（analyze_prompt_node）
- 内容总结（summarize_node）

**配置**: OPENAI_API_KEY, OPENAI_API_BASE

#### AWS S3
**用途**: 文档归档备份
**配置**: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET

## 部署架构

### Kubernetes部署
```
┌──────────────────────────────────────────┐
│           VS Code Copilot Chat           │
└───────────────┬──────────────────────────┘
                │ MCP over SSE
                ▼
┌──────────────────────────────────────────┐
│  confluence-agent Service (ClusterIP)    │
│  Port: 8000                              │
└───────────────┬──────────────────────────┘
                │
                ▼
┌──────────────────────────────────────────┐
│  confluence-agent Deployment             │
│  Replicas: 2                             │
│  Resources: 512Mi-1Gi / 500m-1000m       │
│  Health: /health endpoint                │
└─┬───────────┬──────────────┬─────────────┘
  │           │              │
  │           │              │
  ▼           ▼              ▼
┌───────┐  ┌────────┐  ┌──────────┐
│LiteLLM│  │OpenAI  │  │AWS S3    │
│Proxy  │  │API     │  │Bucket    │
└───┬───┘  └────────┘  └──────────┘
    │
    ▼
┌─────────────────┐
│ Confluence MCP  │
│ Server          │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Confluence API  │
└─────────────────┘
```

### 环境变量配置
```yaml
# Confluence MCP连接
LITELLM_BASE_URL: http://litellm-proxy:4000
LITELLM_API_KEY: <from secret>
CONFLUENCE_MODEL: confluence-mcp

# LLM配置
OPENAI_API_KEY: <from secret>
OPENAI_API_BASE: https://api.openai.com/v1
LLM_MODEL: gpt-4

# S3配置
AWS_ACCESS_KEY_ID: <from secret>
AWS_SECRET_ACCESS_KEY: <from secret>
AWS_REGION: us-east-1
S3_BUCKET: confluence-docs-backup

# Agent配置
SEARCH_LIMIT: 10
```

### Secret管理
```bash
kubectl create secret generic confluence-agent-secret \
  --from-literal=litellm-api-key=$LITELLM_API_KEY \
  --from-literal=openai-api-key=$OPENAI_API_KEY \
  --from-literal=aws-access-key=$AWS_ACCESS_KEY_ID \
  --from-literal=aws-secret-key=$AWS_SECRET_ACCESS_KEY
```

## 数据流

### 完整请求流程
```
1. 用户在Copilot Chat输入：
   "团队的API认证最佳实践是什么？"

2. Copilot调用MCP工具：
   ask_confluence("团队的API认证最佳实践是什么？")

3. Agent执行工作流：
   
   Step 1 - analyze_prompt_node:
   - 调用GPT-4分析意图
   - 生成查询: 'text ~ "API 认证 最佳实践"'
   
   Step 2 - search_confluence_node:
   - OpenAI SDK → LiteLLM → Confluence MCP
   - 调用: confluence_search(query="text ~ \"API 认证 最佳实践\"", limit=10)
   - 返回: [
       {id: "12345", title: "API Security Guidelines", ...},
       {id: "67890", title: "Authentication Best Practices", ...}
     ]
   
   Step 3 - fetch_pages_node:
   - 并发获取页面12345和67890
   - 调用: confluence_get_page(page_id="12345", convert_to_markdown=True)
   - 返回: 完整markdown内容 + 元数据
   
   Step 4 - save_to_s3_node:
   - 上传到S3:
     s3://confluence-docs-backup/confluence-docs/20260109_143022/12345_API_Security_Guidelines.json
     s3://confluence-docs-backup/confluence-docs/20260109_143022/67890_Authentication_Best_Practices.json
   
   Step 5 - summarize_node:
   - 构建上下文：用户问题 + 页面内容
   - 调用GPT-4生成总结
   - 返回格式化的答案 + 引用 + S3链接

4. 返回给Copilot Chat:
   "根据Confluence文档，API认证的最佳实践包括：
    1. 使用OAuth 2.0 - 参考《API Security Guidelines》...
    📚 相关文档已保存到S3: ..."
```

## 性能考虑

### 并发处理
- fetch_pages_node使用asyncio并发获取多个页面
- 典型场景：10个页面，串行需10s，并发仅需1-2s

### 资源限制
- 内存：512Mi-1Gi（处理大量文档内容）
- CPU：500m-1000m（LLM API调用为主，CPU要求不高）
- 副本数：2（高可用）

### 错误处理
- 部分页面获取失败不影响其他页面
- S3保存失败会记录但继续总结
- 每个节点捕获异常，记录到state.errors
- 最终响应包含错误提示

### 超时配置
- LLM API调用：默认60s
- Confluence MCP调用：默认30s
- S3上传：默认10s/文件
- 总体工作流：<2分钟

## 扩展性

### 添加新数据源
1. 在clients/创建新客户端
2. 在agent/nodes.py添加新节点
3. 在agent/graph.py更新工作流图

### 支持其他存储
1. 继承save_to_s3_node
2. 实现不同的存储后端（Azure Blob, GCS等）
3. 通过环境变量切换

### 自定义工作流
1. 修改agent/graph.py的边定义
2. 添加条件分支（如根据搜索结果数量决定是否继续）
3. 支持循环（如搜索→获取→再搜索）

## 监控和日志

### 日志级别
- INFO: 工作流步骤、页面数量、成功/失败
- WARNING: 部分失败、降级处理
- ERROR: 节点执行失败、API错误
- DEBUG: 详细的请求/响应

### 关键指标
- 工作流执行时间
- 每个节点耗时
- 页面获取成功率
- S3上传成功率
- LLM token使用量

### K8s健康检查
- Liveness: /health endpoint（30s间隔）
- Readiness: /health endpoint（10s初始延迟）
- 自动重启失败的Pod

## 安全考虑

### Secret管理
- 所有API密钥存储在K8s Secret
- 通过环境变量注入，不写入代码
- Secret权限限制为特定ServiceAccount

### 网络隔离
- Agent仅在集群内通过ClusterIP暴露
- Confluence MCP仅集群内访问
- S3访问通过IAM角色（生产环境）

### 数据保护
- S3存储的文档可配置加密
- 传输层使用HTTPS（S3, OpenAI API）
- 敏感信息不记录到日志

## 成本优化

### LLM调用
- analyze_prompt: ~200 tokens/次
- summarize: ~2000 tokens/次（取决于页面数量）
- 使用GPT-3.5-turbo可降低70%成本（牺牲质量）

### S3存储
- 生命周期策略：30天后归档到Glacier
- 对象过期：90天后删除
- 月成本估算：10k文档 ≈ $1-2

### Confluence API
- 通过MCP缓存减少重复请求
- 批量获取优化网络开销

## 未来优化

### 智能缓存
- 缓存常见查询结果（Redis）
- 页面内容缓存（避免重复获取）
- LLM响应缓存

### 工作流优化
- 动态调整搜索数量（根据结果相关性）
- 智能过滤（跳过不相关页面）
- 增量更新（仅获取变更内容）

### 多模态支持
- 处理Confluence中的图片、图表
- 生成可视化总结
- 支持表格数据提取

### 用户反馈
- 收集用户对答案的评分
- 基于反馈优化提示词
- A/B测试不同工作流
