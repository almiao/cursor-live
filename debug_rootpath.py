#!/usr/bin/env python3
"""
调试rootPath获取过程
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pathlib
import sqlite3
import json
import logging

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def cursor_root() -> pathlib.Path:
    """获取Cursor根目录路径"""
    h = pathlib.Path.home()
    s = os.name
    if s == "posix":  # macOS/Linux
        if os.uname().sysname == "Darwin":  # macOS
            return h / "Library" / "Application Support" / "Cursor"
        else:  # Linux
            return h / ".config" / "Cursor"
    else:  # Windows
        return h / "AppData" / "Roaming" / "Cursor"

def j(cur: sqlite3.Cursor, table: str, key: str):
    """查询数据库中的JSON配置值"""
    cur.execute(f"SELECT value FROM {table} WHERE key=?", (key,))
    row = cur.fetchone()
    if row:
        try:
            return json.loads(row[0])
        except Exception as e:
            logger.debug(f"Failed to parse JSON for {key}: {e}")
    return None

def get_workspace_id() -> str:
    """获取当前工作区的ID"""
    try:
        # 获取Cursor根目录
        base = cursor_root()
        workspace_storage = base / "User" / "workspaceStorage"
        
        if not workspace_storage.exists():
            logger.warning(f"Workspace存储目录不存在: {workspace_storage}")
            return None
        
        # 查找最新的workspace数据库
        workspace_dirs = list(workspace_storage.glob("*"))
        if not workspace_dirs:
            logger.warning("未找到任何workspace目录")
            return None
        
        # 按修改时间排序，获取最新的
        latest_workspace = max(workspace_dirs, key=lambda x: x.stat().st_mtime)
        return latest_workspace.name
        
    except Exception as e:
        logger.error(f"获取workspace ID失败: {e}")
        return None

def debug_rootpath_extraction():
    """调试rootPath提取过程"""
    print("=" * 60)
    print("调试rootPath提取过程")
    print("=" * 60)
    
    # 获取workspace ID
    workspace_id = get_workspace_id()
    print(f"Workspace ID: {workspace_id}")
    
    if not workspace_id:
        print("❌ 无法获取workspace ID")
        return
    
    # 获取数据库路径
    base = cursor_root()
    workspace_db = base / "User" / "workspaceStorage" / workspace_id / "state.vscdb"
    print(f"数据库路径: {workspace_db}")
    print(f"数据库存在: {workspace_db.exists()}")
    
    if not workspace_db.exists():
        print("❌ 数据库文件不存在")
        return
    
    # 连接数据库并查询
    try:
        con = sqlite3.connect(f"file:{workspace_db}?mode=ro", uri=True)
        cur = con.cursor()
        
        print("\n" + "=" * 40)
        print("1. 查询history.entries:")
        print("=" * 40)
        
        # 查询history.entries
        history_entries = j(cur, "ItemTable", "history.entries")
        if history_entries:
            print(f"✅ 找到 {len(history_entries)} 个历史条目")
            
            # 提取文件路径
            paths = []
            for e in history_entries:
                resource = e.get("editor", {}).get("resource", "")
                if resource and resource.startswith("file:///"):
                    path = resource[len("file:///"):]
                    paths.append(path)
                    print(f"   📁 {path}")
            
            if paths:
                print(f"\n📊 找到 {len(paths)} 个文件路径")
                
                # 计算最长公共前缀
                import os
                common_prefix = os.path.commonprefix(paths)
                print(f"🔍 最长公共前缀: {common_prefix}")
                
                # 找到最后一个目录分隔符
                last_separator_index = common_prefix.rfind('/')
                if last_separator_index > 0:
                    project_root = common_prefix[:last_separator_index]
                    print(f"📂 项目根目录: {project_root}")
                    print(f"🏷️  rootPath: /{project_root.lstrip('/')}")
                else:
                    print("❌ 无法从公共前缀提取项目根目录")
            else:
                print("❌ 未找到有效的文件路径")
        else:
            print("❌ 未找到history.entries")
        
        print("\n" + "=" * 40)
        print("2. 查询debug.selectedroot:")
        print("=" * 40)
        
        # 查询debug.selectedroot
        selected_root = j(cur, "ItemTable", "debug.selectedroot")
        if selected_root:
            print(f"✅ debug.selectedroot: {selected_root}")
            if isinstance(selected_root, str) and selected_root.startswith("file:///"):
                path = selected_root[len("file:///"):]
                if path:
                    root_path = "/" + path.strip("/")
                    print(f"🏷️  rootPath: {root_path}")
        else:
            print("❌ 未找到debug.selectedroot")
        
        print("\n" + "=" * 40)
        print("3. 查询所有包含path的配置项:")
        print("=" * 40)
        
        # 查询所有包含path的键
        cur.execute("SELECT key, value FROM ItemTable WHERE key LIKE '%path%' OR key LIKE '%root%'")
        path_items = cur.fetchall()
        
        if path_items:
            for key, value in path_items:
                print(f"🔍 {key}: {value}")
        else:
            print("❌ 未找到包含path或root的配置项")
        
        con.close()
        
    except Exception as e:
        print(f"❌ 数据库查询失败: {e}")
        import traceback
        traceback.print_exc()

def test_workspace_info():
    """测试workspace_info函数"""
    print("\n" + "=" * 60)
    print("测试workspace_info函数")
    print("=" * 60)
    
    # 导入workspace_info函数
    from server import workspace_info, cursor_root
    
    # 获取workspace ID
    workspace_id = get_workspace_id()
    if not workspace_id:
        print("❌ 无法获取workspace ID")
        return
    
    # 获取数据库路径
    base = cursor_root()
    workspace_db = base / "User" / "workspaceStorage" / workspace_id / "state.vscdb"
    
    if not workspace_db.exists():
        print("❌ 数据库文件不存在")
        return
    
    # 调用workspace_info函数
    try:
        proj, comp_meta = workspace_info(workspace_db)
        print(f"📁 项目名称: {proj['name']}")
        print(f"🏷️  rootPath: {proj['rootPath']}")
        print(f"📊 作曲家数量: {len(comp_meta)}")
        
        # 显示作曲家信息
        if comp_meta:
            print("\n作曲家信息:")
            for comp_id, comp_info in list(comp_meta.items())[:5]:  # 只显示前5个
                print(f"   {comp_id[:8]}: {comp_info['title']}")
        
    except Exception as e:
        print(f"❌ workspace_info调用失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    """主函数"""
    print("rootPath获取调试工具")
    input("按回车键开始调试...")
    
    # 调试rootPath提取过程
    debug_rootpath_extraction()
    
    # 测试workspace_info函数
    test_workspace_info()
    
    print("\n" + "=" * 60)
    print("调试完成")
    print("=" * 60)

if __name__ == "__main__":
    main()
