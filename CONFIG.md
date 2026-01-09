# 配置说明

## LiteLLM配置方案

### 选项1：使用LiteLLM Proxy（推荐用于生产环境）

如果您希望通过LiteLLM proxy来桥接到Confluence MCP Server：

#### LiteLLM Proxy配置示例

创建`litellm_config.yaml`：

```yaml
model_list:
  - model_name: confluence-mcp
    litellm_params:
      model: mcp/confluence  # 使用MCP适配器
      api_base: http://confluence-mcp-server:8080/sse
      mcp_transport: sse

# 可选：启用日志和监控
litellm_settings:
  success_callback: ["langfuse"]
  failure_callback: ["langfuse"]
```

启动LiteLLM proxy：

```bash
litellm --config litellm_config.yaml --port 4000
```

#### 应用配置

在`.env`中设置：

```env
LITELLM_BASE_URL=http://litellm-proxy:4000
LITELLM_API_KEY=your-api-key
CONFLUENCE_MODEL=confluence-mcp
```

当前实现在`clients/confluence.py`中使用OpenAI SDK调用LiteLLM。

### 选项2：直接连接Confluence MCP Server（适合开发测试）

如果不想使用LiteLLM proxy，可以直接连接Confluence MCP Server：

#### 切换到直接MCP客户端

1. 备份当前的`clients/confluence.py`：
```bash
mv clients/confluence.py clients/confluence_litellm.py.bak
```

2. 使用直接MCP客户端实现：
```bash
cp clients/confluence_mcp_direct.py clients/confluence.py
```

3. 更新`.env`：
```env
CONFLUENCE_MCP_URL=http://confluence-mcp:8080/sse
```

4. 确保`pyproject.toml`保留`mcp`依赖（已包含）

## Confluence MCP Server要求

无论使用哪种方案，您都需要一个运行中的Confluence MCP Server。

本项目基于 **sooperset/mcp-atlassian** 实现：
- GitHub: https://github.com/sooperset/mcp-atlassian
- MCP工具名称：`confluence_search`, `confluence_get_page`

### 使用sooperset/mcp-atlassian

这是推荐的Confluence MCP Server实现，支持完整的Confluence API。

#### 安装和运行

```bash
# 使用pip安装
pip install mcp-atlassian

# 或使用pipx
pipx install mcp-atlassian

# 运行服务器（SSE模式）
mcp-atlassian serve \
  --transport sse \
  --port 8080 \
  --confluence-url https://your-domain.atlassian.net/wiki \
  --confluence-username your-email@company.com \
  --confluence-token your-api-token
```

#### 可用工具

该MCP Server提供以下工具：

- **confluence_search** - 使用CQL搜索内容
  - 参数：`query` (str), `limit` (int, 默认10), `spaces_filter` (str | None)
  - 返回：JSON数组，包含简化的页面对象
  
- **confluence_get_page** - 获取页面内容
  - 参数：`page_id` (str) 或 `title` + `space_key`
  - 可选：`include_metadata` (bool), `convert_to_markdown` (bool)
  - 返回：JSON对象，包含页面内容和/或元数据

#### 返回格式示例

**confluence_search 返回：**
```json
[
  {
    "id": "123456789",
    "title": "页面标题",
    "type": "page",
    "url": "https://...",
    "space": {"key": "DEV", "name": "Development"},
    "author": "用户名",
    "created": "2024-01-01T10:00:00Z",
    "updated": "2024-01-10T15:30:00Z",
    "content": {
      "value": "页面内容（markdown或HTML）",
      "format": "markdown"
    }
  }
]
```

**confluence_get_page 返回（include_metadata=true）：**
```json
{
  "metadata": {
    "id": "123456789",
    "title": "页面标题",
    "type": "page",
    "url": "https://...",
    "space": {"key": "DEV", "name": "Development"},
    "content": {
      "value": "完整页面内容",
      "format": "markdown"
    },
    "version": 5,
    "created": "2024-01-01T10:00:00Z",
    "updated": "2024-01-10T15:30:00Z"
  }
}
```

## K8s部署配置对比

### 使用LiteLLM Proxy

```yaml
# 需要部署两个服务：
# 1. LiteLLM Proxy
# 2. Doc MCP Server (本项目)

env:
  - name: LITELLM_BASE_URL
    value: "http://litellm-proxy:4000"
  - name: LITELLM_API_KEY
    valueFrom:
      secretKeyRef:
        name: litellm-secret
        key: api-key
```

### 直接连接MCP

```yaml
# 只需要部署一个服务：
# 1. Doc MCP Server (本项目)

env:
  - name: CONFLUENCE_MCP_URL
    value: "http://confluence-mcp:8080/sse"
```

## 架构对比

### 架构A：通过LiteLLM Proxy

```
VS Code Copilot
      ↓
Doc MCP Server (本项目)
      ↓ OpenAI SDK
LiteLLM Proxy
      ↓ MCP Protocol
Confluence MCP Server
      ↓ REST API
Confluence
```

优点：
- 统一的API接口
- 可以添加认证、限流、日志等中间件
- 支持多种后端（不仅限于MCP）

缺点：
- 多一层代理
- 需要额外部署和维护LiteLLM

### 架构B：直接MCP连接

```
VS Code Copilot
      ↓
Doc MCP Server (本项目)
      ↓ MCP Protocol
Confluence MCP Server
      ↓ REST API
Confluence
```

优点：
- 简单直接
- 减少延迟
- 原生MCP支持

缺点：
- 缺少中间层的额外功能
- 每个后端服务需要独立配置

## 推荐方案

- **开发/测试环境**: 使用架构B（直接MCP连接）- 简单快速
- **生产环境**: 使用架构A（LiteLLM Proxy）- 便于管理和监控

## 当前实现状态

当前代码默认使用**架构A**（LiteLLM Proxy方式）。

如需切换到架构B，按照"选项2"的步骤操作即可。
