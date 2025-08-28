#!/usr/bin/env python3
"""
调试数据库状态检测问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pyautogu import CursorAutomation
import time
import sqlite3
import json

def print_database_details():
    """打印详细的数据库信息"""
    print("=" * 60)
    print("数据库状态详细信息")
    print("=" * 60)
    
    automation = CursorAutomation()
    
    # 获取workspace信息
    workspace_id = automation.get_workspace_id()
    print(f"Workspace ID: {workspace_id}")
    
    if not workspace_id:
        print("❌ 无法获取workspace ID")
        return
    
    # 获取数据库路径
    base = automation.cursor_root()
    workspace_db = base / "User" / "workspaceStorage" / workspace_id / "state.vscdb"
    print(f"数据库路径: {workspace_db}")
    print(f"数据库存在: {workspace_db.exists()}")
    
    if not workspace_db.exists():
        print("❌ 数据库文件不存在")
        return
    
    # 连接数据库并查询详细信息
    try:
        con = sqlite3.connect(f"file:{workspace_db}?mode=ro", uri=True)
        cur = con.cursor()
        
        # 查询所有相关的键
        print("\n" + "=" * 40)
        print("相关配置项:")
        print("=" * 40)
        
        keys_to_check = [
            "workbench.auxiliaryBar.hidden",
            "workbench.auxiliaryBar.visible", 
            "workbench.auxiliaryBar.parts.editor",
            "workbench.panel.aichat.view.aichat.chatdata",
            "workbench.auxiliaryBar.location",
            "workbench.auxiliaryBar.size",
            "workbench.auxiliaryBar.lastKnownSize",
            "workbench.auxiliaryBar.lastKnownLocation"
        ]
        
        for key in keys_to_check:
            cur.execute("SELECT value FROM ItemTable WHERE key=?", (key,))
            row = cur.fetchone()
            if row:
                print(f"✅ {key}: {row[0]}")
            else:
                print(f"❌ {key}: 未找到")
        
        # 查询所有包含auxiliaryBar的键
        print("\n" + "=" * 40)
        print("所有包含auxiliaryBar的配置项:")
        print("=" * 40)
        
        cur.execute("SELECT key, value FROM ItemTable WHERE key LIKE '%auxiliaryBar%'")
        auxiliary_bar_items = cur.fetchall()
        
        if auxiliary_bar_items:
            for key, value in auxiliary_bar_items:
                print(f"🔍 {key}: {value}")
        else:
            print("❌ 未找到任何包含auxiliaryBar的配置项")
        
        # 查询所有包含aichat的键
        print("\n" + "=" * 40)
        print("所有包含aichat的配置项:")
        print("=" * 40)
        
        cur.execute("SELECT key, value FROM ItemTable WHERE key LIKE '%aichat%'")
        aichat_items = cur.fetchall()
        
        if aichat_items:
            for key, value in aichat_items:
                print(f"🤖 {key}: {value}")
        else:
            print("❌ 未找到任何包含aichat的配置项")
        
        # 查询数据库表结构
        print("\n" + "=" * 40)
        print("数据库表结构:")
        print("=" * 40)
        
        cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cur.fetchall()
        for table in tables:
            print(f"📋 表名: {table[0]}")
        
        # 查询ItemTable的总记录数
        cur.execute("SELECT COUNT(*) FROM ItemTable")
        count = cur.fetchone()[0]
        print(f"📊 ItemTable总记录数: {count}")
        
        con.close()
        
    except Exception as e:
        print(f"❌ 数据库查询失败: {e}")
        import traceback
        traceback.print_exc()

def monitor_database_changes():
    """监控数据库状态变化"""
    print("\n" + "=" * 60)
    print("监控数据库状态变化")
    print("=" * 60)
    
    automation = CursorAutomation()
    
    # 获取初始状态
    print("1. 获取初始状态:")
    initial_state = automation.detect_dialog_state()
    print(f"   初始状态: {initial_state}")
    
    # 发送快捷键
    print("\n2. 发送快捷键 Option+Command+B:")
    try:
        import pyautogui
        pyautogui.hotkey('option', 'command', 'b')
        print("   ✅ 已发送快捷键")
    except Exception as e:
        print(f"   ❌ 发送快捷键失败: {e}")
        return
    
    # 监控状态变化
    print("\n3. 监控状态变化:")
    for i in range(10):
        time.sleep(1)
        state = automation.detect_dialog_state()
        print(f"   第{i+1}秒: {state}")
        
        if state == 'dialogue':
            print("   ✅ 检测到对话框状态变化")
            break
    else:
        print("   ❌ 10秒内未检测到状态变化")
    
    # 再次打印数据库详情
    print("\n4. 发送快捷键后的数据库状态:")
    print_database_details()

def main():
    """主函数"""
    print("数据库状态调试工具")
    print("请确保Cursor应用已打开")
    input("按回车键开始调试...")
    
    # 打印当前数据库详情
    print_database_details()
    
    # 监控状态变化
    monitor_database_changes()
    
    print("\n" + "=" * 60)
    print("调试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
