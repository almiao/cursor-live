import pyautogui
import time
import subprocess
import platform
import logging
from typing import Optional

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CursorAutomation:
    def __init__(self):
        self.system = platform.system()
        self.modifier = 'command' if self.system == 'Darwin' else 'ctrl'
        self.alt_modifier = 'option' if self.system == 'Darwin' else 'alt'
        
    def open_cursor(self) -> bool:
        """打开Cursor应用"""
        try:
            if self.system == 'Darwin':
                # Mac: 使用open命令打开Cursor
                subprocess.run(['open', '-a', 'Cursor'])
            elif self.system == 'Windows':
                # Windows: 尝试通过开始菜单或直接路径打开
                try:
                    subprocess.run(['start', 'cursor:'], shell=True)
                except:
                    # 如果上述方法失败，尝试直接路径
                    subprocess.run(['C:\\Program Files\\Cursor\\Cursor.exe'])
            else:
                # Linux
                subprocess.run(['cursor'])
            
            logger.info("已尝试打开Cursor")
            time.sleep(3)  # 等待应用启动
            return True
            
        except Exception as e:
            logger.error(f"打开Cursor失败: {e}")
            return False
    
    def activate_cursor(self) -> bool:
        """激活Cursor窗口"""
        try:
            if self.system == 'Darwin':
                # macOS: 使用Bundle ID激活Cursor应用（更可靠）
                script = '''
                tell application id "com.todesktop.230313mzl4w4u92"
                    activate
                end tell
                '''
                result = subprocess.run(['osascript', '-e', script], 
                                       capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info("已激活Cursor窗口")
                    time.sleep(1)
                    return True
                else:
                    # 如果Bundle ID失败，尝试使用进程名
                    logger.warning("Bundle ID激活失败，尝试使用进程名")
                    script_fallback = '''
                    tell application "System Events"
                        set appName to "Electron"
                        if exists (processes whose name is appName) then
                            tell application appName to activate
                            return true
                        else
                            return false
                        end if
                    end tell
                    '''
                    result = subprocess.run(['osascript', '-e', script_fallback], 
                                           capture_output=True, text=True)
                    if result.returncode == 0 and 'true' in result.stdout:
                        logger.info("已激活Cursor窗口（通过进程名）")
                        time.sleep(1)
                        return True
                    else:
                        logger.warning("未找到Cursor窗口，尝试打开")
                        return self.open_cursor()
            else:
                # Windows/Linux: 直接尝试打开Cursor应用
                 # 注意：pyautogui的getWindowsWithTitle在某些系统上不可用
                 logger.info("非macOS系统，直接尝试打开Cursor")
                 return self.open_cursor()
                
        except Exception as e:
            logger.error(f"激活Cursor窗口失败: {e}")
            return False
    
    def open_chat_dialog(self, skip_activation: bool = False) -> bool:
        """调出聊天对话框（Command/Ctrl + I）
        
        Args:
            skip_activation: 是否跳过激活步骤
        """
        try:
            # 确保Cursor是活动窗口（如果不跳过激活）
            if not skip_activation:
                self.activate_cursor()
                time.sleep(1)  # 等待窗口激活
            else:
                logger.info("跳过对话框激活步骤")
                time.sleep(0.5)  # 短暂等待
            
            # 发送快捷键：Command/Ctrl + I
            pyautogui.hotkey(self.modifier, 'i')
            logger.info("已发送快捷键 Command+I 打开聊天对话框")
            time.sleep(2)  # 等待对话框打开
            
            return True
            
        except Exception as e:
            logger.error(f"打开聊天对话框失败: {e}")
            return False
    
    def input_text(self, text: str) -> bool:
        """
        在Cursor聊天对话框中输入文本
        
        Args:
            text: 要输入的文本
            
        Returns:
            bool: 输入成功返回True，失败返回False
        """
        try:
            logger.info(f"开始输入文本: {text[:50]}...")
            
            # 等待对话框稳定
            time.sleep(1)
            
            # 尝试多种输入方法
            success = False
            
            # 方法1: 使用剪贴板（最可靠）
            try:
                import subprocess
                subprocess.run(['pbcopy'], input=text.encode('utf-8'))
                pyautogui.hotkey(self.modifier, 'v')
                logger.info(f"已通过剪贴板输入文本: {text[:50]}...")
                success = True
            except Exception as e:
                logger.warning(f"剪贴板输入失败: {e}")
            
            # 方法2: 如果剪贴板失败，使用pyautogui.write
            if not success:
                try:
                    pyautogui.write(text, interval=0.1)
                    logger.info(f"已通过write方法输入文本: {text[:50]}...")
                    success = True
                except Exception as e:
                    logger.warning(f"write方法失败: {e}")
            
            # 方法3: 如果都失败，尝试逐字符输入
            if not success:
                try:
                    for char in text:
                        pyautogui.press(char)
                        time.sleep(0.05)
                    logger.info(f"已通过逐字符输入文本: {text[:50]}...")
                    success = True
                except Exception as e:
                    logger.warning(f"逐字符输入失败: {e}")
            
            if not success:
                logger.error("所有文本输入方法都失败")
                return False
            
            # 等待文本输入完成
            time.sleep(1)
            return True
            
        except Exception as e:
            logger.error(f"输入文本失败: {e}")
            return False
    
    def submit_message(self) -> bool:
        """提交消息（通常是Enter或Command+Enter）"""
        try:
            # 尝试不同的提交方式
            submit_methods = [
                lambda: pyautogui.press('enter'),
                lambda: pyautogui.hotkey(self.modifier, 'enter'),
                lambda: pyautogui.hotkey('ctrl', 'enter')
            ]
            
            for method in submit_methods:
                try:
                    method()
                    logger.info("已尝试提交消息")
                    time.sleep(0.5)
                    # 检查是否提交成功（可以根据需要添加验证逻辑）
                    return True
                except:
                    continue
            
            logger.warning("所有提交方式都失败")
            return False
            
        except Exception as e:
            logger.error(f"提交消息失败: {e}")
            return False
    
    def send_to_cursor(self, text: str, max_retries: int = 3, skip_activation: bool = False) -> bool:
        """完整的发送流程
        
        Args:
            text: 要发送的文本
            max_retries: 最大重试次数
            skip_activation: 是否跳过激活步骤（当刚切换项目后使用）
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"尝试第 {attempt + 1} 次发送")
                
                # 1. 激活或打开Cursor（如果不跳过激活）
                if not skip_activation:
                    if not self.activate_cursor():
                        continue
                else:
                    logger.info("跳过激活步骤，使用当前Cursor窗口")
                    time.sleep(2)  # 等待Cursor稳定
                
                # 2. 打开聊天对话框
                if not self.open_chat_dialog(skip_activation=skip_activation):
                    continue
                
                # 3. 输入文本
                if not self.input_text(text):
                    continue
                
                # 4. 提交消息
                if not self.submit_message():
                    continue
                
                logger.info("消息发送成功！")
                return True
                
            except Exception as e:
                logger.error(f"第 {attempt + 1} 次尝试失败: {e}")
                time.sleep(2)  # 失败后等待一会儿再重试
        
        logger.error(f"所有 {max_retries} 次尝试都失败")
        return False
    
    def switch_cursor_project(self, root_path: str) -> bool:
        """切换Cursor到指定项目目录"""
        try:
            logger.info(f"正在切换到项目: {root_path}")
            
            # 在终端中执行cursor命令打开指定项目
            if self.system == 'Darwin':
                # macOS: 使用Terminal执行cursor命令
                script = f'''
                tell application "Terminal"
                    activate
                    do script "cursor '{root_path}'"
                end tell
                '''
                result = subprocess.run(['osascript', '-e', script], 
                                       capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info(f"已在Terminal中执行: cursor '{root_path}'")
                    time.sleep(5)  # 增加等待时间，确保Cursor完全加载项目
                    return True
                else:
                    logger.error(f"Terminal脚本执行失败: {result.stderr}")
                    return False
            else:
                # Windows/Linux: 直接执行cursor命令
                try:
                    result = subprocess.run(['cursor', root_path], 
                                           capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        logger.info(f"已执行: cursor {root_path}")
                        time.sleep(5)  # 增加等待时间，确保Cursor完全加载项目
                        return True
                    else:
                        logger.error(f"cursor命令执行失败: {result.stderr}")
                        return False
                except subprocess.TimeoutExpired:
                    logger.info(f"cursor命令已启动（超时但可能成功）: {root_path}")
                    time.sleep(5)  # 增加等待时间
                    return True
                except FileNotFoundError:
                    logger.error("cursor命令未找到，请确保Cursor CLI已安装")
                    return False
                    
        except Exception as e:
            logger.error(f"切换项目失败: {e}")
            return False

# 使用示例
def main():
    # 创建自动化实例
    automator = CursorAutomation()
    
    # 示例文本（可以从你的App接口获取）
    sample_text = "请帮我分析这段代码的优化方案：\n\nfunction calculate(data) {\n  let result = 0;\n  for (let i = 0; i < data.length; i++) {\n    result += data[i];\n  }\n  return result;\n}"
    
    # 发送到Cursor
    success = automator.send_to_cursor(sample_text)
    
    if success:
        print("✅ 消息成功发送到Cursor！")
    else:
        print("❌ 发送失败，请检查Cursor是否安装并运行")

# 如果从其他模块调用
def receive_from_app(text: str, skip_activation: bool = False):
    """从你的App调用这个函数
    
    Args:
        text: 要发送的文本
        skip_activation: 是否跳过激活步骤（当刚切换项目后使用）
    """
    automator = CursorAutomation()
    return automator.send_to_cursor(text, skip_activation=skip_activation)

def switch_cursor_project(root_path: str):
    """切换Cursor到指定项目目录"""
    automator = CursorAutomation()
    return automator.switch_cursor_project(root_path)

if __name__ == "__main__":
    main()