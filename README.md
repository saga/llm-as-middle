# Enterprise Doc Agent - MCP Server

这是一个运行在Kubernetes中的MCP (Model Context Protocol) Server，用于VS Code Copilot Chat查询Confluence文档。

## 架构

```
VS Code Copilot Chat
        ↓
   Doc MCP Server (本服务)
        ↓
   LiteLLM Proxy
        ↓
  Confluence MCP Server
        ↓
   Confluence API
```

## 功能

- **MCP Server**: 提供SSE传输协议的MCP服务，可被VS Code Copilot Chat调用
- **Confluence集成**: 通过LiteLLM Proxy桥接到Confluence MCP Server
- **工具**:
  - `search_confluence`: 搜索Confluence页面
  - `get_confluence_page`: 获取指定页面内容

## 技术栈

- **Python 3.12+**
- **FastMCP**: MCP Server框架
- **OpenAI SDK**: 通过LiteLLM Proxy调用其他MCP服务
- **Kubernetes**: 容器编排
- **Docker**: 容器化部署

## 本地开发

### 安装依赖

```bash
# 使用uv包管理器
uv sync

# 或使用pip
pip install -e .
```

### 配置环境变量

创建 `.env` 文件：

```env
LITELLM_BASE_URL=http://localhost:4000
LITELLM_API_KEY=your-api-key
CONFLUENCE_MODEL=confluence-mcp
```

### 运行服务

```bash
python main.py
```

服务将在 `http://0.0.0.0:8000` 启动，使用SSE传输协议。

### 测试健康检查

```bash
curl http://localhost:8000/health
```

## Docker构建

```bash
# 构建镜像
docker build -t your-org/doc-mcp:latest .

# 运行容器
docker run -p 8000:8000 \
  -e LITELLM_BASE_URL=http://litellm-proxy:4000 \
  -e LITELLM_API_KEY=your-key \
  your-org/doc-mcp:latest
```

## Kubernetes部署

### 前置要求

1. 已部署LiteLLM Proxy服务
2. LiteLLM Proxy已配置Confluence MCP Server

### 部署步骤

1. 更新Secret中的API密钥：

```bash
kubectl edit secret litellm-secret
```

2. 应用配置：

```bash
kubectl apply -f k8s.yml
```

3. 检查部署状态：

```bash
kubectl get pods -l app=doc-mcp
kubectl logs -l app=doc-mcp
```

4. 验证服务：

```bash
kubectl port-forward svc/doc-mcp 8000:8000
curl http://localhost:8000/health
```

## VS Code Copilot Chat配置

在VS Code settings.json中添加：

```json
{
  "github.copilot.chat.codeGeneration.useInstructionFiles": true,
  "github.copilot.advanced": {
    "mcp": {
      "servers": {
        "enterprise-doc": {
          "transport": "sse",
          "url": "http://doc-mcp:8000/sse"
        }
      }
    }
  }
}
```

## 环境变量

| 变量 | 描述 | 默认值 |
|------|------|--------|
| `LITELLM_BASE_URL` | LiteLLM Proxy地址 | `http://litellm-proxy:4000` |
| `LITELLM_API_KEY` | LiteLLM API密钥 | `dummy-key` |
| `CONFLUENCE_MODEL` | Confluence模型名称 | `confluence-mcp` |

## API端点

- `GET /health` - 健康检查
- `POST /sse` - MCP SSE传输端点

## 故障排查

### 服务无法启动

检查日志：
```bash
kubectl logs -l app=doc-mcp --tail=100
```

### 无法连接到LiteLLM Proxy

1. 验证LiteLLM服务是否运行：
```bash
kubectl get svc litellm-proxy
```

2. 测试连接：
```bash
kubectl exec -it <pod-name> -- curl http://litellm-proxy:4000/health
```

### VS Code无法连接MCP Server

1. 确保服务可访问（根据网络配置可能需要Ingress）
2. 检查VS Code MCP配置
3. 查看VS Code输出面板的MCP日志

## 开发计划

- [ ] 添加认证和授权
- [ ] 支持更多Confluence操作
- [ ] 添加缓存层
- [ ] 监控和日志聚合
- [ ] 性能优化

## 许可证

MIT