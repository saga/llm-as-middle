"""测试MSAL认证功能"""
import os
import sys
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()


def test_msal_auth():
    """测试MSAL认证"""
    print("=" * 60)
    print("MSAL认证测试")
    print("=" * 60)
    
    # 检查环境变量
    print("\n1. 检查环境变量...")
    required_vars = [
        "AZURE_TENANT_ID",
        "AZURE_CLIENT_ID", 
        "AZURE_CLIENT_SECRET"
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            # 只显示前几个字符
            display_value = f"{value[:8]}..." if len(value) > 8 else value
            print(f"   ✓ {var}: {display_value}")
        else:
            print(f"   ✗ {var}: 未设置")
            missing_vars.append(var)
    
    if missing_vars:
        print(f"\n❌ 错误: 缺少必要的环境变量: {', '.join(missing_vars)}")
        print("请在 .env 文件中配置这些变量")
        return False
    
    # 测试获取token
    print("\n2. 尝试获取访问令牌...")
    try:
        from auth import get_access_token
        from auth.msal_auth import get_token_manager
        
        manager = get_token_manager()
        print(f"   Authority: {manager.authority}")
        if manager.client_id:
            print(f"   Client ID: {manager.client_id[:8]}...")
        print(f"   Scope: {manager.scope}")
        
        print("\n   正在获取token...")
        token = get_access_token()
        
        # 显示token信息（不显示完整token）
        print(f"\n   ✓ 成功获取访问令牌!")
        print(f"   Token长度: {len(token)} 字符")
        print(f"   Token预览: {token[:20]}...{token[-20:]}")
        
        # 尝试解析token（仅显示基本信息）
        try:
            import base64
            import json
            
            # JWT token格式: header.payload.signature
            parts = token.split('.')
            if len(parts) == 3:
                # 解码payload（需要添加padding）
                payload = parts[1]
                # 添加必要的padding
                padding = 4 - len(payload) % 4
                if padding != 4:
                    payload += '=' * padding
                
                decoded = base64.urlsafe_b64decode(payload)
                token_data = json.loads(decoded)
                
                print("\n   Token信息:")
                if 'exp' in token_data:
                    from datetime import datetime
                    exp_time = datetime.fromtimestamp(token_data['exp'])
                    print(f"   - 过期时间: {exp_time}")
                if 'aud' in token_data:
                    print(f"   - Audience: {token_data['aud']}")
                if 'iss' in token_data:
                    print(f"   - Issuer: {token_data['iss']}")
                    
        except Exception as e:
            print(f"   (无法解析token详情: {e})")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 获取token失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_llm_with_msal():
    """测试使用MSAL token调用LLM"""
    print("\n" + "=" * 60)
    print("LLM集成测试")
    print("=" * 60)
    
    try:
        from agent.nodes import get_llm
        from langchain_core.messages import HumanMessage
        
        print("\n正在初始化LLM（使用MSAL认证）...")
        llm = get_llm()
        
        print(f"模型: {llm.model_name}")
        print(f"Base URL: {llm.openai_api_base}")
        
        print("\n发送测试消息...")
        response = llm.invoke([HumanMessage(content="Say 'Hello from MSAL!'")])
        
        print(f"\n✓ LLM响应: {response.content}")
        return True
        
    except Exception as e:
        print(f"\n❌ LLM测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🚀 开始测试MSAL认证集成...\n")
    
    # 测试MSAL认证
    auth_success = test_msal_auth()
    
    if auth_success:
        print("\n" + "=" * 60)
        print("✅ MSAL认证测试通过!")
        
        # 询问是否测试LLM
        response = input("\n是否测试LLM调用? (需要配置LITELLM_BASE_URL) [y/N]: ")
        if response.lower() == 'y':
            llm_success = test_llm_with_msal()
            if llm_success:
                print("\n✅ 所有测试通过!")
            else:
                print("\n⚠️  MSAL认证正常，但LLM调用失败")
                print("请检查:")
                print("1. LITELLM_BASE_URL是否正确")
                print("2. LiteLLM proxy是否正在运行")
                print("3. LiteLLM是否配置接受Azure AD token")
    else:
        print("\n❌ MSAL认证测试失败")
        print("\n请检查:")
        print("1. Azure AD应用是否正确配置")
        print("2. Client Secret是否有效")
        print("3. API权限是否已授予")
        print("\n详细配置指南: MSAL_AUTH_GUIDE.md")
        sys.exit(1)
