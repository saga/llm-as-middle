# 快速部署指南

## 1. 本地测试

```bash
# 安装依赖
uv sync

# 复制环境变量配置
cp .env.example .env

# 编辑 .env 文件，填入实际的LiteLLM配置
# LITELLM_BASE_URL=http://your-litellm-proxy:4000
# LITELLM_API_KEY=your-api-key

# 运行服务
python main.py
```

访问 http://localhost:8000/health 验证服务正常。

## 2. 构建Docker镜像

```bash
# 构建镜像
docker build -t your-registry/doc-mcp:v1.0.0 .

# 推送到镜像仓库
docker push your-registry/doc-mcp:v1.0.0
```

## 3. 部署到Kubernetes

### 3.1 更新配置

编辑 `k8s.yml`：
- 修改镜像地址为您的镜像仓库地址
- 更新 `LITELLM_BASE_URL` 为实际的LiteLLM服务地址
- 在Secret中设置正确的API密钥

```yaml
# 修改这些值
spec:
  template:
    spec:
      containers:
        - name: app
          image: your-registry/doc-mcp:v1.0.0  # 修改这里
          env:
            - name: LITELLM_BASE_URL
              value: "http://your-litellm-service:4000"  # 修改这里
```

### 3.2 创建Secret

```bash
# 方式1: 使用kubectl命令
kubectl create secret generic litellm-secret \
  --from-literal=api-key='your-actual-api-key'

# 方式2: 编辑k8s.yml中的Secret部分后应用
# 注意：生产环境建议使用外部密钥管理系统
```

### 3.3 应用配置

```bash
# 部署应用
kubectl apply -f k8s.yml

# 检查部署状态
kubectl get pods -l app=doc-mcp
kubectl get svc doc-mcp

# 查看日志
kubectl logs -l app=doc-mcp -f
```

### 3.4 验证部署

```bash
# 端口转发到本地
kubectl port-forward svc/doc-mcp 8000:8000

# 测试健康检查
curl http://localhost:8000/health
```

## 4. 配置VS Code Copilot Chat

### 方式1: 集群内访问（推荐）

如果VS Code运行在同一K8s集群中，在settings.json添加：

```json
{
  "github.copilot.advanced": {
    "mcp": {
      "servers": {
        "enterprise-doc": {
          "transport": "sse",
          "url": "http://doc-mcp.default.svc.cluster.local:8000/sse"
        }
      }
    }
  }
}
```

### 方式2: 通过Ingress访问

如果需要从集群外访问，创建Ingress：

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: doc-mcp-ingress
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
spec:
  rules:
  - host: doc-mcp.yourdomain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: doc-mcp
            port:
              number: 8000
```

然后在VS Code配置：

```json
{
  "github.copilot.advanced": {
    "mcp": {
      "servers": {
        "enterprise-doc": {
          "transport": "sse",
          "url": "https://doc-mcp.yourdomain.com/sse"
        }
      }
    }
  }
}
```

## 5. 使用示例

在VS Code Copilot Chat中：

```
@enterprise-doc 搜索关于API认证的文档
```

或

```
@enterprise-doc 获取页面ID为12345的内容
```

## 6. 监控和维护

### 查看日志

```bash
# 实时日志
kubectl logs -l app=doc-mcp -f

# 最近100行
kubectl logs -l app=doc-mcp --tail=100
```

### 扩容

```bash
# 手动扩容
kubectl scale deployment doc-mcp --replicas=5

# 自动扩容 (需要安装HPA)
kubectl autoscale deployment doc-mcp --min=2 --max=10 --cpu-percent=70
```

### 更新版本

```bash
# 构建新版本
docker build -t your-registry/doc-mcp:v1.1.0 .
docker push your-registry/doc-mcp:v1.1.0

# 更新部署
kubectl set image deployment/doc-mcp app=your-registry/doc-mcp:v1.1.0

# 查看滚动更新状态
kubectl rollout status deployment/doc-mcp

# 如需回滚
kubectl rollout undo deployment/doc-mcp
```

## 7. 故障排查

### Pod无法启动

```bash
kubectl describe pod -l app=doc-mcp
kubectl logs -l app=doc-mcp --previous
```

### 无法连接LiteLLM

```bash
# 在Pod内测试连接
kubectl exec -it <pod-name> -- curl http://litellm-proxy:4000/health

# 检查网络策略
kubectl get networkpolicies
```

### VS Code无法连接MCP

1. 确认服务端点可访问
2. 检查VS Code MCP配置
3. 查看VS Code输出面板的Copilot日志
4. 验证URL格式正确（需要 `/sse` 后缀）

## 8. 安全建议

- 使用专用的Secret管理工具（如Vault、AWS Secrets Manager）
- 启用网络策略限制Pod间通信
- 配置RBAC权限
- 使用TLS加密通信
- 定期更新依赖和基础镜像
