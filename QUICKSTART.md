# 快速开始指南

## 前置条件

1. **Confluence MCP Server** - 已部署sooperset/mcp-atlassian
2. **LiteLLM Proxy** - 配置为桥接Confluence MCP
3. **OpenAI API** - 用于意图分析和总结
4. **AWS S3** - 用于文档归档（可选）

## 5分钟快速部署

### 步骤1: 配置环境变量

```bash
cp .env.example .env
```

编辑`.env`：
```env
# Confluence MCP（必需）
LITELLM_BASE_URL=http://localhost:4000
LITELLM_API_KEY=your-litellm-key
CONFLUENCE_MODEL=confluence-mcp

# OpenAI（必需）
OPENAI_API_KEY=sk-your-openai-key
OPENAI_API_BASE=https://api.openai.com/v1
LLM_MODEL=gpt-4

# AWS S3（可选）
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
S3_BUCKET=confluence-docs-backup
```

### 步骤2: 安装依赖

```bash
uv sync
```

### 步骤3: 运行服务

```bash
python main.py
```

### 步骤4: 配置VS Code

在`settings.json`中添加：

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

### 步骤5: 测试使用

在Copilot Chat中：
```
@workspace #confluence-agent 团队的API文档在哪里？
```

## Kubernetes部署

```bash
# 创建Secret
kubectl create secret generic confluence-agent-secret \
  --from-literal=litellm-api-key=$LITELLM_API_KEY \
  --from-literal=openai-api-key=$OPENAI_API_KEY \
  --from-literal=aws-access-key=$AWS_ACCESS_KEY_ID \
  --from-literal=aws-secret-key=$AWS_SECRET_ACCESS_KEY

# 部署
kubectl apply -f k8s.yml
```

## 临时禁用S3（测试）

编辑`agent/graph.py`：
```python
# 跳过S3节点
workflow.add_edge("fetch_pages", "summarize")
```

查看[ARCHITECTURE.md](ARCHITECTURE.md)了解详细架构设计。
