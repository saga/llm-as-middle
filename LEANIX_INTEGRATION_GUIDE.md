# LeanIX集成指南

## 概述

LeanIX是SAP提供的企业架构管理(EAM)平台，帮助组织管理IT资产、应用、数据、流程和业务能力。本项目通过GraphQL API集成LeanIX，提供智能搜索和分析功能。

## 功能特性

### 1. Fact Sheet搜索
搜索LeanIX中的各类fact sheets（事实表），包括：
- **Application** - 业务应用和软件系统
- **DataObject** - 数据实体、数据库、数据集
- **ITComponent** - 基础设施组件、服务器、硬件
- **BusinessCapability** - 业务能力和功能
- **Process** - 业务流程和工作流
- **UserGroup** - 团队、部门、利益相关者
- **Project** - 项目和举措
- **Interface** - API和集成接口

### 2. 详细信息获取
- 获取fact sheet的完整信息
- 包含关联关系（relToChild）
- 包含相关文档
- 标签和元数据

### 3. 数据归档
- 将架构数据保存到S3
- 便于后续分析和审计
- 包含完整的时间戳和元数据

## 配置步骤

### 1. 获取LeanIX API Token

1. 登录到你的LeanIX工作空间（例如：`https://mycompany.leanix.net`）
2. 点击右上角的帮助菜单 → Developer Tools → API Tokens
3. 创建新的API Token：
   - 名称：例如"VS Code Copilot Integration"
   - 权限：至少需要"Read"权限
   - 复制生成的Token

### 2. 配置环境变量

在`.env`文件中添加：

```env
# LeanIX配置
LEANIX_SUBDOMAIN=mycompany          # 你的子域名（不含.leanix.net）
LEANIX_API_TOKEN=your-api-token     # 从步骤1获取的Token
```

### 3. 验证配置

运行测试脚本验证配置是否正确：

```python
import asyncio
from clients.leanix import get_fact_sheet_types, search_fact_sheets

async def test_connection():
    # 测试1: 获取fact sheet类型
    types = await get_fact_sheet_types()
    print(f"Available types: {types}")
    
    # 测试2: 搜索应用
    apps = await search_fact_sheets(
        search_term="CRM",
        fact_sheet_type="Application",
        limit=5
    )
    print(f"Found {len(apps)} applications")
    for app in apps:
        print(f"  - {app['name']}")

asyncio.run(test_connection())
```

## API使用方法

### 方法1: 通过MCP工具使用

在VS Code Copilot Chat中：

```
# 搜索所有CRM应用
@workspace search_leanix("CRM", fact_sheet_type="Application", limit=10)

# 获取所有fact sheet类型
@workspace get_leanix_fact_sheet_types()

# 搜索所有类型（不指定type）
@workspace search_leanix("customer data")
```

### 方法2: 直接使用Python客户端

```python
from clients.leanix import (
    search_fact_sheets,
    get_fact_sheet,
    search_applications,
    get_fact_sheet_types
)

# 1. 搜索fact sheets
results = await search_fact_sheets(
    search_term="customer",
    fact_sheet_type="Application",  # 可选
    limit=10,
    include_fields=["tags", "updatedAt"]
)

# 2. 获取详细信息
detail = await get_fact_sheet(
    fact_sheet_id="abc-123",
    include_relations=True,
    include_documents=True
)

# 3. 搜索应用（便捷方法）
apps = await search_applications(
    search_term="CRM",
    limit=10,
    include_lifecycle=True
)

# 4. 获取所有fact sheet类型
types = await get_fact_sheet_types()
```

## GraphQL查询示例

### 基础搜索查询

```graphql
query {
  allFactSheets(
    filter: {
      fullTextSearch: "CRM"
      facetFilters: [{facetKey: "FactSheetTypes", keys: ["Application"]}]
    }
    first: 10
  ) {
    edges {
      node {
        id
        name
        type
        description
        displayName
        tags { name }
        updatedAt
      }
    }
  }
}
```

### 获取详细信息（含关系）

```graphql
query {
  factSheet(id: "abc-123") {
    id
    name
    type
    description
    tags { name }
    relToChild {
      edges {
        node {
          factSheet {
            id
            name
            type
            displayName
          }
        }
      }
    }
    documents {
      edges {
        node {
          id
          name
          description
          url
        }
      }
    }
  }
}
```

### 搜索特定类型（Application）

```graphql
query {
  allFactSheets(
    filter: {
      facetFilters: [{facetKey: "FactSheetTypes", keys: ["Application"]}]
      fullTextSearch: "sales"
    }
    first: 10
  ) {
    edges {
      node {
        ... on Application {
          id
          name
          displayName
          description
          alias
          lifecycle {
            asString
            phases {
              phase
              startDate
            }
          }
        }
      }
    }
  }
}
```

## 常见Fact Sheet类型说明

| 类型 | 说明 | 典型用例 |
|------|------|----------|
| Application | 业务应用系统 | CRM、ERP、自建系统 |
| DataObject | 数据对象 | 客户数据库、订单数据 |
| ITComponent | IT组件 | 服务器、容器、中间件 |
| BusinessCapability | 业务能力 | 销售管理、库存管理 |
| Process | 业务流程 | 订单处理流程 |
| UserGroup | 用户组 | 销售团队、IT部门 |
| Project | 项目 | 数字化转型项目 |
| Provider | 供应商 | 云服务提供商 |
| Interface | 接口 | REST API、集成点 |

## 最佳实践

### 1. 搜索优化
- 使用具体的搜索词而不是泛泛的关键词
- 指定fact sheet类型可以提高搜索效率
- 合理设置limit，避免返回过多结果

### 2. 错误处理
```python
try:
    results = await search_fact_sheets(
        search_term="CRM",
        fact_sheet_type="Application"
    )
    if not results:
        print("No results found")
except Exception as e:
    print(f"Error: {e}")
    # 检查LEANIX_SUBDOMAIN和LEANIX_API_TOKEN是否正确配置
```

### 3. 性能考虑
- 首次查询会获取OAuth2 token，后续查询会复用
- 批量查询时考虑使用GraphQL的批处理能力
- 大量数据建议使用分页（pagination）

### 4. 安全建议
- 不要在代码中硬编码API Token
- 使用环境变量或密钥管理服务
- 定期轮换API Token
- 限制Token的权限范围（最小权限原则）

## 故障排查

### 常见问题

**Q: "Failed to get access token" 错误**
- 检查LEANIX_API_TOKEN是否正确
- 确认Token未过期
- 验证Token权限是否足够

**Q: "No fact sheets found" 但确定有数据**
- 检查搜索词是否正确
- 尝试不指定fact_sheet_type搜索全部类型
- 确认用户有权限访问这些fact sheets

**Q: GraphQL errors返回**
- 查看具体的错误消息
- 检查查询语法是否正确
- 确认请求的字段在schema中存在

**Q: 性能较慢**
- 减小limit参数
- 减少include_fields中的字段
- 避免在循环中频繁调用API

## 参考资源

- [SAP LeanIX API文档](https://help.sap.com/docs/leanix/ea/sap-leanix-apis)
- [GraphQL API参考](https://help.sap.com/docs/leanix/ea/graphql-api)
- [GraphQL基础教程](https://graphql.org/learn/)
- [LeanIX公开GitHub示例](https://github.com/leanix-public/scripts)

## 支持

如有问题或建议，请：
1. 查看本文档的故障排查部分
2. 参考SAP LeanIX官方文档
3. 在项目中提交Issue
