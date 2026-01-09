# MSAL认证集成说明

## 概述

本项目使用Microsoft Authentication Library (MSAL) 来获取Azure AD访问令牌，然后使用该令牌调用LiteLLM proxy。

## 认证流程

```
1. 应用启动时初始化MSAL客户端
2. 使用Client Credentials流程获取访问令牌
   - Tenant ID
   - Client ID  
   - Client Secret
3. 将令牌添加到LiteLLM API调用的Authorization头中
4. Token自动缓存和刷新
```

## Azure AD应用注册

### 1. 在Azure Portal创建应用注册

1. 登录 [Azure Portal](https://portal.azure.com)
2. 导航至 **Azure Active Directory** > **App registrations** > **New registration**
3. 填写应用信息：
   - Name: `llm-as-middle-app` (或您的应用名称)
   - Supported account types: 选择适合您组织的类型
   - Redirect URI: 不需要（我们使用Client Credentials流程）
4. 点击 **Register**

### 2. 获取认证信息

注册完成后，从"Overview"页面获取：
- **Application (client) ID** → `AZURE_CLIENT_ID`
- **Directory (tenant) ID** → `AZURE_TENANT_ID`

### 3. 创建Client Secret

1. 导航至 **Certificates & secrets** > **Client secrets** > **New client secret**
2. 添加描述并选择过期时间
3. 点击 **Add**
4. **立即复制生成的secret值** → `AZURE_CLIENT_SECRET`
   - ⚠️ 此值只显示一次，请妥善保存

### 4. 配置API权限

1. 导航至 **API permissions** > **Add a permission**
2. 根据您的LiteLLM配置选择适当的权限：
   - 如果使用Azure OpenAI: 选择 **Azure Service Management** 或 **Cognitive Services**
   - 添加 `https://cognitiveservices.azure.com/.default` 作为scope
3. 点击 **Grant admin consent** 授予权限

## 环境变量配置

在 `.env` 文件中配置以下变量：

```bash
# Azure AD认证配置
AZURE_TENANT_ID=your-tenant-id-here
AZURE_CLIENT_ID=your-client-id-here
AZURE_CLIENT_SECRET=your-client-secret-here
AZURE_SCOPE=https://cognitiveservices.azure.com/.default

# LiteLLM配置
LITELLM_BASE_URL=http://localhost:4000
LLM_MODEL=gpt-4
```

## 使用示例

### 基本使用

认证模块会自动在需要时获取令牌：

```python
from auth import get_access_token, get_token_headers

# 获取访问令牌
token = get_access_token()

# 获取包含认证头的字典
headers = get_token_headers()
# {'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiIs...'}
```

### 在Agent中使用

Agent的LLM调用会自动使用MSAL认证：

```python
# agent/nodes.py 中已自动配置
llm = get_llm()  # 使用MSAL token认证

# 所有LLM调用都会带上token
result = await llm.ainvoke([system_msg, human_msg])
```

## Token管理

- **自动缓存**: 获取的token会被MSAL库自动缓存
- **自动刷新**: Token过期前会自动刷新
- **线程安全**: Token管理器使用单例模式，确保线程安全

## 故障排查

### 错误：缺少必要的Azure认证配置

```
ValueError: 缺少必要的Azure认证配置。请设置以下环境变量：
- AZURE_TENANT_ID
- AZURE_CLIENT_ID
- AZURE_CLIENT_SECRET
```

**解决方案**: 检查 `.env` 文件，确保所有必需的环境变量都已设置。

### 错误：获取访问令牌失败

```
Exception: 获取访问令牌失败: invalid_client - AADSTS7000215: Invalid client secret provided.
```

**可能原因**:
1. Client Secret错误或已过期
2. Client ID或Tenant ID不正确
3. 应用权限未正确配置

**解决方案**:
1. 在Azure Portal验证Client Secret是否有效
2. 检查AZURE_CLIENT_ID和AZURE_TENANT_ID是否正确
3. 确认API权限已授予admin consent

### 错误：Scope配置问题

如果您的LiteLLM使用不同的Azure资源，可能需要调整scope：

```bash
# 对于Azure OpenAI
AZURE_SCOPE=https://cognitiveservices.azure.com/.default

# 对于其他Azure资源
AZURE_SCOPE=https://your-resource/.default
```

## 安全最佳实践

1. **永远不要**将 `.env` 文件提交到版本控制
2. **使用环境变量**或密钥管理服务存储敏感信息
3. **定期轮换** Client Secret
4. **最小权限原则**: 只授予应用所需的最小权限
5. **监控**: 在Azure Portal监控应用的登录和API使用情况

## 与LiteLLM Proxy集成

LiteLLM proxy应该配置为接受Azure AD令牌：

```yaml
# litellm_config.yaml 示例
model_list:
  - model_name: gpt-4
    litellm_params:
      model: azure/gpt-4
      api_base: https://your-resource.openai.azure.com/
      api_version: "2024-02-15-preview"
      
general_settings:
  master_key: os.environ/LITELLM_MASTER_KEY
  
# 启用Azure AD认证
litellm_settings:
  enable_azure_ad: true
  allowed_tenant_ids:
    - your-tenant-id-here
```

## 参考资料

- [MSAL Python文档](https://msal-python.readthedocs.io/)
- [Azure AD应用注册](https://docs.microsoft.com/azure/active-directory/develop/quickstart-register-app)
- [Client Credentials流程](https://docs.microsoft.com/azure/active-directory/develop/v2-oauth2-client-creds-grant-flow)
- [LiteLLM文档](https://docs.litellm.ai/)
