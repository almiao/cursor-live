#!/usr/bin/env python3
"""
调试send_to_cursor接口的问题
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

def debug_dialog_state_detection():
    """调试对话框状态检测"""
    print("=" * 60)
    print("调试对话框状态检测")
    print("=" * 60)
    
    automation = CursorAutomation()
    
    # 测试1: 检测当前状态
    print("\n1. 检测当前对话框状态:")
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
                    "workbench.auxiliaryBar.hidden"
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

def debug_open_chat_dialog():
    """调试打开聊天对话框"""
    print("\n" + "=" * 60)
    print("调试打开聊天对话框")
    print("=" * 60)
    
    automation = CursorAutomation()
    
    # 测试1: 检查当前状态
    print("\n1. 检查当前状态:")
    current_state = automation.detect_dialog_state()
    print(f"   当前状态: {current_state}")
    
    if current_state == 'dialogue':
        print("   ✓ 对话框已经打开，无需重复打开")
        return True
    
    # 测试2: 激活Cursor
    print("\n2. 激活Cursor窗口:")
    activation_result = automation.activate_cursor()
    print(f"   激活结果: {'成功' if activation_result else '失败'}")
    
    if not activation_result:
        print("   ✗ 激活失败，无法继续")
        return False
    
    # 测试3: 发送快捷键
    print("\n3. 发送快捷键 Option+Command+B:")
    try:
        import pyautogui
        pyautogui.hotkey('option', 'command', 'b')
        print("   ✓ 已发送快捷键")
    except Exception as e:
        print(f"   ✗ 发送快捷键失败: {e}")
        return False
    
    # 测试4: 等待状态变化
    print("\n4. 等待状态变化:")
    for i in range(10):
        time.sleep(0.5)
        state = automation.detect_dialog_state()
        print(f"   第{i+1}次检测: {state}")
        if state == 'dialogue':
            print("   ✓ 成功检测到对话框状态")
            return True
    
    print("   ✗ 未能检测到对话框状态")
    return False

def debug_send_to_cursor_flow():
    """调试完整的send_to_cursor流程"""
    print("\n" + "=" * 60)
    print("调试完整的send_to_cursor流程")
    print("=" * 60)
    
    automation = CursorAutomation()
    test_message = "这是一个测试消息"
    
    print(f"测试消息: {test_message}")
    
    # 执行完整的发送流程
    success = automation.send_to_cursor(test_message, max_retries=1, skip_activation=False)
    
    print(f"\n最终结果: {'成功' if success else '失败'}")
    return success

def debug_alternative_methods():
    """调试替代方法"""
    print("\n" + "=" * 60)
    print("调试替代方法")
    print("=" * 60)
    
    automation = CursorAutomation()
    
    # 测试1: 尝试打开AI侧边栏
    print("\n1. 尝试打开AI侧边栏 (Command+Shift+A):")
    result = automation.open_ai_sidebar()
    print(f"   结果: {'成功' if result else '失败'}")
    
    # 测试2: 尝试其他快捷键
    print("\n2. 尝试其他可能的快捷键:")
    try:
        import pyautogui
        shortcuts = [
            ('Option+Command+B', ['option', 'command', 'b']),
            ('Command+I', ['command', 'i']),
            ('Command+J', ['command', 'j']),
            ('Command+Shift+A', ['command', 'shift', 'a']),
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
    """主调试函数"""
    print("send_to_cursor接口调试工具")
    print("请确保Cursor应用已打开")
    input("按回车键开始调试...")
    
    # 运行调试
    debug_dialog_state_detection()
    debug_open_chat_dialog()
    debug_send_to_cursor_flow()
    # debug_alternative_methods()
    
    print("\n" + "=" * 60)
    print("调试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()

