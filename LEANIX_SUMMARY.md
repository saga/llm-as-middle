# LeanIX集成功能总结

## 新增功能概述

根据SAP LeanIX API文档，为项目添加了完整的LeanIX企业架构管理(EAM)平台集成功能。

## 实现的文件

### 1. 核心客户端 - `clients/leanix.py`

**认证功能：**
- `get_access_token()` - 使用API Token获取OAuth2访问令牌
- 自动处理token认证流程

**搜索功能：**
- `search_fact_sheets()` - 通用fact sheet搜索
  - 支持全文搜索
  - 支持类型过滤（Application、DataObject等）
  - 可配置返回字段
  - 支持结果数量限制

- `search_applications()` - 专门的应用搜索
  - 包含生命周期信息
  - 针对Application类型优化

**详细信息获取：**
- `get_fact_sheet()` - 获取单个fact sheet详情
  - 可选包含关联关系（relToChild）
  - 可选包含相关文档
  - 完整的元数据（标签、创建/更新时间等）

**工具功能：**
- `get_fact_sheet_types()` - 获取所有可用的fact sheet类型
  - 用于发现工作空间配置

### 2. Agent节点 - `agent/nodes.py`

新增了三个LeanIX专用节点：

**`search_leanix_node`**
- 智能识别用户查询中的fact sheet类型关键词
- 自动选择合适的类型过滤器
- 返回搜索结果和fact sheet ID列表

**`fetch_leanix_details_node`**
- 批量获取fact sheet详细信息
- 包含关系和文档数据
- 错误处理和日志记录

**`save_leanix_to_s3_node`**
- 将fact sheet数据归档到S3
- 按类型组织文件夹结构
- 完整的元数据标注

**`summarize_leanix_node`**
- 使用LLM总结架构数据
- 提取关键洞察
- 生成结构化响应

### 3. MCP工具 - `server.py`

新增两个MCP工具供VS Code Copilot调用：

**`search_leanix(query, fact_sheet_type, limit)`**
- 搜索LeanIX fact sheets
- 支持类型过滤
- 返回JSON格式结果
- 完整的错误处理

**`get_leanix_fact_sheet_types()`**
- 获取工作空间中所有可用的fact sheet类型
- 帮助用户了解数据结构

### 4. 文档和测试

**`LEANIX_INTEGRATION_GUIDE.md`**
- 完整的集成指南
- API使用示例
- GraphQL查询示例
- 故障排查指南
- 最佳实践建议

**`test_leanix_integration.py`**
- 自动化测试脚本
- 验证配置正确性
- 测试所有核心功能
- 提供详细的诊断信息

## 技术特点

### GraphQL API集成
- 使用LeanIX的GraphQL API（而非REST API）
- 更灵活的数据查询
- 减少网络传输
- 支持复杂关系查询

### 认证机制
- OAuth2 Client Credentials流程
- 基于API Token的认证
- 自动token管理

### 异步架构
- 全异步实现（async/await）
- 使用aiohttp进行HTTP请求
- 高性能并发处理

### 错误处理
- 完善的异常捕获
- 详细的错误日志
- 友好的错误消息

## 支持的Fact Sheet类型

实现支持LeanIX中的所有标准fact sheet类型：

1. **Application** - 应用系统
2. **BusinessCapability** - 业务能力
3. **Process** - 业务流程
4. **DataObject** - 数据对象
5. **ITComponent** - IT组件
6. **UserGroup** - 用户组
7. **Project** - 项目
8. **Provider** - 供应商
9. **Interface** - 接口

## 配置要求

需要的环境变量：
```env
LEANIX_SUBDOMAIN=your-company     # LeanIX子域名
LEANIX_API_TOKEN=your-token       # API访问令牌
```

可选配置：
```env
SEARCH_LIMIT=10                   # 默认搜索结果数量
S3_BUCKET=your-bucket            # S3归档桶（可选）
```

## 使用场景

### 1. 企业架构查询
```
搜索所有CRM相关应用系统
查找客户数据对象
列出所有云基础设施组件
```

### 2. 依赖关系分析
```
获取某应用的所有依赖组件
查看数据对象的关联应用
分析业务能力的实现应用
```

### 3. 架构文档化
```
导出所有应用到S3供审计
归档特定项目的架构数据
生成架构现状报告
```

## 与Confluence集成的对比

| 特性 | Confluence | LeanIX |
|------|-----------|---------|
| 数据类型 | 文档、页面 | Fact Sheets（架构数据）|
| API类型 | REST (via MCP) | GraphQL (直接) |
| 主要用途 | 知识管理 | 企业架构管理 |
| 搜索方式 | CQL查询 | 全文+类型过滤 |
| 关系数据 | 有限 | 丰富（关联关系）|

## 后续增强建议

1. **高级查询**
   - 添加更复杂的GraphQL查询支持
   - 支持自定义字段查询
   - 实现聚合和统计查询

2. **可视化**
   - 生成架构关系图
   - 导出为Mermaid图表
   - 依赖关系可视化

3. **数据分析**
   - 使用LLM分析架构模式
   - 识别架构风险
   - 提供优化建议

4. **批量操作**
   - 支持批量导出
   - 实现增量同步
   - 定期备份到S3

5. **Integration API**
   - 集成LeanIX的Integration API
   - 支持LDIF格式数据
   - 实现双向同步

## 参考资源

- [SAP LeanIX APIs文档](https://help.sap.com/docs/leanix/ea/sap-leanix-apis)
- [GraphQL API参考](https://help.sap.com/docs/leanix/ea/graphql-api)
- [认证指南](https://help.sap.com/docs/leanix/ea/authentication-to-sap-leanix-services)
- [示例脚本](https://github.com/leanix-public/scripts)
