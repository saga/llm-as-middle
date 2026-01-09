# 变更日志

## v0.3.0 - MSAL认证集成 (2026-01-09)

### 🔐 新增功能

#### Azure AD MSAL认证
- **Microsoft Authentication Library (MSAL)集成**: 使用MSAL获取Azure AD访问令牌
- **Client Credentials流程**: 通过Tenant ID、Client ID和Client Secret获取token
- **自动Token管理**: MSAL自动处理token缓存和刷新
- **LiteLLM集成**: 获取的token用于调用LiteLLM proxy

#### 新增模块
- `auth/msal_auth.py`: MSAL Token管理器实现
- `auth/__init__.py`: 认证模块接口

#### 配置变更
- **新环境变量**:
  - `AZURE_TENANT_ID`: Azure AD租户ID
  - `AZURE_CLIENT_ID`: 应用客户端ID
  - `AZURE_CLIENT_SECRET`: 客户端密钥
  - `AZURE_SCOPE`: 认证scope（默认: `https://cognitiveservices.azure.com/.default`）
- **移除环境变量**:
  - `OPENAI_API_KEY`: 不再需要，使用MSAL token代替
  - `LITELLM_API_KEY`: 不再需要，使用MSAL token代替

### 📚 新增文档
- `MSAL_AUTH_GUIDE.md`: 详细的MSAL认证配置指南
- `QUICKSTART_MSAL.md`: 快速开始配置步骤
- `.env.example.full`: 完整的配置示例文件
- `test_msal_auth.py`: MSAL认证测试脚本

### 🔧 代码更新
- `agent/nodes.py`: 
  - 修改LLM初始化使用MSAL token
  - 新增`get_llm()`函数自动获取和配置token
- `.env.example`: 更新为MSAL认证配置
- `README.md`: 添加MSAL认证说明

### 🧪 测试工具
运行测试脚本验证配置：
```bash
python test_msal_auth.py
```

### 📦 依赖更新
```toml
msal = ">=1.24.0"  # Microsoft Authentication Library
```

### ⚠️ 破坏性变更
- LLM认证方式从静态API key改为动态MSAL token
- 需要在Azure Portal配置应用注册
- 环境变量配置有较大变化，请参考 `QUICKSTART_MSAL.md`

### 🔄 迁移指南
从v0.2.0升级到v0.3.0:

1. **Azure Portal配置**:
   - 创建Azure AD应用注册
   - 获取Tenant ID、Client ID、Client Secret
   - 配置API权限并授予管理员同意

2. **更新环境变量**:
   ```bash
   # 删除
   - OPENAI_API_KEY
   - LITELLM_API_KEY
   
   # 添加
   + AZURE_TENANT_ID
   + AZURE_CLIENT_ID
   + AZURE_CLIENT_SECRET
   + AZURE_SCOPE
   ```

3. **测试认证**:
   ```bash
   python test_msal_auth.py
   ```

详细步骤: [QUICKSTART_MSAL.md](QUICKSTART_MSAL.md)

---

## v0.2.0 - LangGraph智能Agent重构 (2026-01-09)

### 🚀 重大变更

#### 架构转型
- **从工具提供者到智能Agent**: 不再是简单的search/get工具转发，而是接收用户prompt，自主编排完整工作流
- **LangGraph工作流**: 引入5步骤智能工作流：意图分析 → 搜索 → 获取 → 归档 → 总结
- **单一接口**: 现在只提供一个工具 `ask_confluence(user_prompt)` 接收自然语言问题

#### 新增功能
- **意图分析节点** (analyze_prompt_node): 使用LLM分析用户问题，生成优化的CQL搜索查询
- **S3自动归档** (save_to_s3_node): 所有检索的文档自动保存到S3，带时间戳和元数据
- **智能总结** (summarize_node): LLM基于实际页面内容生成答案，包含引用和S3链接
- **并发优化** (fetch_pages_node): 异步并发获取多个页面，大幅提升速度
- **错误容忍**: 部分失败不影响整体流程，记录errors供用户查看

