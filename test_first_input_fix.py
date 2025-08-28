#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试首次输入问题修复
"""

import sys
import os
import time

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from pyautogu import CursorAutomation, receive_from_app

def test_first_input_fix():
    """测试首次输入问题修复"""
    print("=" * 60)
    print("测试首次输入问题修复")
    print("=" * 60)
    
    automator = CursorAutomation()
    
    # 测试1: 打开对话框并检查输入状态
    print("\n1. 测试打开对话框")
    print("-" * 30)
    success = automator.open_chat_dialog()
    print(f"打开对话框结果: {'成功' if success else '失败'}")
    
    if success:
        print("等待3秒让对话框稳定...")
        time.sleep(3)
        
        # 测试2: 尝试输入文本
        print("\n2. 测试输入文本")
        print("-" * 30)
        test_text = "这是一个测试消息，用于验证首次输入问题是否修复"
        input_success = automator.input_text(test_text)
        print(f"输入文本结果: {'成功' if input_success else '失败'}")
        
        if input_success:
            # 测试3: 提交消息
            print("\n3. 测试提交消息")
            print("-" * 30)
            submit_success = automator.submit_message()
            print(f"提交消息结果: {'成功' if submit_success else '失败'}")
    
    print("\n" + "=" * 60)
    print("首次输入问题修复测试完成")
    print("=" * 60)

def test_new_chat_input_fix():
    """测试新对话输入问题修复"""
    print("\n" + "=" * 60)
    print("测试新对话输入问题修复")
    print("=" * 60)
    
    test_message = "这是一个测试消息，用于验证新对话的首次输入问题"
    print(f"测试消息: {test_message}")
    
    # 发送消息并创建新对话
    success, session_id = receive_from_app(test_message, create_new_chat=True)
    
    print(f"发送结果: {'成功' if success else '失败'}")
    if session_id:
        print(f"新session_id: {session_id}")
    else:
        print("未获取到session_id")
    
    print("\n" + "=" * 60)
    print("新对话输入问题修复测试完成")
    print("=" * 60)

def test_input_buffer_clear():
    """测试输入缓冲区清除功能"""
    print("\n" + "=" * 60)
    print("测试输入缓冲区清除功能")
    print("=" * 60)
    
    automator = CursorAutomation()
    
    # 测试1: 模拟可能的输入状态
    print("\n1. 模拟可能的输入状态")
    print("-" * 30)
    print("请手动在Cursor中输入一些内容，然后按回车继续...")
    input("按回车继续...")
    
    # 测试2: 清除输入缓冲区
    print("\n2. 清除输入缓冲区")
    print("-" * 30)
    print("正在清除输入缓冲区...")
    import pyautogui
    pyautogui.press('escape')
    time.sleep(0.5)
    print("输入缓冲区已清除")
    
    # 测试3: 打开对话框
    print("\n3. 打开对话框")
    print("-" * 30)
    success = automator.open_chat_dialog()
    print(f"打开对话框结果: {'成功' if success else '失败'}")
    
    print("\n" + "=" * 60)
    print("输入缓冲区清除测试完成")
    print("=" * 60)

if __name__ == "__main__":
    print("首次输入问题修复测试")
    print("请确保Cursor已安装并可以正常运行")
    print("注意：此测试会发送消息到Cursor，请确保没有重要工作在进行")
    
    input("\n按回车键开始测试...")
    
    try:
        test_first_input_fix()
        test_new_chat_input_fix()
        test_input_buffer_clear()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
