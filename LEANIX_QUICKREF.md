# LeanIX工具快速参考

## 可用工具

### 1. search_leanix
搜索LeanIX fact sheets

**参数：**
- `query` (str) - 搜索关键词
- `fact_sheet_type` (str, 可选) - Fact sheet类型过滤
- `limit` (int, 默认10) - 最大返回结果数

**示例：**
```python
# 搜索所有CRM应用
search_leanix("CRM", fact_sheet_type="Application", limit=10)

# 搜索客户数据（所有类型）
search_leanix("customer data")

# 搜索IT组件
search_leanix("server", fact_sheet_type="ITComponent")
```

### 2. get_leanix_fact_sheet_types
获取所有可用的fact sheet类型

**参数：** 无

**示例：**
```python
get_leanix_fact_sheet_types()
```

## Fact Sheet类型

| 类型 | 英文 | 用途 |
|------|------|------|
| 应用 | Application | 业务应用系统 |
| 业务能力 | BusinessCapability | 业务功能 |
| 流程 | Process | 业务流程 |
| 数据对象 | DataObject | 数据库、数据集 |
| IT组件 | ITComponent | 服务器、基础设施 |
| 用户组 | UserGroup | 团队、部门 |
| 项目 | Project | 项目、计划 |
| 供应商 | Provider | 服务提供商 |
| 接口 | Interface | API、集成 |

## VS Code Copilot Chat使用

### 基础搜索
```
@workspace #search_leanix 查找所有CRM应用
```

### 带类型过滤
```
@workspace #search_leanix 搜索客户数据，类型：DataObject
```

### 获取类型列表
```
@workspace #get_leanix_fact_sheet_types 获取所有fact sheet类型
```

## Python API使用

### 导入
```python
from clients.leanix import (
    search_fact_sheets,
    get_fact_sheet,
    search_applications,
    get_fact_sheet_types
)
```

### 搜索示例
```python
# 1. 基础搜索
results = await search_fact_sheets(
    search_term="CRM",
    limit=10
)

# 2. 带类型过滤
apps = await search_fact_sheets(
    search_term="sales",
    fact_sheet_type="Application",
    limit=5
)

# 3. 应用专用搜索
apps = await search_applications(
    search_term="CRM",
    limit=10,
    include_lifecycle=True
)

# 4. 获取详细信息
detail = await get_fact_sheet(
    fact_sheet_id="abc-123",
    include_relations=True,
    include_documents=True
)

# 5. 获取类型列表
types = await get_fact_sheet_types()
```

## 返回数据格式

### search_leanix返回格式
```json
{
  "success": true,
  "message": "Found 5 fact sheet(s)",
  "query": "CRM",
  "type_filter": "Application",
  "count": 5,
  "results": [
    {
      "id": "abc-123",
      "name": "Salesforce CRM",
      "type": "Application",
      "description": "Customer relationship management",
      "tags": ["CRM", "Sales"],
      "updated_at": "2026-01-05T10:30:00Z",
      "created_at": "2025-06-01T09:00:00Z"
    }
  ]
}
```

### get_fact_sheet返回格式
```json
{
  "id": "abc-123",
  "name": "Salesforce CRM",
  "type": "Application",
  "description": "Customer relationship management platform",
  "displayName": "Salesforce CRM",
  "tags": [
    {"name": "CRM"},
    {"name": "Cloud"}
  ],
  "updatedAt": "2026-01-05T10:30:00Z",
  "createdAt": "2025-06-01T09:00:00Z",
  "relToChild": {
    "edges": [
      {
        "node": {
          "factSheet": {
            "id": "def-456",
            "name": "Customer Database",
            "type": "DataObject"
          }
        }
      }
    ]
  },
  "documents": {
    "edges": [
      {
        "node": {
          "id": "doc-1",
          "name": "Architecture Design",
          "url": "https://..."
        }
      }
    ]
  }
}
```

## 常见查询模式

### 1. 查找特定应用
```python
apps = await search_applications("CRM", limit=10)
```

### 2. 查找数据对象
```python
data = await search_fact_sheets(
    search_term="customer",
    fact_sheet_type="DataObject"
)
```

### 3. 查找基础设施
```python
infra = await search_fact_sheets(
    search_term="server",
    fact_sheet_type="ITComponent"
)
```

### 4. 获取应用依赖
```python
app = await get_fact_sheet(
    fact_sheet_id="app-123",
    include_relations=True
)
dependencies = app.get("relToChild", {}).get("edges", [])
```

## 环境变量

必需配置：
```env
LEANIX_SUBDOMAIN=mycompany        # 你的LeanIX子域名
LEANIX_API_TOKEN=your-token       # API访问令牌
```

## 故障排查

### 问题：认证失败
**原因：** Token无效或过期  
**解决：** 检查LEANIX_API_TOKEN，从LeanIX管理面板重新生成

### 问题：搜索无结果
**原因：** 搜索词不匹配或类型错误  
**解决：** 
1. 不指定类型再试
2. 简化搜索词
3. 使用`get_fact_sheet_types()`确认可用类型

### 问题：连接超时
**原因：** 网络问题或subdomain错误  
**解决：** 
1. 检查LEANIX_SUBDOMAIN是否正确
2. 验证网络连接
3. 确认防火墙设置

## 更多资源

- [完整集成指南](LEANIX_INTEGRATION_GUIDE.md)
- [功能总结](LEANIX_SUMMARY.md)
- [SAP官方文档](https://help.sap.com/docs/leanix/ea/sap-leanix-apis)
