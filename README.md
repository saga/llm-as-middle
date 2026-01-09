# Confluence Intelligent Agent (MCP Server)

基于LangGraph的智能Confluence文档助手，为VS Code Copilot Chat提供智能文档检索、总结和归档服务。

## 🌟 核心特性

### 智能工作流（LangGraph驱动）
当用户提出问题时，Agent会自动执行以下步骤：

1. **📋 意图分析** - 使用LLM分析用户问题，生成最优Confluence搜索查询
2. **🔍 智能搜索** - 在Confluence中搜索相关文档
3. **📄 内容获取** - 批量获取搜索到的页面完整内容
4. **💾 S3归档** - 将所有页面内容保存到S3（带时间戳和元数据）
5. **🤖 智能总结** - 基于页面内容回答用户问题，提供引用链接

### 与传统MCP Server的区别
- **传统**: 提供简单的search/get工具，由客户端（Copilot）决定如何使用
- **本项目**: 接收用户自然语言问题，自主编排完整工作流，返回最终结果

## 🏗️ 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                    VS Code Copilot Chat                      │
└─────────────────────┬───────────────────────────────────────┘
                      │ MCP Protocol (SSE)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│              Confluence Intelligent Agent                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              LangGraph Workflow                      │   │
│  │                                                       │   │
│  │  1. Analyze Prompt    → LLM分析用户意图              │   │
│  │  2. Search Confluence → 调用Confluence MCP           │   │
│  │  3. Fetch Pages       → 批量获取页面                 │   │
│  │  4. Save to S3        → 归档到云存储                 │   │
│  │  5. Summarize         → LLM生成总结回答              │   │
│  └─────────────────────────────────────────────────────┘   │
└────┬──────────────────┬──────────────────┬─────────────────┘
     │                  │                  │
     ▼                  ▼                  ▼
┌──────────┐    ┌──────────────┐    ┌──────────┐
│Confluence│    │  LLM (GPT-4) │    │ AWS S3   │
│   MCP    │    │ via LiteLLM  │    │  Bucket  │
└──────────┘    └──────────────┘    └──────────┘
```

## 🚀 快速开始

### 1. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env填入配置
```

必需的环境变量：
```env
# Azure AD认证（用于获取LiteLLM访问令牌）
AZURE_TENANT_ID=your-tenant-id
AZURE_CLIENT_ID=your-client-id
AZURE_CLIENT_SECRET=your-client-secret
AZURE_SCOPE=https://cognitiveservices.azure.com/.default

# Confluence MCP（通过LiteLLM调用）
LITELLM_BASE_URL=http://localhost:4000
CONFLUENCE_MODEL=confluence-mcp

# LLM（用于意图分析和总结）
LLM_MODEL=gpt-4

# AWS S3（用于文档归档）
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_REGION=us-east-1
S3_BUCKET=confluence-docs-backup

# 可选配置
SEARCH_LIMIT=10  # 最多搜索多少个页面
```

**重要**: 详细的Azure AD认证配置请参考 [MSAL认证集成说明](MSAL_AUTH_GUIDE.md)

### 2. 安装依赖

```bash
# 使用uv（推荐）
uv sync

# 或使用pip
pip install -e .
```

### 3. 运行服务

```bash
# 本地开发
python main.py
```

### 4. VS Code配置

在VS Code的`settings.json`中添加：

```json
{
  "github.copilot.chat.mcp.servers": {
    "confluence-agent": {
      "command": "http",
      "args": ["http://localhost:8000/sse"]
    }
  }
}
```

## 💡 使用示例

在VS Code Copilot Chat中：

```
@workspace 使用 #confluence-agent

问：团队的API认证最佳实践是什么？
```

Agent会自动完成工作流并返回：

