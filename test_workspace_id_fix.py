#!/usr/bin/env python3
"""
测试workspace_id参数修复后的功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pyautogu import CursorAutomation
import time

def test_workspace_id_parameter():
    """测试workspace_id参数传递"""
    print("=" * 60)
    print("测试workspace_id参数传递")
    print("=" * 60)
    
    automation = CursorAutomation()
    
    # 获取当前workspace_id
    workspace_id = automation.get_workspace_id()
    print(f"当前workspace_id: {workspace_id}")
    
    if not workspace_id:
        print("❌ 无法获取workspace_id")
        return False
    
    # 测试1: 使用默认workspace_id检测状态
    print("\n1. 使用默认workspace_id检测状态:")
    state1 = automation.detect_dialog_state()
    print(f"   状态: {state1}")
    
    # 测试2: 显式传入workspace_id检测状态
    print("\n2. 显式传入workspace_id检测状态:")
    state2 = automation.detect_dialog_state(workspace_id)
    print(f"   状态: {state2}")
    
    # 验证两个状态是否一致
    if state1 == state2:
        print("   ✅ 状态检测一致")
    else:
        print("   ❌ 状态检测不一致")
        return False
    
    # 测试3: 测试打开对话框功能
    print("\n3. 测试打开对话框功能:")
    success = automation.open_chat_dialog(workspace_id=workspace_id)
    print(f"   打开结果: {'成功' if success else '失败'}")
    
    # 测试4: 验证状态变化
    print("\n4. 验证状态变化:")
    for i in range(5):
        time.sleep(1)
        state = automation.detect_dialog_state(workspace_id)
        print(f"   第{i+1}秒: {state}")
        if state == 'dialogue':
            print("   ✅ 成功检测到对话框状态")
            break
    else:
        print("   ❌ 未能检测到对话框状态")
    
    return True

def test_send_message_with_workspace_id():
    """测试使用workspace_id发送消息"""
    print("\n" + "=" * 60)
    print("测试使用workspace_id发送消息")
    print("=" * 60)
    
    automation = CursorAutomation()
    workspace_id = automation.get_workspace_id()
    
    if not workspace_id:
        print("❌ 无法获取workspace_id")
        return False
    
    test_message = "这是一个测试消息，验证workspace_id参数修复"
    print(f"测试消息: {test_message}")
    print(f"Workspace ID: {workspace_id}")
    
    # 发送消息
    success = automation.send_to_cursor(test_message, workspace_id=workspace_id)
    
    print(f"发送结果: {'成功' if success else '失败'}")
    return success

def main():
    """主测试函数"""
    print("workspace_id参数修复测试")
    print("请确保Cursor应用已打开")
    input("按回车键开始测试...")
    
    # 测试workspace_id参数传递
    param_test = test_workspace_id_parameter()
    
    if param_test:
        # 测试发送消息
        message_test = test_send_message_with_workspace_id()
        
        print("\n" + "=" * 60)
        print("测试结果总结:")
        print(f"参数传递测试: {'✓ 成功' if param_test else '✗ 失败'}")
        print(f"消息发送测试: {'✓ 成功' if message_test else '✗ 失败'}")
    else:
        print("\n" + "=" * 60)
        print("测试结果:")
        print("✗ 参数传递测试失败，跳过消息发送测试")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
