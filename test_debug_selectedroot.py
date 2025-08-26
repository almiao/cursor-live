#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试debug.selectedroot的读取功能
"""

import sqlite3
import json
import pathlib
import urllib.parse
import logging

# 设置日志
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def j(cur: sqlite3.Cursor, table: str, key: str):
    """从数据库中获取JSON值"""
    cur.execute(f"SELECT value FROM {table} WHERE key=?", (key,))
    row = cur.fetchone()
    if row:
        try:    
            return json.loads(row[0])
        except Exception as e: 
            logger.debug(f"Failed to parse JSON for {key}: {e}")
    return None

def test_debug_selectedroot():
    """测试debug.selectedroot的读取"""
    # 用户提供的数据库路径
    db_path = "/Users/dxm/Library/Application Support/Cursor/User/workspaceStorage/9072e5b3a13b781b403c9304d73302b3/state.vscdb"
    
    print(f"=== 测试数据库: {db_path} ===")
    
    try:
        con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cur = con.cursor()
        
        # 测试1: 使用j函数（JSON解析）
        print("\n1. 使用j函数（JSON解析）:")
        selected_root_json = j(cur, "ItemTable", "debug.selectedroot")
        print(f"   结果: {selected_root_json}")
        print(f"   类型: {type(selected_root_json)}")
        
        # 测试2: 直接获取原始字符串
        print("\n2. 直接获取原始字符串:")
        cur.execute("SELECT value FROM ItemTable WHERE key=?", ("debug.selectedroot",))
        row = cur.fetchone()
        if row:
            selected_root_raw = row[0]
            print(f"   结果: {selected_root_raw}")
            print(f"   类型: {type(selected_root_raw)}")
            
            # 测试URI解析
            if selected_root_raw and selected_root_raw.startswith("file:///"):
                print("\n3. URI解析测试（新逻辑）:")
                try:
                    path = pathlib.Path(urllib.parse.unquote(selected_root_raw[len("file:///"):])).as_posix()
                    if not path.startswith("/"):
                        path = "/" + path
                    print(f"   解析后路径: {path}")
                    
                    # 应用新的路径处理逻辑
                    path_obj = pathlib.Path(path)
                    if path_obj.is_file() or path.endswith(('.json', '.js', '.ts', '.py', '.md', '.txt')):
                        # It's a file, get the parent directory
                        root_path = str(path_obj.parent)
                        print(f"   检测到文件，使用父目录: {root_path}")
                    else:
                        # It's likely a directory
                        root_path = path
                        print(f"   使用路径作为目录: {root_path}")
                    
                    # Further check: if we got .vscode or similar config directory, go up one more level
                    if root_path.endswith(('/.vscode', '/.git', '/.idea', '/node_modules')):
                        root_path = str(pathlib.Path(root_path).parent)
                        print(f"   检测到配置目录，使用上级目录: {root_path}")
                    
                    if root_path and root_path != "/":
                        print(f"   最终根路径: {root_path}")
                        
                        # 提取项目名称
                        project_name = pathlib.Path(root_path).name if pathlib.Path(root_path).name else "Unknown"
                        print(f"   项目名称: {project_name}")
                    else:
                        print(f"   无效的根路径: {root_path}")
                    
                except Exception as e:
                    print(f"   URI解析失败: {e}")
        else:
            print("   未找到debug.selectedroot")
        
        # 测试3: 检查history.entries
        print("\n4. 检查history.entries:")
        history_entries = j(cur, "ItemTable", "history.entries")
        print(f"   结果: {history_entries}")
        print(f"   类型: {type(history_entries)}")
        if history_entries:
            print(f"   条目数量: {len(history_entries)}")
        
        con.close()
        
    except Exception as e:
        print(f"数据库连接或查询失败: {e}")

if __name__ == "__main__":
    test_debug_selectedroot()