### 📦 新增依赖
```toml
langgraph = ">=0.2.0"        # 工作流编排
langchain = ">=0.3.0"        # LLM抽象
langchain-openai = ">=0.2.0" # OpenAI集成
boto3 = ">=1.35.0"           # AWS S3客户端
pydantic = ">=2.0.0"         # 数据验证
```

### 📁 新增文件

#### Agent模块 (`agent/`)
- `state.py`: AgentState定义，包含工作流所有状态字段
- `nodes.py`: 5个工作流节点实现
  - `analyze_prompt_node`: 意图分析
  - `search_confluence_node`: Confluence搜索
  - `fetch_pages_node`: 批量获取页面
  - `save_to_s3_node`: S3归档
  - `summarize_node`: LLM总结
- `graph.py`: LangGraph工作流图定义和编译
- `__init__.py`: 模块导出

#### 文档
- `ARCHITECTURE.md`: 详细架构设计文档（70+ KB）
- `QUICKSTART.md`: 5分钟快速开始指南
- `architecture.txt`: ASCII架构图（更新）

### 🔧 文件修改

#### `server.py`
**之前**: 提供2个工具
```python
@mcp.tool()
async def confluence_search(query, limit, spaces_filter):
    ...

@mcp.tool()
async def confluence_get_page(page_id, title, space_key, ...):
    ...
```

**现在**: 提供1个智能工具
```python
@mcp.tool()
async def ask_confluence(user_prompt: str) -> str:
    """智能Confluence助手 - 自动搜索、获取、保存和总结"""
    result = await run_agent(user_prompt)
    return result["response"]
```

#### `pyproject.toml`
- 版本: 0.1.0 → 0.2.0
- 描述: "MCP Server for Confluence queries" → "Intelligent MCP Agent for Confluence with LangGraph workflow"
- 新增6个依赖包

#### `.env.example`
新增环境变量：
```env
# LLM配置（用于Agent）
OPENAI_API_KEY=...
OPENAI_API_BASE=...
LLM_MODEL=gpt-4

# AWS S3配置
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=us-east-1
S3_BUCKET=confluence-docs-backup

# Agent配置
SEARCH_LIMIT=10
```

#### `k8s.yml`
- Deployment名称: doc-mcp-server → confluence-agent
- Secret名称: litellm-secret → confluence-agent-secret
- 新增环境变量注入：OpenAI API、AWS凭证
- 资源调整: 256Mi-512Mi → 512Mi-1Gi（处理更多数据）
- CPU调整: 200m-500m → 500m-1000m

#### `Dockerfile`
- 新增复制 `agent/` 目录

#### `README.md`
- 完全重写，聚焦智能Agent特性
- 新增架构图（ASCII art）
- 新增使用示例（展示工作流效果）
- 技术栈表格
- 工作流节点说明

### 🎯 工作流详解

```
用户提问 "团队的API认证最佳实践是什么？"
    ↓
[1] analyze_prompt_node
    - 调用GPT-4分析意图
    - 生成: 'text ~ "API 认证 最佳实践"'
    ↓
[2] search_confluence_node
    - 调用Confluence MCP搜索
    - 返回: 10个相关页面ID
    ↓
[3] fetch_pages_node (并发)
    - 同时获取10个页面内容
    - 转换为Markdown格式
    ↓
[4] save_to_s3_node
    - 上传到S3: confluence-docs/{timestamp}/{id}_{title}.json
    - 带元数据: page-id, title, timestamp
    ↓
[5] summarize_node
    - GPT-4基于页面内容生成答案
    - 包含引用（标题+URL）
    - 附加S3备份链接
    ↓
返回完整回答给用户
```

### 📊 性能提升

- **并发获取**: 10个页面从10s降到1-2s（~80%提升）
- **智能过滤**: LLM生成的查询比简单关键词更精准
- **一次调用**: 用户只需一次`ask_confluence`调用，无需多次往返

### 🔐 安全增强

- AWS凭证通过K8s Secret管理
- OpenAI API Key隔离存储
- S3可配置服务端加密
- 日志不输出敏感信息

### 💰 成本考虑

每次查询的LLM token使用：
- analyze_prompt: ~200 tokens
- summarize: ~2000-5000 tokens（取决于页面数量）
- 总计: ~2500 tokens/查询（GPT-4约$0.10）

