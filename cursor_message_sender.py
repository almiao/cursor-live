#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor消息发送工具
使用AppleScript和pyautogui可靠地向Cursor AI对话发送消息
"""

import subprocess
import time
import urllib.parse
import pyautogui
from datetime import datetime

class CursorMessageSender:
    def __init__(self):
        self.last_message_time = 0
        self.min_interval = 1.0  # 最小发送间隔（秒）
    
    def send_via_applescript(self, message):
        """
        使用AppleScript发送消息（推荐方法）
        """
        # 转义特殊字符
        escaped_message = message.replace('"', '\\"').replace("'", "\\'")
        
        applescript = f'''
        tell application "System Events"
            try
                -- 确保Cursor是前台应用
                set frontApp to name of first application process whose frontmost is true
                if frontApp is not "Cursor" then
                    return "NOT_CURSOR|" & frontApp
                end if
                
                -- 输入消息
                keystroke "{escaped_message}"
                delay 0.3
                
                -- 按回车发送
                key code 36
                
                return "SUCCESS"
            on error errMsg
                return "ERROR|" & errMsg
            end try
        end tell
        '''
        
        try:
            result = subprocess.run(['osascript', '-e', applescript], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if output == "SUCCESS":
                    return True, "消息发送成功"
                elif output.startswith("NOT_CURSOR"):
                    app_name = output.split("|")[1] if "|" in output else "未知应用"
                    return False, f"Cursor不是前台应用，当前应用是: {app_name}"
                else:
                    return False, f"AppleScript错误: {output}"
            else:
                return False, f"脚本执行失败: {result.stderr.decode()}"
                
        except subprocess.TimeoutExpired:
            return False, "脚本执行超时"
        except Exception as e:
            return False, f"执行异常: {e}"
    
    def send_via_pyautogui(self, message):
        """
        使用pyautogui发送消息
        """
        try:
            # 检查时间间隔
            current_time = time.time()
            if current_time - self.last_message_time < self.min_interval:
                time.sleep(self.min_interval - (current_time - self.last_message_time))
            
            # 输入消息
            pyautogui.write(message)
            time.sleep(0.3)
            
            # 按回车发送
            pyautogui.press('enter')
            
            self.last_message_time = time.time()
            return True, "消息发送成功"
            
        except Exception as e:
            return False, f"pyautogui错误: {e}"
    
    def send_via_clipboard(self, message):
        """
        使用剪贴板发送消息
        """
        try:
            # 设置剪贴板
            escaped_message = message.replace('"', '\\"')
            set_clipboard_script = f'''
            tell application "System Events"
                set the clipboard to "{escaped_message}"
            end tell
            '''
            
            result = subprocess.run(['osascript', '-e', set_clipboard_script], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode != 0:
                return False, "剪贴板设置失败"
            
            # 粘贴并发送
            paste_script = '''
            tell application "System Events"
                keystroke "v" using command down
                delay 0.3
                key code 36
            end tell
            '''
            
            result2 = subprocess.run(['osascript', '-e', paste_script], 
                                   capture_output=True, text=True, timeout=5)
            
            if result2.returncode == 0:
                return True, "剪贴板发送成功"
            else:
                return False, "粘贴发送失败"
                
        except Exception as e:
            return False, f"剪贴板操作异常: {e}"
    
    def send_message(self, message, method="auto"):
        """
        发送消息到Cursor AI对话
        
        Args:
            message: 要发送的消息
            method: 发送方法 ("auto", "applescript", "pyautogui", "clipboard")
        """
        timestamp = datetime.now().strftime('%H:%M:%S')
        print(f"[{timestamp}] 📤 发送消息: {message}")
        
        if method == "auto":
            # 自动选择最佳方法
            success, result = self.send_via_applescript(message)
            if success:
                print(f"✅ {result}")
                return True
            else:
                print(f"⚠️  AppleScript失败: {result}")
                print("🔄 尝试pyautogui方法...")
                
                success2, result2 = self.send_via_pyautogui(message)
                if success2:
                    print(f"✅ {result2}")
                    return True
                else:
                    print(f"❌ pyautogui也失败: {result2}")
                    return False
        
        elif method == "applescript":
            success, result = self.send_via_applescript(message)
            print(f"✅ {result}" if success else f"❌ {result}")
            return success
        
        elif method == "pyautogui":
            success, result = self.send_via_pyautogui(message)
            print(f"✅ {result}" if success else f"❌ {result}")
            return success
        
        elif method == "clipboard":
            success, result = self.send_via_clipboard(message)
            print(f"✅ {result}" if success else f"❌ {result}")
            return success
        
        else:
            print(f"❌ 未知的发送方法: {method}")
            return False

def test_message_sender():
    """
    测试消息发送器
    """
    print("🚀 Cursor消息发送器测试")
    print("=" * 50)
    
    sender = CursorMessageSender()
    
    # 测试消息
    test_messages = [
        "你好，请帮我写一个Python函数",
        "实现快速排序算法",
        "请解释一下什么是递归",
        "帮我优化这段代码的性能"
    ]
    
    print("请确保:")
    print("1. Cursor已打开")
    print("2. 光标在AI对话框输入框中")
    print("3. 准备好观察消息发送效果")
    
    input("\n按回车键开始测试...")
    
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- 测试消息 {i} ---")
        success = sender.send_message(message, method="auto")
        
        if success:
            print("✅ 消息发送成功")
        else:
            print("❌ 消息发送失败")
        
        # 等待一下
        time.sleep(2)

def interactive_mode():
    """
    交互式模式
    """
    print("💬 交互式消息发送模式")
    print("输入消息发送到Cursor（输入 'quit' 退出）")
    print("=" * 50)
    
    sender = CursorMessageSender()
    
    while True:
        try:
            message = input("\n💬 请输入消息: ").strip()
            
            if message.lower() in ['quit', 'exit', 'q']:
                print("👋 退出交互式模式")
                break
            
            if not message:
                continue
            
            success = sender.send_message(message, method="auto")
            
            if not success:
                print("❌ 发送失败，请检查Cursor状态")
                
        except KeyboardInterrupt:
            print("\n👋 退出交互式模式")
            break
        except Exception as e:
            print(f"❌ 输入错误: {e}")

def main():
    """
    主函数
    """
    print("🚀 Cursor消息发送工具")
    print("=" * 50)
    print("选择模式:")
    print("1. 测试模式")
    print("2. 交互式模式")
    print("0. 退出")
    
    while True:
        try:
            choice = input("\n请选择 (0-2): ").strip()
            
            if choice == '0':
                print("👋 退出程序")
                break
            elif choice == '1':
                test_message_sender()
                break
            elif choice == '2':
                interactive_mode()
                break
            else:
                print("❌ 无效选择，请输入 0-2")
                
        except KeyboardInterrupt:
            print("\n👋 退出程序")
            break
        except Exception as e:
            print(f"❌ 输入错误: {e}")

if __name__ == "__main__":
    main()
