# 快速开始

## ⚡ 5分钟快速启动

### 前置要求
- Python 3.12+
- uv包管理器（或pip）
- 运行中的LiteLLM Proxy（可选）

### 步骤

#### 1. 克隆/进入项目目录
```bash
cd d:\temp\llm-as-middle
```

#### 2. 安装依赖
```bash
uv sync
```

#### 3. 配置环境变量
```bash
# 复制示例配置
copy .env.example .env

# 编辑 .env 文件，填入实际值
# LITELLM_BASE_URL=http://your-litellm-server:4000
# LITELLM_API_KEY=your-api-key
# CONFLUENCE_MODEL=confluence-mcp
```

#### 4. 启动服务
```bash
python main.py
```

#### 5. 验证服务
打开新终端：
```bash
curl http://localhost:8000/health
```

应该看到：
```json
{"status":"healthy","service":"enterprise-doc-agent"}
```

### ✅ 完成！

服务现在运行在 `http://localhost:8000`

MCP SSE端点：`http://localhost:8000/sse`

---

## 🔧 配置VS Code Copilot

### 编辑settings.json

按 `Ctrl+Shift+P` → 输入 "Preferences: Open User Settings (JSON)"

添加：
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

### 测试

在VS Code中打开Copilot Chat (Ctrl+Alt+I)，输入：

```
@enterprise-doc 搜索关于认证的文档
```

---

## 🐳 Docker快速启动

### 构建并运行
```bash
# 构建镜像
docker build -t doc-mcp .

# 运行
docker run -p 8000:8000 \
  -e LITELLM_BASE_URL=http://host.docker.internal:4000 \
  -e LITELLM_API_KEY=your-key \
  doc-mcp
```

### 测试
```bash
curl http://localhost:8000/health
```

---

## ☸️ Kubernetes快速部署

### 1. 更新配置
编辑 `k8s.yml`：
- 修改镜像地址
- 更新环境变量
- 设置API密钥

### 2. 部署
```bash
kubectl apply -f k8s.yml
```

### 3. 验证
```bash
# 查看Pod状态
kubectl get pods -l app=doc-mcp

# 端口转发
kubectl port-forward svc/doc-mcp 8000:8000

# 测试
curl http://localhost:8000/health
```

---

## 🔄 切换到直接MCP连接

如果不想使用LiteLLM Proxy：

### 1. 切换客户端实现
```bash
# 备份当前文件
copy clients\confluence.py clients\confluence_litellm.py.bak

# 使用直接MCP实现
copy clients\confluence_mcp_direct.py clients\confluence.py
```

### 2. 更新环境变量
编辑 `.env`：
```env
CONFLUENCE_MCP_URL=http://confluence-mcp:8080/sse
```

### 3. 重启服务
```bash
python main.py
```

---

## 📚 下一步

- 阅读完整文档：[README.md](README.md)
- 查看部署指南：[DEPLOY.md](DEPLOY.md)
- 了解配置选项：[CONFIG.md](CONFIG.md)
- 测试命令集合：[TESTING.md](TESTING.md)

## 🐛 遇到问题？

### 服务无法启动
- 检查Python版本：`python --version`（需要3.12+）
- 检查端口占用：`netstat -ano | findstr :8000`
- 查看详细错误：检查终端输出

### 无法连接LiteLLM
- 验证LiteLLM URL可访问
- 检查API密钥正确性
- 尝试直接curl LiteLLM健康检查

### VS Code无法连接
- 确认服务运行中
- 检查URL配置正确
- 重启VS Code

更多故障排查，参见 [README.md#故障排查](README.md#故障排查)
