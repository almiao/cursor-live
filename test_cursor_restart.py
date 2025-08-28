#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Cursor重启功能
"""

import sys
import os
import time

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from pyautogu import CursorAutomation, receive_from_app

def test_cursor_restart():
    """测试Cursor重启功能"""
    print("=" * 60)
    print("测试Cursor重启功能")
    print("=" * 60)
    
    automator = CursorAutomation()
    
    # 测试1: 关闭Cursor
    print("\n1. 测试关闭Cursor")
    print("-" * 30)
    success = automator.close_cursor()
    print(f"关闭结果: {'成功' if success else '失败'}")
    
    # 等待一段时间
    print("等待3秒...")
    time.sleep(3)
    
    # 测试2: 打开Cursor
    print("\n2. 测试打开Cursor")
    print("-" * 30)
    success = automator.open_cursor()
    print(f"打开结果: {'成功' if success else '失败'}")
    
    # 等待一段时间
    print("等待5秒...")
    time.sleep(5)
    
    # 测试3: 强制重启发送消息
    print("\n3. 测试强制重启发送消息")
    print("-" * 30)
    test_message = "这是一个测试消息，用于验证强制重启功能"
    success = receive_from_app(test_message, force_restart=True)
    print(f"发送结果: {'成功' if success else '失败'}")
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)

def test_project_switch():
    """测试项目切换功能"""
    print("\n" + "=" * 60)
    print("测试项目切换功能")
    print("=" * 60)
    
    automator = CursorAutomation()
    
    # 测试切换到当前项目
    current_project = os.getcwd()
    print(f"切换到项目: {current_project}")
    
    success = automator.switch_cursor_project(current_project)
    print(f"切换结果: {'成功' if success else '失败'}")
    
    print("\n" + "=" * 60)
    print("项目切换测试完成")
    print("=" * 60)

if __name__ == "__main__":
    print("Cursor重启功能测试")
    print("请确保Cursor已安装并可以正常运行")
    print("注意：此测试会关闭并重新打开Cursor，请保存好当前工作")
    
    input("\n按回车键开始测试...")
    
    try:
        test_cursor_restart()
        test_project_switch()
    except KeyboardInterrupt:
        print("\n测试被用户中断")
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()






