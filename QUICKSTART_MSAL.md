# MSAL认证快速配置指南

本文档提供简化的步骤帮助您快速配置MSAL认证。

## 步骤1: Azure AD应用注册

### 1.1 登录Azure Portal
访问 https://portal.azure.com 并登录

### 1.2 创建应用注册
1. 搜索并进入 "Azure Active Directory"
2. 点击左侧菜单的 "应用注册"
3. 点击 "+ 新注册"
4. 填写：
   - **名称**: `llm-as-middle-app`
   - **支持的账户类型**: 选择"仅此组织目录中的账户"
   - **重定向URI**: 留空
5. 点击"注册"

### 1.3 获取认证信息
注册完成后，在"概述"页面复制：

- **应用程序(客户端) ID** 
- **目录(租户) ID**

### 1.4 创建客户端密钥
1. 在左侧菜单点击"证书和密钥"
2. 点击"+ 新建客户端密钥"
3. 填写描述: `llm-as-middle-secret`
4. 选择过期时间（建议6个月或1年）
5. 点击"添加"
6. **立即复制"值"** - 这个密钥只显示一次！

### 1.5 配置API权限
1. 在左侧菜单点击"API权限"
2. 点击"+ 添加权限"
3. 根据您的LiteLLM配置选择：
   - **使用Azure OpenAI**: 选择 "Azure Service Management" → "user_impersonation"
   - 或添加自定义scope: `https://cognitiveservices.azure.com/.default`
4. 点击"授予管理员同意" (需要管理员权限)

## 步骤2: 配置环境变量

创建或编辑 `.env` 文件：

```bash
# Azure AD认证
AZURE_TENANT_ID=<步骤1.3中复制的租户ID>
AZURE_CLIENT_ID=<步骤1.3中复制的客户端ID>
AZURE_CLIENT_SECRET=<步骤1.4中复制的客户端密钥>
AZURE_SCOPE=https://cognitiveservices.azure.com/.default

# LiteLLM配置
LITELLM_BASE_URL=http://localhost:4000
LLM_MODEL=gpt-4

# AWS S3配置
AWS_ACCESS_KEY_ID=your-aws-key
AWS_SECRET_ACCESS_KEY=your-aws-secret
AWS_REGION=us-east-1
S3_BUCKET=confluence-docs-backup

# 其他配置
SEARCH_LIMIT=10
```

## 步骤3: 测试认证

运行测试脚本验证配置：

```bash
python test_msal_auth.py
```

期望输出：
```
🚀 开始测试MSAL认证集成...

============================================================
MSAL认证测试
============================================================

1. 检查环境变量...
   ✓ AZURE_TENANT_ID: 12345678...
   ✓ AZURE_CLIENT_ID: abcdefgh...
   ✓ AZURE_CLIENT_SECRET: xxxxxxxx...

2. 尝试获取访问令牌...
   Authority: https://login.microsoftonline.com/12345678-...
   Client ID: abcdefgh...
   Scope: https://cognitiveservices.azure.com/.default

   正在获取token...

   ✓ 成功获取访问令牌!
   Token长度: 1234 字符
   
============================================================
✅ MSAL认证测试通过!
```

## 步骤4: 启动服务

```bash
python main.py
```

服务将在 http://0.0.0.0:8000 启动。

## 步骤5: 配置VS Code

在VS Code的 `settings.json` 中添加：

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

## 常见问题

### Q1: 获取token失败，提示"invalid_client"

**原因**: Client Secret错误或过期

**解决**:
1. 在Azure Portal检查客户端密钥是否有效
2. 如果过期，创建新密钥并更新 `.env` 文件

### Q2: 获取token失败，提示权限相关错误

**原因**: API权限未正确配置或未授予管理员同意

**解决**:
1. 在Azure Portal的"API权限"页面
2. 确认权限已添加
3. 点击"授予管理员同意"按钮

### Q3: LLM调用失败

**可能原因**:
1. LiteLLM proxy未运行
2. LITELLM_BASE_URL配置错误
3. LiteLLM未配置接受Azure AD token

**解决**:
1. 确认LiteLLM proxy正在运行: `curl http://localhost:4000/health`
2. 检查LiteLLM配置是否启用Azure AD认证
3. 查看LiteLLM日志

### Q4: Scope应该配置什么？

根据您的Azure资源选择：

| 使用的服务 | Scope |
|-----------|-------|
| Azure OpenAI | `https://cognitiveservices.azure.com/.default` |
| Azure资源管理 | `https://management.azure.com/.default` |
| 自定义API | `api://<your-api-id>/.default` |

## 安全提醒

1. ⚠️ **永远不要**将 `.env` 文件提交到Git
2. 🔐 定期轮换Client Secret（建议每3-6个月）
3. 🔒 使用最小权限原则，仅授予必要的API权限
4. 📊 定期在Azure Portal监控应用的使用情况

## 下一步

- 阅读完整文档: [MSAL_AUTH_GUIDE.md](MSAL_AUTH_GUIDE.md)
- 了解项目架构: [README.md](README.md)
- 查看工作流详情: [architecture.txt](architecture.txt)

## 需要帮助？

如果遇到问题：
1. 查看日志输出
2. 运行 `python test_msal_auth.py` 诊断
3. 检查Azure AD应用配置
4. 参考 [MSAL文档](https://msal-python.readthedocs.io/)