S3存储：
- 10页面/查询 × 100KB/页 = 1MB/查询
- 1000次查询/月 ≈ 1GB ≈ $0.02/月

### ⚠️ 破坏性变更

1. **MCP工具接口完全改变**
   - 移除: `confluence_search`, `confluence_get_page`
   - 新增: `ask_confluence`
   - 迁移: 客户端需要适配新的调用方式

2. **环境变量要求**
   - 新增必需变量: OPENAI_API_KEY, OPENAI_API_BASE, LLM_MODEL
   - 新增可选变量: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, S3_BUCKET

3. **K8s配置**
   - Secret名称变更
   - Deployment/Service名称变更
   - 需要重新创建Secret和部署

### 📝 迁移指南

#### 从v0.1.x迁移到v0.2.0

1. **更新环境变量**
```bash
# 在.env中添加
OPENAI_API_KEY=your-key
OPENAI_API_BASE=https://api.openai.com/v1
LLM_MODEL=gpt-4

# 可选：如果使用S3
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
S3_BUCKET=confluence-docs-backup
```

2. **更新K8s部署**
```bash
# 删除旧资源
kubectl delete deployment doc-mcp-server
kubectl delete service doc-mcp-server
kubectl delete secret litellm-secret

# 创建新Secret
kubectl create secret generic confluence-agent-secret \
  --from-literal=litellm-api-key=$LITELLM_API_KEY \
  --from-literal=openai-api-key=$OPENAI_API_KEY \
  --from-literal=aws-access-key=$AWS_ACCESS_KEY_ID \
  --from-literal=aws-secret-key=$AWS_SECRET_ACCESS_KEY

# 部署新版本
kubectl apply -f k8s.yml
```

3. **更新VS Code配置**
```json
{
  "github.copilot.chat.mcp.servers": {
    "confluence-agent": {  // 新名称
      "command": "http",
      "args": ["http://confluence-agent:8000/sse"]  // 新服务名
    }
  }
}
```

4. **调用方式变更**

**之前**（v0.1.x）:
```
Copilot会自动调用:
1. confluence_search("API文档")
2. confluence_get_page(page_id="12345")
3. 自己整合结果
```

**现在**（v0.2.0）:
```
用户直接问:
"API文档在哪里？"

Agent自动完成所有步骤并返回最终答案
```

### 🚫 临时禁用S3（可选）

如果暂时没有S3，可以跳过save_to_s3节点：

编辑`agent/graph.py`:
```python
# workflow.add_edge("fetch_pages", "save_to_s3")
# workflow.add_edge("save_to_s3", "summarize")
workflow.add_edge("fetch_pages", "summarize")  # 直接跳到总结
```

### 🎉 使用示例

**问**: "最近的系统架构设计文档有哪些？"

**返回**:
```
根据Confluence最近更新的文档，以下是主要的系统架构设计：

1. **微服务架构v2.0** - 2025-12-15更新
   详细介绍了新的微服务拆分策略...
   URL: https://confluence.example.com/pages/12345

2. **API Gateway设计** - 2025-12-10更新
   包含路由规则、限流策略...
   URL: https://confluence.example.com/pages/67890

---
📚 相关文档已保存到S3:
- s3://confluence-docs-backup/confluence-docs/20260109_143022/12345_Microservices_v2.json
- s3://confluence-docs-backup/confluence-docs/20260109_143022/67890_API_Gateway.json
```

### 🔮 未来计划

- [ ] 智能缓存（Redis）减少重复查询
- [ ] 动态调整搜索数量（基于结果相关性）
- [ ] 支持图片、表格提取
- [ ] 用户反馈收集和工作流优化
- [ ] 多轮对话支持（记忆上下文）
- [ ] 支持其他文档系统（Notion, Google Docs）

---

## v0.1.0 - 初始版本 (2026-01-08)

### 功能
- FastMCP Server基础框架
- 通过LiteLLM Proxy调用Confluence MCP
- 提供confluence_search和confluence_get_page工具
- K8s部署配置
- Docker支持

### 依赖
- mcp >= 1.0.0
- openai >= 1.0.0
- uvicorn, starlette

### 文档
- README.md
- DEPLOY.md
- CONFIG.md
- TESTING.md
