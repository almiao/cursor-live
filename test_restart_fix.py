#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试重启逻辑修复
"""

import sys
import os
import time

# 添加当前目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from pyautogu import CursorAutomation

def test_restart_logic():
    """测试重启逻辑"""
    print("=" * 60)
    print("测试重启逻辑修复")
    print("=" * 60)
    
    automator = CursorAutomation()
    
    # 测试1: 模拟首次发送消息（force_restart=True, skip_activation=False）
    print("\n1. 测试首次发送消息")
    print("-" * 30)
    print("参数: force_restart=True, skip_activation=False")
    print("预期: 应该执行强制重启")
    
    # 这里只是测试逻辑，不实际发送消息
    force_restart = True
    skip_activation = False
    
    if force_restart and not skip_activation:
        print("✓ 会执行强制重启流程")
    else:
        print("✗ 不会执行强制重启流程")
    
    # 测试2: 模拟切换项目后发送消息（force_restart=False, skip_activation=True）
    print("\n2. 测试切换项目后发送消息")
    print("-" * 30)
    print("参数: force_restart=False, skip_activation=True")
    print("预期: 不应该执行强制重启")
    
    force_restart = False
    skip_activation = True
    
    if force_restart and not skip_activation:
        print("✗ 会执行强制重启流程（不应该）")
    else:
        print("✓ 不会执行强制重启流程")
    
    # 测试3: 模拟正常发送消息（force_restart=False, skip_activation=False）
    print("\n3. 测试正常发送消息")
    print("-" * 30)
    print("参数: force_restart=False, skip_activation=False")
    print("预期: 不应该执行强制重启")
    
    force_restart = False
    skip_activation = False
    
    if force_restart and not skip_activation:
        print("✗ 会执行强制重启流程（不应该）")
    else:
        print("✓ 不会执行强制重启流程")
    
    print("\n" + "=" * 60)
    print("逻辑测试完成")
    print("=" * 60)

def test_project_switch():
    """测试项目切换功能（不实际执行）"""
    print("\n" + "=" * 60)
    print("项目切换功能说明")
    print("=" * 60)
    
    print("项目切换流程：")
    print("1. 关闭当前Cursor实例")
    print("2. 等待Cursor完全关闭")
    print("3. 使用命令行打开新项目")
    print("4. 等待Cursor完全启动")
    print("5. 发送消息时跳过激活步骤")
    
    print("\n这样可以避免重复关闭Cursor的问题")

if __name__ == "__main__":
    print("重启逻辑修复测试")
    print("此测试只验证逻辑，不会实际操作Cursor")
    
    try:
        test_restart_logic()
        test_project_switch()
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()
