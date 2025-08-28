#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试新对话功能
"""

import sys
import os
import time

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from pyautogu import CursorAutomation, receive_from_app

def test_new_chat_creation():
    """测试新对话创建功能"""
    print("=" * 60)
    print("测试新对话创建功能")
    print("=" * 60)
    
    automator = CursorAutomation()
    
    # 测试1: 创建新对话
    print("\n1. 测试创建新对话")
    print("-" * 30)
    success = automator.create_new_chat()
    print(f"创建新对话结果: {'成功' if success else '失败'}")
    
    if success:
        # 等待一段时间让新对话创建完成
        print("等待3秒让新对话创建完成...")
        time.sleep(3)
        
        # 测试2: 获取最新session_id
        print("\n2. 测试获取最新session_id")
        print("-" * 30)
        session_id = automator.get_latest_session_id()
        if session_id:
            print(f"最新session_id: {session_id}")
        else:
            print("未找到session_id")
    
    print("\n" + "=" * 60)
    print("新对话创建测试完成")
    print("=" * 60)

def test_send_with_new_chat():
    """测试发送消息并创建新对话"""
    print("\n" + "=" * 60)
    print("测试发送消息并创建新对话")
    print("=" * 60)
    
    test_message = "这是一个测试消息，用于验证新对话功能"
    print(f"测试消息: {test_message}")
    
    # 发送消息并创建新对话
    success, session_id = receive_from_app(test_message, create_new_chat=True)
    
    print(f"发送结果: {'成功' if success else '失败'}")
    if session_id:
        print(f"新session_id: {session_id}")
    else:
        print("未获取到session_id")
    
    print("\n" + "=" * 60)
    print("发送消息并创建新对话测试完成")
    print("=" * 60)

def test_get_latest_session_id():
    """测试获取最新session_id功能"""
    print("\n" + "=" * 60)
    print("测试获取最新session_id功能")
    print("=" * 60)
    
    automator = CursorAutomation()
    
    # 获取当前workspace_id
    workspace_id = automator.get_workspace_id()
    print(f"当前workspace_id: {workspace_id}")
    
    # 获取最新session_id
    session_id = automator.get_latest_session_id(workspace_id)
    if session_id:
        print(f"最新session_id: {session_id}")
    else:
        print("未找到session_id")
    
    print("\n" + "=" * 60)
    print("获取最新session_id测试完成")
    print("=" * 60)

if __name__ == "__main__":
    print("新对话功能测试")
    print("请确保Cursor已安装并可以正常运行")
    print("注意：此测试会创建新对话，请确保没有重要工作在进行")
    
    input("\n按回车键开始测试...")
    
    try:
        test_new_chat_creation()
        test_send_with_new_chat()
        test_get_latest_session_id()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
