# 测试命令集合

## 语法检查
```bash
# 检查Python语法错误
D:/temp/llm-as-middle/.venv/Scripts/python.exe -m py_compile main.py
D:/temp/llm-as-middle/.venv/Scripts/python.exe -m py_compile server.py
D:/temp/llm-as-middle/.venv/Scripts/python.exe -m py_compile clients/confluence.py
```

## 本地运行测试

### 1. 设置环境变量
```bash
# Windows PowerShell
$env:LITELLM_BASE_URL="http://localhost:4000"
$env:LITELLM_API_KEY="your-api-key"
$env:CONFLUENCE_MODEL="confluence-mcp"
```

### 2. 启动服务
```bash
python main.py
```

### 3. 测试健康检查
```bash
# 新开一个终端
curl http://localhost:8000/health

# 或使用PowerShell
Invoke-WebRequest -Uri http://localhost:8000/health | Select-Object -Expand Content
```

### 4. 测试MCP端点（需要MCP客户端工具）
```bash
# 使用MCP Inspector工具
mcp-inspector http://localhost:8000/sse
```

## Docker测试

### 构建镜像
```bash
docker build -t doc-mcp:test .
```

### 运行容器
```bash
docker run -p 8000:8000 `
  -e LITELLM_BASE_URL=http://host.docker.internal:4000 `
  -e LITELLM_API_KEY=your-key `
  doc-mcp:test
```

### 测试容器
```bash
# 健康检查
docker ps  # 查看容器状态
curl http://localhost:8000/health

# 查看日志
docker logs <container-id>
```

## Kubernetes测试

### 部署
```bash
# 应用配置
kubectl apply -f k8s.yml

# 查看状态
kubectl get pods -l app=doc-mcp
kubectl get svc doc-mcp
```

### 测试
```bash
# 端口转发
kubectl port-forward svc/doc-mcp 8000:8000

# 在另一个终端测试
curl http://localhost:8000/health
```

### 查看日志
```bash
kubectl logs -l app=doc-mcp -f
```

### 调试
```bash
# 进入容器
kubectl exec -it <pod-name> -- /bin/sh

# 测试网络连接
kubectl exec -it <pod-name> -- curl http://litellm-proxy:4000/health
```

## VS Code Copilot测试

### 配置
在VS Code的 `settings.json` 添加：

```json
{
  "github.copilot.advanced": {
    "mcp": {
      "servers": {
        "enterprise-doc": {
          "transport": "sse",
          "url": "http://localhost:8000/sse"
        }
      }
    }
  }
}
```

### 测试对话
在Copilot Chat中输入：

```
@enterprise-doc 搜索关于API的文档
```

或

```
@enterprise-doc 获取页面ID为12345的内容
```

## 性能测试

### 负载测试
```bash
# 安装 wrk
# Windows: scoop install wrk

# 测试健康检查端点
wrk -t4 -c100 -d30s http://localhost:8000/health
```

### 并发测试
```python
# test_concurrent.py
import asyncio
import httpx

async def test_health():
    async with httpx.AsyncClient() as client:
        tasks = [client.get("http://localhost:8000/health") for _ in range(100)]
        responses = await asyncio.gather(*tasks)
        success = sum(1 for r in responses if r.status_code == 200)
        print(f"Success: {success}/100")

asyncio.run(test_health())
```

## 故障排查命令

### 检查端口占用
```bash
# Windows
netstat -ano | findstr :8000

# Linux/Mac
lsof -i :8000
```

### 检查Python环境
```bash
D:/temp/llm-as-middle/.venv/Scripts/python.exe --version
D:/temp/llm-as-middle/.venv/Scripts/python.exe -m pip list
```

### 检查依赖
```bash
uv pip check
```

### 验证配置
```bash
# 检查环境变量
D:/temp/llm-as-middle/.venv/Scripts/python.exe -c "import os; print(os.getenv('LITELLM_BASE_URL'))"
```
