#!/usr/bin/env python3
"""
测试Cursor状态检查功能
"""

import requests
import time
import json

def test_cursor_status_api():
    """测试Cursor状态API"""
    print("=" * 50)
    print("测试Cursor状态API")
    print("=" * 50)
    
    try:
        # 测试API端点
        response = requests.get('http://localhost:5001/api/cursor-status')
        
        if response.status_code == 200:
            data = response.json()
            print("✓ API响应成功")
            print(f"  Cursor激活状态: {data.get('isActive', 'N/A')}")
            print(f"  AI对话框状态: {data.get('isDialogOpen', 'N/A')}")
            print(f"  对话框状态: {data.get('dialogState', 'N/A')}")
            print(f"  时间戳: {data.get('timestamp', 'N/A')}")
            
            # 检查数据结构
            if isinstance(data.get('isActive'), dict):
                print(f"  Cursor详细信息: {json.dumps(data['isActive'], indent=2)}")
            
        else:
            print(f"✗ API响应失败: {response.status_code}")
            print(f"  响应内容: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("✗ 无法连接到服务器，请确保服务器正在运行")
    except Exception as e:
        print(f"✗ 测试失败: {e}")

def test_status_monitoring():
    """测试状态监控"""
    print("\n" + "=" * 50)
    print("测试状态监控（连续5次检查）")
    print("=" * 50)
    
    for i in range(5):
        try:
            response = requests.get('http://localhost:5001/api/cursor-status')
            if response.status_code == 200:
                data = response.json()
                is_active = data.get('isActive', False)
                is_dialog_open = data.get('isDialogOpen', False)
                
                print(f"第{i+1}次检查:")
                print(f"  Cursor激活: {'✓' if is_active else '✗'}")
                print(f"  AI对话框: {'✓' if is_dialog_open else '✗'}")
                print(f"  状态: {data.get('dialogState', 'unknown')}")
                print()
            else:
                print(f"第{i+1}次检查失败: {response.status_code}")
                
        except Exception as e:
            print(f"第{i+1}次检查异常: {e}")
        
        if i < 4:  # 不是最后一次
            time.sleep(2)

def main():
    """主测试函数"""
    print("Cursor状态检查功能测试")
    print("请确保:")
    print("1. 服务器正在运行 (python3 server.py --port 5001)")
    print("2. Cursor应用已打开")
    print("3. 可以尝试打开/关闭AI对话框来测试状态变化")
    input("\n按回车键开始测试...")
    
    # 运行测试
    test_cursor_status_api()
    test_status_monitoring()
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)

if __name__ == "__main__":
    main()

