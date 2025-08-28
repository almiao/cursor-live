#!/usr/bin/env python3
"""
测试修复后的AI对话框打开功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pyautogu import CursorAutomation
import time

def test_ai_dialog_open():
    """测试AI对话框打开功能"""
    print("=" * 50)
    print("测试AI对话框打开功能")
    print("=" * 50)
    
    automation = CursorAutomation()
    
    # 检查当前状态
    print("\n1. 检查当前状态:")
    current_state = automation.detect_dialog_state()
    print(f"   当前状态: {current_state}")
    
    if current_state == 'dialogue':
        print("   ✓ AI对话框已经打开")
        return True
    
    # 尝试打开AI对话框
    print("\n2. 尝试打开AI对话框:")
    print("   将发送快捷键: Option+Command+B (Mac)")
    
    success = automation.open_chat_dialog()
    print(f"   打开结果: {'成功' if success else '失败'}")
    
    if success:
        # 验证状态
        print("\n3. 验证状态:")
        for i in range(5):
            time.sleep(1)
            state = automation.detect_dialog_state()
            print(f"   第{i+1}次检测: {state}")
            if state == 'dialogue':
                print("   ✓ 成功检测到AI对话框状态")
                return True
        
        print("   ✗ 未能检测到AI对话框状态")
        return False
    else:
        print("   ✗ AI对话框打开失败")
        return False

def test_send_message():
    """测试发送消息功能"""
    print("\n" + "=" * 50)
    print("测试发送消息功能")
    print("=" * 50)
    
    automation = CursorAutomation()
    test_message = "这是一个测试消息，用于验证AI对话框功能"
    
    print(f"测试消息: {test_message}")
    
    # 发送消息
    success = automation.send_to_cursor(test_message, max_retries=1)
    
    print(f"发送结果: {'成功' if success else '失败'}")
    return success

def main():
    """主测试函数"""
    print("AI对话框功能测试")
    print("请确保:")
    print("1. Cursor应用已打开")
    print("2. 当前没有AI对话框打开")
    input("\n按回车键开始测试...")
    
    # 测试AI对话框打开
    dialog_success = test_ai_dialog_open()
    
    if dialog_success:
        # 如果对话框打开成功，测试发送消息
        message_success = test_send_message()
        
        print("\n" + "=" * 50)
        print("测试结果总结:")
        print(f"AI对话框打开: {'✓ 成功' if dialog_success else '✗ 失败'}")
        print(f"消息发送: {'✓ 成功' if message_success else '✗ 失败'}")
    else:
        print("\n" + "=" * 50)
        print("测试结果:")
        print("✗ AI对话框打开失败，跳过消息发送测试")
    
    print("=" * 50)

if __name__ == "__main__":
    main()
