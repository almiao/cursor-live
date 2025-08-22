#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AppleScript窗口焦点检测工具
用于测试Cursor应用的窗口和焦点状态检测
"""

import subprocess
import time
from datetime import datetime

def get_cursor_windows():
    """
    获取Cursor应用的窗口信息
    """
    applescript = '''
    tell application "System Events"
        try
            set cursorProcess to first application process whose name is "Cursor"
            set windowList to {}
            repeat with w in windows of cursorProcess
                set windowList to windowList & {name of w}
            end repeat
            return windowList as string
        on error
            return "No Cursor windows found"
        end try
    end tell
    '''
    
    try:
        result = subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True, timeout=5)
        return result.stdout.strip() if result.returncode == 0 else "Error getting windows"
    except:
        return "Exception getting windows"

def detect_front_app():
    """
    检测当前前台应用
    """
    applescript = '''
    tell application "System Events"
        set frontApp to name of first application process whose frontmost is true
        return frontApp
    end tell
    '''
    
    try:
        result = subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True, timeout=5)
        return result.stdout.strip() if result.returncode == 0 else "Unknown"
    except:
        return "Error"

def detect_cursor_window():
    """
    检测Cursor窗口标题
    """
    applescript = '''
    tell application "System Events"
        try
            set frontApp to name of first application process whose frontmost is true
            set frontProcess to first application process whose frontmost is true
            set frontWindow to front window of frontProcess
            set windowTitle to name of frontWindow
            return frontApp & "|" & windowTitle
        on error
            return "No window"
        end try
    end tell
    '''
    
    try:
        result = subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True, timeout=5)
        return result.stdout.strip() if result.returncode == 0 else "Error"
    except:
        return "Exception"

def detect_cursor_focus():
    """
    检测Cursor焦点状态
    """
    applescript = '''
    tell application "System Events"
        try
            set frontProcess to first application process whose frontmost is true
            set focusedElement to focused UI element of frontProcess
            if focusedElement is not missing value then
                return "HAS_FOCUS"
            else
                return "NO_FOCUS"
            end if
        on error
            return "ERROR"
        end try
    end tell
    '''
    
    try:
        result = subprocess.run(['osascript', '-e', applescript], capture_output=True, text=True, timeout=5)
        return result.stdout.strip() if result.returncode == 0 else "SCRIPT_ERROR"
    except:
        return "EXCEPTION"

def is_cursor_app(app_name, window_title):
    """
    判断是否为Cursor应用
    """
    # Cursor可能显示为Electron或Cursor
    if app_name in ["Cursor", "Electron"]:
        # 检查窗口标题是否包含Cursor相关信息
        cursor_indicators = ["cursor-live", "service-agent", ".java", ".py", ".js", ".ts", ".md"]
        return any(indicator in window_title.lower() for indicator in cursor_indicators)
    return False

def print_detection_result(front_app, window_info, focus_status):
    """
    格式化打印检测结果
    """
    timestamp = datetime.now().strftime('%H:%M:%S.%f')[:-3]
    print(f"\n[{timestamp}] === AppleScript焦点检测结果 ===")
    
    print(f"📱 前台应用: {front_app}")
    
    if "|" in window_info:
        app_name, window_title = window_info.split("|", 1)
        print(f"🪟 窗口标题: {window_title}")
        
        if is_cursor_app(app_name, window_title):
            print(f"✅ 检测到Cursor应用")
            
            if focus_status == "HAS_FOCUS":
                print(f"🎯 焦点状态: ✅ 有焦点元素")
            elif focus_status == "NO_FOCUS":
                print(f"🎯 焦点状态: ❌ 无焦点元素")
            else:
                print(f"🎯 焦点状态: ⚠️ 检测失败 ({focus_status})")
        else:
            print(f"❌ 不是Cursor应用")
    else:
        print(f"🪟 窗口信息: {window_info}")
        print(f"❌ 无法获取窗口详情")
    
    print("=" * 50)

def main():
    """
    主函数 - 循环检测Cursor焦点状态
    """
    print("🚀 AppleScript窗口焦点检测工具启动")
    print("💡 提示：请切换到Cursor应用并尝试打开/关闭聊天对话框")
    print("⏹️  按 Ctrl+C 停止检测")
    
    # 显示Cursor窗口信息
    windows_info = get_cursor_windows()
    print(f"\n📋 Cursor窗口信息:")
    print(windows_info)
    print("=" * 50)
    
    while True:
        try:
            # 执行检测
            front_app = detect_front_app()
            window_info = detect_cursor_window()
            focus_status = detect_cursor_focus()
            
            print_detection_result(front_app, window_info, focus_status)
            
            # 等待1秒
            time.sleep(1)
            
        except KeyboardInterrupt:
            print("\n\n👋 检测已停止")
            break
        except Exception as e:
            print(f"\n💥 程序异常: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(1)

if __name__ == "__main__":
    main()