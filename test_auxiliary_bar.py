#!/usr/bin/env python3
"""
测试Cursor辅助栏打开功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pyautogu import CursorAutomation
import time
import logging

# 设置详细日志
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_auxiliary_bar_detection():
    """测试辅助栏状态检测"""
    print("=" * 50)
    print("测试辅助栏状态检测")
    print("=" * 50)
    
    automation = CursorAutomation()
    
    # 测试1: 检测当前状态
    print("\n1. 检测当前辅助栏状态:")
    current_state = automation.detect_dialog_state()
    print(f"   当前状态: {current_state}")
    
    # 测试2: 获取workspace信息
    print("\n2. 获取workspace信息:")
    workspace_id = automation.get_workspace_id()
    print(f"   Workspace ID: {workspace_id}")
    
    # 测试3: 检查数据库文件
    if workspace_id:
        base = automation.cursor_root()
        workspace_db = base / "User" / "workspaceStorage" / workspace_id / "state.vscdb"
        print(f"   数据库文件路径: {workspace_db}")
        print(f"   数据库文件存在: {workspace_db.exists()}")
        
        if workspace_db.exists():
            # 测试4: 直接查询数据库
            print("\n3. 直接查询数据库:")
            try:
                import sqlite3
                con = sqlite3.connect(f"file:{workspace_db}?mode=ro", uri=True)
                cur = con.cursor()
                
                # 查询所有相关的键
                keys_to_check = [
                    "workbench.auxiliaryBar.hidden",
                    "workbench.panel.aichat.view.aichat.chatdata",
                    "workbench.auxiliaryBar.parts.editor"
                ]
                
                for key in keys_to_check:
                    cur.execute("SELECT value FROM ItemTable WHERE key=?", (key,))
                    row = cur.fetchone()
                    if row:
                        print(f"   {key}: {row[0]}")
                    else:
                        print(f"   {key}: 未找到")
                
                con.close()
            except Exception as e:
                print(f"   数据库查询失败: {e}")

def test_auxiliary_bar_opening():
    """测试辅助栏打开功能"""
    print("\n" + "=" * 50)
    print("测试辅助栏打开功能")
    print("=" * 50)
    
    automation = CursorAutomation()
    
    # 测试1: 打开聊天对话框
    print("\n1. 尝试打开聊天对话框:")
    result = automation.open_chat_dialog()
    print(f"   打开结果: {'成功' if result else '失败'}")
    
    # 等待并检测状态
    print("\n2. 等待并检测状态变化:")
    for i in range(10):
        state = automation.detect_dialog_state()
        print(f"   第{i+1}次检测: {state}")
        if state == 'dialogue':
            print("   ✓ 成功检测到对话框状态")
            break
        time.sleep(1)
    else:
        print("   ✗ 未能检测到对话框状态")

def test_alternative_methods():
    """测试替代方法"""
    print("\n" + "=" * 50)
    print("测试替代方法")
    print("=" * 50)
    
    automation = CursorAutomation()
    
    # 测试1: 尝试打开AI侧边栏
    print("\n1. 尝试打开AI侧边栏 (Command+Shift+A):")
    result = automation.open_ai_sidebar()
    print(f"   打开结果: {'成功' if result else '失败'}")
    
    # 测试2: 尝试其他快捷键
    print("\n2. 尝试其他可能的快捷键:")
    try:
        import pyautogui
        shortcuts = [
            ('Command+J', ['command', 'j']),
            ('Command+Shift+I', ['command', 'shift', 'i']),
            ('Command+Option+I', ['command', 'option', 'i']),
        ]
        
        for name, keys in shortcuts:
            print(f"   尝试 {name}...")
            pyautogui.hotkey(*keys)
            time.sleep(2)
            
            # 检测状态
            state = automation.detect_dialog_state()
            print(f"   状态: {state}")
            
            if state == 'dialogue':
                print(f"   ✓ {name} 成功打开对话框")
                break
    except Exception as e:
        print(f"   快捷键测试失败: {e}")

def main():
    """主测试函数"""
    print("Cursor辅助栏功能测试")
    print("请确保Cursor应用已打开并处于活动状态")
    input("按回车键开始测试...")
    
    # 运行测试
    test_auxiliary_bar_detection()
    test_auxiliary_bar_opening()
    test_alternative_methods()
    
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)

if __name__ == "__main__":
    main()

