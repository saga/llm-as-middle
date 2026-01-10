"""
LeanIX集成测试脚本

测试LeanIX API连接和基本功能
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_leanix_connection():
    """测试LeanIX连接和基本功能"""
    from clients.leanix import (
        get_fact_sheet_types,
        search_fact_sheets,
        search_applications,
        get_fact_sheet
    )
    
    print("=" * 60)
    print("LeanIX集成测试")
    print("=" * 60)
    
    # 检查环境变量
    subdomain = os.getenv("LEANIX_SUBDOMAIN")
    api_token = os.getenv("LEANIX_API_TOKEN")
    
    if not subdomain or not api_token:
        print("❌ 错误: 请配置LEANIX_SUBDOMAIN和LEANIX_API_TOKEN环境变量")
        print("\n在.env文件中添加:")
        print("LEANIX_SUBDOMAIN=your-company")
        print("LEANIX_API_TOKEN=your-api-token")
        return False
    
    print(f"✓ LeanIX子域名: {subdomain}")
    print(f"✓ API Token: {'*' * 20}{api_token[-4:]}")
    print()
    
    try:
        # 测试1: 获取fact sheet类型
        print("测试 1: 获取Fact Sheet类型")
        print("-" * 60)
        types = await get_fact_sheet_types()
        
        if types:
            print(f"✓ 成功获取 {len(types)} 个类型:")
            for t in sorted(types):
                print(f"  - {t}")
            print()
        else:
            print("⚠️ 未获取到fact sheet类型（可能是权限问题）")
            print()
        
        # 测试2: 搜索所有fact sheets
        print("测试 2: 搜索Fact Sheets（全类型）")
        print("-" * 60)
        all_results = await search_fact_sheets(
            search_term="",  # 空搜索词，获取前5个
            limit=5
        )
        
        if all_results:
            print(f"✓ 成功获取 {len(all_results)} 个fact sheets:")
            for fs in all_results:
                print(f"  - {fs.get('name', 'N/A')} ({fs.get('type', 'Unknown')})")
                print(f"    ID: {fs.get('id', 'N/A')}")
                if fs.get('description'):
                    desc = fs['description'][:60] + "..." if len(fs['description']) > 60 else fs['description']
                    print(f"    描述: {desc}")
            print()
        else:
            print("⚠️ 未找到fact sheets")
            print()
        
        # 测试3: 搜索Application类型
        print("测试 3: 搜索Applications")
        print("-" * 60)
        apps = await search_applications(
            search_term="",  # 空搜索词，获取任意应用
            limit=3,
            include_lifecycle=True
        )
        
        if apps:
            print(f"✓ 成功获取 {len(apps)} 个应用:")
            for app in apps:
                print(f"  - {app.get('name', 'N/A')}")
                print(f"    显示名: {app.get('displayName', 'N/A')}")
                print(f"    描述: {app.get('description', 'No description')[:60]}")
                if app.get('lifecycle'):
                    print(f"    生命周期: {app['lifecycle'].get('asString', 'N/A')}")
            print()
        else:
            print("⚠️ 未找到应用")
            print()
        
        # 测试4: 如果有fact sheet，获取详细信息
        if all_results and len(all_results) > 0:
            print("测试 4: 获取Fact Sheet详细信息")
            print("-" * 60)
            first_fs = all_results[0]
            fs_id = first_fs.get('id')
            
            if fs_id:
                detail = await get_fact_sheet(
                    fact_sheet_id=fs_id,
                    include_relations=True,
                    include_documents=True
                )
                
                if detail:
                    print(f"✓ 成功获取fact sheet详情:")
                    print(f"  名称: {detail.get('name', 'N/A')}")
                    print(f"  类型: {detail.get('type', 'N/A')}")
                    print(f"  ID: {detail.get('id', 'N/A')}")
                    
                    # 标签
                    tags = detail.get('tags', [])
                    if tags:
                        tag_names = [t.get('name', '') for t in tags]
                        print(f"  标签: {', '.join(tag_names)}")
                    
                    # 关联关系
                    relations = detail.get('relToChild', {}).get('edges', [])
                    if relations:
                        print(f"  关联关系: {len(relations)} 个子fact sheets")
                        for rel in relations[:3]:  # 只显示前3个
                            rel_fs = rel.get('node', {}).get('factSheet', {})
                            print(f"    → {rel_fs.get('name', 'N/A')} ({rel_fs.get('type', 'N/A')})")
                    
                    # 文档
                    documents = detail.get('documents', {}).get('edges', [])
                    if documents:
                        print(f"  文档: {len(documents)} 个")
                        for doc in documents[:3]:  # 只显示前3个
                            doc_node = doc.get('node', {})
                            print(f"    📄 {doc_node.get('name', 'N/A')}")
                    
                    print()
                else:
                    print("⚠️ 未能获取详细信息")
                    print()
        
        print("=" * 60)
        print("✅ 所有测试完成!")
        print("=" * 60)
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        print("\n请检查:")
        print("1. LEANIX_SUBDOMAIN是否正确（不包含.leanix.net）")
        print("2. LEANIX_API_TOKEN是否有效且未过期")
        print("3. Token是否有足够的读取权限")
        print("4. 网络连接是否正常")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_leanix_connection())
    sys.exit(0 if success else 1)
