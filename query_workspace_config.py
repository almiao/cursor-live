#!/usr/bin/env python3
import sqlite3
import json
import pathlib

def j(cur: sqlite3.Cursor, table: str, key: str):
    """查询数据库中的JSON配置值"""
    cur.execute(f"SELECT value FROM {table} WHERE key=?", (key,))
    row = cur.fetchone()
    if row:
        try:
            return json.loads(row[0])
        except Exception as e:
            print(f"解析JSON失败 {key}: {e}")
    return None

def query_workspace_config(db_path: str, key: str = "workbench.auxiliaryBar.hidden"):
    """查询workspace数据库中的配置值"""
    db_file = pathlib.Path(db_path)
    
    if not db_file.exists():
        print(f"数据库文件不存在: {db_path}")
        return
    
    try:
        # 连接数据库
        con = sqlite3.connect(f"file:{db_file}?mode=ro", uri=True)
        cur = con.cursor()
        
        # 查询指定配置的值
        value = j(cur, "ItemTable", key)
        
        print(f"配置键: {key}")
        print(f"配置值: {value}")
        print(f"类型: {type(value)}")
        
        # 如果是布尔值，显示更友好的信息
        if isinstance(value, bool):
            print(f"侧边栏状态: {'隐藏' if value else '显示'}")
        
        con.close()
        
    except Exception as e:
        print(f"查询失败: {e}")

if __name__ == "__main__":
    # 您提供的数据库路径
    db_path = "/Users/dxm/Library/Application Support/Cursor/User/workspaceStorage/c27e103d94c8551d951a6e721a27b5f5/state.vscdb"
    
    # 查询workbench.auxiliaryBar.hidden配置
    query_workspace_config(db_path, "workbench.auxiliaryBar.hidden")
    
    # 也可以查询其他相关配置
    print("\n" + "="*50)
    print("其他相关配置:")
    
    other_configs = [
        "workbench.panel.aichat.view.aichat.chatdata",
        "composer.composerData",
        "workbench.sideBar.hidden"
    ]
    
    for config in other_configs:
        print(f"\n查询: {config}")
        query_workspace_config(db_path, config)