```
根据Confluence文档，API认证的最佳实践包括：

1. **使用OAuth 2.0** - 参考《API Security Guidelines》
   - 实现Token过期和刷新机制
   - 使用HTTPS确保传输安全
   
2. **API Key管理** - 参考《Authentication Best Practices》
   - 定期轮换API密钥
   - 为不同环境使用不同的密钥

---
📚 相关文档已保存到S3:
- s3://confluence-docs-backup/confluence-docs/20260109_143022/12345_API_Security_Guidelines.json
- s3://confluence-docs-backup/confluence-docs/20260109_143022/67890_Authentication_Best_Practices.json
```

## 🛠️ 技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| MCP Server | FastMCP | 与VS Code Copilot通信 |
| 工作流编排 | LangGraph | 多步骤Agent工作流 |
| LLM调用 | LangChain + OpenAI SDK | 意图分析、内容总结 |
| Confluence集成 | MCP Client (via LiteLLM) | 搜索和获取Confluence内容 |
| 存储 | boto3 + AWS S3 | 文档归档 |
| 服务器 | uvicorn + Starlette | HTTP/SSE服务 |

## 📦 部署

### Kubernetes

```bash
# 创建Secret
kubectl create secret generic confluence-agent-secret \
  --from-literal=litellm-api-key=your-key \
  --from-literal=openai-api-key=your-key \
  --from-literal=aws-access-key=your-key \
  --from-literal=aws-secret-key=your-secret

# 部署
kubectl apply -f k8s.yml

# 检查
kubectl get pods -l app=confluence-agent
kubectl logs -f deployment/confluence-agent
```

## 🔧 开发

### 认证机制

本项目使用 **Microsoft Authentication Library (MSAL)** 实现Azure AD认证：

1. **Client Credentials流程**: 使用Azure AD应用的Client ID和Secret获取访问令牌
2. **自动Token管理**: MSAL自动处理token缓存和刷新
3. **与LiteLLM集成**: 获取的token用于调用LiteLLM proxy

详细配置指南: [MSAL_AUTH_GUIDE.md](MSAL_AUTH_GUIDE.md)

### 项目结构

```
├── agent/                  # LangGraph Agent实现
│   ├── state.py           # Agent状态定义
│   ├── nodes.py           # 工作流节点（5个步骤）
│   ├── graph.py           # LangGraph图定义
│   └── __init__.py
├── auth/                  # 认证模块
│   ├── msal_auth.py      # MSAL Token管理器
│   └── __init__.py
├── clients/               # 外部服务客户端
│   ├── confluence.py     # Confluence MCP客户端
│   └── confluence_mcp_direct.py  # 直接MCP连接（备选）
├── server.py             # MCP Server定义
├── main.py               # 应用入口
├── k8s.yml               # Kubernetes配置
├── MSAL_AUTH_GUIDE.md    # MSAL认证配置指南
└── pyproject.toml        # 项目依赖
```

### 工作流细节

**节点1: analyze_prompt** - 分析用户意图
- 输入：用户问题
- 处理：LLM生成CQL搜索查询
- 输出：搜索查询字符串

**节点2: search_confluence** - 搜索文档
- 输入：搜索查询
- 处理：调用Confluence MCP
- 输出：页面ID列表

**节点3: fetch_pages** - 获取内容
- 输入：页面ID
- 处理：并发获取完整内容
- 输出：页面内容列表

**节点4: save_to_s3** - 归档备份
- 输入：页面内容
- 处理：上传S3带元数据
- 输出：S3 URL列表

**节点5: summarize** - 生成答案
- 输入：用户问题 + 页面内容
- 处理：LLM总结生成答案
- 输出：最终响应

## 🐛 故障排查

### 常见问题

**Q: Agent执行失败**
- 检查LLM API配置（OPENAI_API_KEY）
- 检查Confluence MCP连接（LITELLM_BASE_URL）
- 查看日志中的详细错误

**Q: S3保存失败**
- 验证AWS凭证
- 确认S3 Bucket存在且有写权限

**Q: 搜索结果为空**
- 检查Confluence MCP是否正常
- 尝试更简单的查询

## 📄 许可证

MIT License
