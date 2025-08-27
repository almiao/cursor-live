#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试AI侧边栏API功能

这个脚本用于测试新添加的AI侧边栏状态检测和打开功能。
"""

import requests
import json
import sys
import time

# 服务器配置
SERVER_URL = "http://127.0.0.1:5000"

def test_sidebar_status(workspace_id: str):
    """测试侧边栏状态检测API
    
    Args:
        workspace_id: workspace ID
    """
    print(f"\n=== 测试侧边栏状态检测 ===")
    print(f"Workspace ID: {workspace_id}")
    
    try:
        # 调用侧边栏状态API
        response = requests.get(
            f"{SERVER_URL}/api/cursor/sidebar/status",
            params={"workspace_id": workspace_id}
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # 返回是否需要打开命令
            return data.get("needs_open_command", False)
        else:
            print(f"错误: {response.text}")
            return None
            
    except Exception as e:
        print(f"请求异常: {e}")
        return None

def test_open_sidebar(skip_activation: bool = False):
    """测试打开侧边栏API
    
    Args:
        skip_activation: 是否跳过激活步骤
    """
    print(f"\n=== 测试打开AI侧边栏 ===")
    print(f"Skip activation: {skip_activation}")
    
    try:
        # 调用打开侧边栏API
        response = requests.post(
            f"{SERVER_URL}/api/cursor/sidebar/open",
            json={"skip_activation": skip_activation}
        )
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"响应数据: {json.dumps(data, indent=2, ensure_ascii=False)}")
            return True
        else:
            print(f"错误: {response.text}")
            return False
            
    except Exception as e:
        print(f"请求异常: {e}")
        return False

def main():
    """主函数"""
    print("AI侧边栏API测试工具")
    print("=" * 50)
    
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("使用方法: python test_sidebar_api.py <workspace_id>")
        print("示例: python test_sidebar_api.py 1234567890abcdef")
        sys.exit(1)
    
    workspace_id = sys.argv[1]
    
    # 测试侧边栏状态
    needs_open = test_sidebar_status(workspace_id)
    
    if needs_open is None:
        print("\n❌ 状态检测失败，无法继续测试")
        sys.exit(1)
    
    # 根据状态决定是否需要打开侧边栏
    if needs_open:
        print("\n📋 检测到侧边栏已隐藏，需要打开")
        
        # 询问用户是否要测试打开功能
        user_input = input("\n是否要测试打开AI侧边栏功能？(y/n): ")
        if user_input.lower() in ['y', 'yes', '是']:
            success = test_open_sidebar()
            if success:
                print("\n✅ AI侧边栏打开成功！")
                
                # 等待几秒后再次检测状态
                print("\n等待3秒后重新检测状态...")
                time.sleep(3)
                test_sidebar_status(workspace_id)
            else:
                print("\n❌ AI侧边栏打开失败")
        else:
            print("\n跳过打开测试")
    else:
        print("\n✅ 侧边栏已经打开，无需执行打开命令")
    
    print("\n测试完成！")

if __name__ == "__main__":
    main()