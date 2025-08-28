import pyautogui
from pyautogui import ImageNotFoundException
import time
import subprocess
import platform
import logging
import os
from typing import Optional

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CursorAutomation:
    def __init__(self):
        self.system = platform.system()
        self.modifier = 'command' if self.system == 'Darwin' else 'ctrl'
        self.alt_modifier = 'option' if self.system == 'Darwin' else 'alt'
        
        # 图像文件路径
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.dialogue_image = os.path.join(self.base_dir, 'cursor_dialogue.png')
        self.empty_image = os.path.join(self.base_dir, 'cursor_empty.png')
        
        # 设置pyautogui的置信度
        pyautogui.FAILSAFE = True
        
    def detect_dialog_state(self) -> str:
        """检测当前对话框状态
        
        Returns:
            str: 'dialogue' - 检测到对话框, 'empty' - 检测到空白界面, 'unknown' - 未检测到已知状态
        """
        try:
            logger.info("开始图像检测...")
            
            # 检测是否有对话框
            if os.path.exists(self.dialogue_image):
                logger.info(f"正在检测对话框图像: {self.dialogue_image}")
                try:
                    dialogue_location = pyautogui.locateOnScreen(self.dialogue_image, confidence=0.8)
                    logger.info(f"图像检测：检测到对话框已打开，位置: {dialogue_location}")
                    return 'dialogue'
                except ImageNotFoundException:
                    logger.info("图像检测：未检测到对话框")
                except Exception as e:
                    logger.warning(f"对话框图像检测异常: {e}")
            else:
                logger.warning(f"对话框图像文件不存在: {self.dialogue_image}")
            
            # 检测是否是空白界面
            if os.path.exists(self.empty_image):
                logger.info(f"正在检测空白界面图像: {self.empty_image}")
                try:
                    empty_location = pyautogui.locateOnScreen(self.empty_image, confidence=0.8)
                    logger.info(f"图像检测：检测到空白界面，位置: {empty_location}")
                    return 'empty'
                except ImageNotFoundException:
                    logger.info("图像检测：未检测到空白界面")
                except Exception as e:
                    logger.warning(f"空白界面图像检测异常: {e}")
            else:
                logger.warning(f"空白界面图像文件不存在: {self.empty_image}")
            
            logger.info("图像检测：未检测到已知状态")
            return 'unknown'
            
        except Exception as e:
            logger.error(f"图像检测失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return 'unknown'
    
    def wait_for_dialog_state(self, expected_state: str, timeout: int = 10) -> bool:
        """等待特定的对话框状态
        
        Args:
            expected_state: 期望的状态 ('dialogue', 'empty')
            timeout: 超时时间（秒）
            
        Returns:
            bool: 是否检测到期望状态
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_state = self.detect_dialog_state()
            if current_state == expected_state:
                logger.info(f"成功检测到期望状态: {expected_state}")
                return True
            time.sleep(0.5)
        
        logger.warning(f"等待状态 {expected_state} 超时")
        return False
        
    def open_cursor(self) -> bool:
        """打开Cursor应用"""
        try:
            if self.system == 'Darwin':
                # Mac: 使用open命令打开Cursor
                subprocess.run(['open', '-a', 'Cursor'])
            elif self.system == 'Windows':
                # Windows: 尝试通过开始菜单或直接路径打开
                try:
                    # This is the most reliable way if the protocol is registered
                    subprocess.run(['start', 'cursor:'], shell=True, check=True)
                except (subprocess.CalledProcessError, FileNotFoundError):
                    logger.warning("Could not open Cursor via protocol, trying common paths.")
                    # Fallback to common installation paths
                    possible_paths = [
                        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Cursor", "Cursor.exe"),
                        os.path.join(os.environ.get("ProgramFiles", ""), "Cursor", "Cursor.exe"),
                    ]
                    for path in possible_paths:
                        if os.path.exists(path):
                            subprocess.run([path])
                            logger.info(f"Found and opened Cursor at: {path}")
                            break
                    else:
                        logger.error("Could not find Cursor.exe in common locations.")
                        return False
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
                # Windows/Linux: 尝试使用pygetwindow激活
                try:
                    import pygetwindow as gw
                    # 查找标题中含有"Cursor"的窗口
                    cursor_windows = []
                    
                    # 使用动态属性检查来避免linter错误
                    get_windows_func = getattr(gw, 'getWindowsWithTitle', None)
                    get_all_windows_func = getattr(gw, 'getAllWindows', None)
                    
                    if get_windows_func:
                        try:
                            cursor_windows = get_windows_func('Cursor')
                        except Exception:
                            cursor_windows = []
                    elif get_all_windows_func:
                        try:
                            all_windows = get_all_windows_func()
                            cursor_windows = [w for w in all_windows if 'Cursor' in str(getattr(w, 'title', ''))]
                        except Exception:
                            cursor_windows = []
                    
                    if cursor_windows:
                        # 激活第一个找到的窗口
                        window = cursor_windows[0]
                        try:
                            is_active = getattr(window, 'isActive', None)
                            activate_func = getattr(window, 'activate', None)
                            
                            if is_active is not None and not is_active:
                                if activate_func:
                                    activate_func()
                            elif activate_func:
                                activate_func()
                            
                            logger.info("已激活Cursor窗口")
                            time.sleep(1)
                            return True
                        except Exception as e:
                            logger.warning(f"激活窗口失败: {e}")
                            return False
                    else:
                        logger.warning("未找到Cursor窗口，尝试打开")
                        return self.open_cursor()
                except ImportError:
                    logger.error("pygetwindow模块未安装，请运行 'pip install pygetwindow'")
                    return self.open_cursor() # Fallback to opening
                except Exception as e:
                    logger.error(f"使用pygetwindow激活失败: {e}")
                    return self.open_cursor() # Fallback to opening
                
        except Exception as e:
            logger.error(f"激活Cursor窗口失败: {e}")
            return False
    
    def open_chat_dialog(self, skip_activation: bool = False) -> bool:
        """调出聊天对话框（Command/Ctrl + I）
        
        Args:
            skip_activation: 是否跳过激活步骤
        """
        try:
            # 检测当前对话框状态
            current_state = self.detect_dialog_state()
            if current_state == 'dialogue':
                logger.info("对话框已经打开，无需重复打开")
                return True
            
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
            
            # 等待对话框打开并验证
            if self.wait_for_dialog_state('dialogue', timeout=5):
                logger.info("对话框成功打开")
                return True
            else:
                logger.warning("对话框可能未成功打开")
                return False
            
        except Exception as e:
            logger.error(f"打开聊天对话框失败: {e}")
            return False
    
    def open_ai_sidebar(self, skip_activation: bool = False) -> bool:
        """打开AI侧边栏（已移除Command+Shift+A，因为它是截图快捷键）
        
        Args:
            skip_activation: 是否跳过激活步骤
        """
        try:
            # 确保Cursor是活动窗口（如果不跳过激活）
            if not skip_activation:
                self.activate_cursor()
                time.sleep(1)  # 等待窗口激活
            else:
                logger.info("跳过侧边栏激活步骤")
                time.sleep(0.5)  # 短暂等待
            
            # 移除Command+Shift+A快捷键，因为它是截图快捷键
            logger.warning("已移除Command+Shift+A快捷键，因为它是截图快捷键")
            logger.info("AI侧边栏功能暂时不可用")
            
            # 等待一下
            time.sleep(2)
            logger.info("AI侧边栏功能已禁用")
            return False
            
        except Exception as e:
            logger.error(f"打开AI侧边栏失败: {e}")
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
            
            # 检测对话框状态
            current_state = self.detect_dialog_state()
            if current_state != 'dialogue':
                logger.warning(f"当前状态不是对话框状态: {current_state}，尝试重新打开对话框")
                if not self.open_chat_dialog():
                    logger.error("无法打开对话框，输入文本失败")
                    return False
            
            # 等待对话框稳定
            time.sleep(1)
            
            # 尝试多种输入方法
            success = False
            
            # 方法1: 使用剪贴板（最可靠）
            try:
                import pyperclip
                pyperclip.copy(text)
                pyautogui.hotkey(self.modifier, 'v')
                logger.info(f"已通过剪贴板输入文本: {text[:50]}...")
                success = True
            except ImportError:
                logger.warning("pyperclip模块未安装，请运行 'pip install pyperclip'")
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
        logger.info("=== 开始消息发送流程 ===")
        logger.info(f"目标消息: {text[:50]}{'...' if len(text) > 50 else ''}")
        logger.info(f"最大重试次数: {max_retries}")
        logger.info(f"跳过激活: {skip_activation}")
        
        for attempt in range(max_retries):
            try:
                logger.info(f"\n--- 第 {attempt + 1} 次发送尝试 ---")
                
                # 步骤1: 检测初始页面状态
                logger.info("步骤1: 检测当前页面状态")
                initial_state = self.detect_dialog_state()
                logger.info(f"初始页面状态: {initial_state}")
                
                # 步骤2: 激活或打开Cursor（如果不跳过激活）
                logger.info("步骤2: 处理Cursor窗口激活")
                if not skip_activation:
                    logger.info("执行操作: 激活Cursor窗口")
                    activation_result = self.activate_cursor()
                    logger.info(f"激活结果: {'成功' if activation_result else '失败'}")
                    if not activation_result:
                        logger.warning("激活失败，跳过此次尝试")
                        continue
                else:
                    logger.info("执行操作: 跳过激活步骤，使用当前Cursor窗口")
                    time.sleep(2)  # 等待Cursor稳定
                    logger.info("等待2秒让Cursor窗口稳定")
                
                # 步骤3: 打开聊天对话框
                logger.info("步骤3: 打开聊天对话框")
                pre_dialog_state = self.detect_dialog_state()
                logger.info(f"打开对话框前的状态: {pre_dialog_state}")
                
                logger.info("执行操作: 调用open_chat_dialog方法")
                dialog_result = self.open_chat_dialog(skip_activation=skip_activation)
                logger.info(f"对话框打开结果: {'成功' if dialog_result else '失败'}")
                
                if dialog_result:
                    post_dialog_state = self.detect_dialog_state()
                    logger.info(f"打开对话框后的状态: {post_dialog_state}")
                else:
                    logger.warning("对话框打开失败，跳过此次尝试")
                    continue
                
                # 步骤4: 输入文本
                logger.info("步骤4: 输入文本内容")
                pre_input_state = self.detect_dialog_state()
                logger.info(f"输入文本前的状态: {pre_input_state}")
                
                logger.info(f"执行操作: 输入文本内容 (长度: {len(text)} 字符)")
                input_result = self.input_text(text)
                logger.info(f"文本输入结果: {'成功' if input_result else '失败'}")
                
                if not input_result:
                    logger.warning("文本输入失败，跳过此次尝试")
                    continue
                
                # 步骤5: 提交消息
                logger.info("步骤5: 提交消息")
                logger.info("执行操作: 调用submit_message方法")
                submit_result = self.submit_message()
                logger.info(f"消息提交结果: {'成功' if submit_result else '失败'}")
                
                if not submit_result:
                    logger.warning("消息提交失败，跳过此次尝试")
                    continue
                
                # 步骤6: 验证最终状态
                logger.info("步骤6: 验证发送完成状态")
                final_state = self.detect_dialog_state()
                logger.info(f"最终页面状态: {final_state}")
                
                logger.info("=== 消息发送成功！===")
                return True
                
            except Exception as e:
                logger.error(f"第 {attempt + 1} 次尝试发生异常: {e}")
                import traceback
                logger.error(f"异常详情: {traceback.format_exc()}")
                time.sleep(2)  # 失败后等待一会儿再重试
                logger.info(f"等待2秒后进行下一次尝试")
        
        logger.error(f"=== 所有 {max_retries} 次尝试都失败 ===")
        return False
    
    def _find_cursor_cmd_on_windows(self) -> Optional[str]:
        """Find the path to the cursor.cmd on Windows."""
        # Common installation directories for Cursor
        base_paths = [
            os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "Cursor"),
            os.path.join(os.environ.get("ProgramFiles", ""), "Cursor"),
        ]
        for base in base_paths:
            # The CLI script is typically in resources/app/bin
            cli_path = os.path.join(base, "resources", "app", "bin", "cursor.cmd")
            if os.path.exists(cli_path):
                logger.info(f"Found Cursor CLI at: {cli_path}")
                return cli_path
        return None

    def switch_cursor_project(self, root_path: str) -> bool:
        """切换Cursor到指定项目目录"""
        try:
            logger.info("=== 开始切换Cursor项目 ===")
            logger.info(f"目标项目路径: {root_path}")
            logger.info(f"当前操作系统: {self.system}")
            
            if not os.path.exists(root_path):
                logger.warning(f"目标路径不存在: {root_path}")
                # Still try to proceed, as Cursor might handle it
            
            if self.system == 'Darwin':
                logger.info("执行方式: macOS Terminal + AppleScript")
                script = f'''
                tell application "Terminal"
                    activate
                    do script "cursor '{root_path}'"
                end tell
                '''
                result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info(f"✓ 成功在Terminal中执行: cursor '{root_path}'")
                    time.sleep(5)
                    return True
                else:
                    logger.error(f"✗ Terminal脚本执行失败: {result.stderr}")
                    return False
            else:
                # Windows/Linux
                command = ['cursor', root_path]
                try:
                    # First, try with 'cursor' directly (from PATH)
                    result = subprocess.run(command, capture_output=True, text=True, timeout=15, shell=False)
                    if result.returncode != 0:
                        raise FileNotFoundError # Treat non-zero exit as "not found" to trigger fallback
                except (FileNotFoundError, subprocess.TimeoutExpired) as e:
                    if isinstance(e, subprocess.TimeoutExpired):
                         logger.warning("`cursor` command timed out. Assuming it worked.")
                         time.sleep(5)
                         return True

                    logger.warning(f"`cursor` command failed or not in PATH. Searching common locations...")
                    if self.system == 'Windows':
                        cursor_cmd = self._find_cursor_cmd_on_windows()
                        if not cursor_cmd:
                            logger.error("✗ cursor.cmd not found. Please add Cursor's bin directory to your PATH.")
                            return False
                        command = [cursor_cmd, root_path]
                        # Retry with the full path
                        try:
                            subprocess.run(command, timeout=15, shell=True) # shell=True for .cmd
                            logger.info(f"✓ 成功执行: {' '.join(command)}")
                            time.sleep(5)
                            return True
                        except Exception as final_e:
                            logger.error(f"✗ 执行cursor.cmd失败: {final_e}")
                            return False
                    else: # Linux
                        logger.error("✗ 'cursor' command not found. Please add it to your PATH.")
                        return False

                logger.info(f"✓ 成功执行: {' '.join(command)}")
                time.sleep(5)
                return True
                    
        except Exception as e:
            logger.error(f"=== 切换项目发生异常: {e} ===")
            import traceback
            logger.error(f"异常详情: {traceback.format_exc()}")
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
def receive_from_app(text: str, skip_activation: bool = False, workspace_id: str = None, force_restart: bool = False, create_new_chat: bool = False):
    """从你的App调用这个函数
    
    Args:
        text: 要发送的文本
        skip_activation: 是否跳过激活步骤（当刚切换项目后使用）
        workspace_id: 工作空间ID（用于日志记录）
        force_restart: 是否强制重启Cursor
        create_new_chat: 是否创建新对话
    """
    automator = CursorAutomation()
    
    # 如果需要创建新对话，执行重启和打开对话框，然后查找最新的对话ID
    if create_new_chat:
        logger.info("创建新对话：重启Cursor并打开对话框")
        # 记录创建新对话的时间
        import time
        creation_time = time.time()
        
        # 执行重启和打开对话框的操作
        result = automator.send_to_cursor("", skip_activation=skip_activation)
        if result:
            logger.info("新对话准备完成，开始查找最新对话ID")
            
            # 等待一下让Cursor有时间创建对话记录
            time.sleep(3)
            
            # 尝试查找最新的对话ID
            try:
                # 导入server.py中的extract_chats函数
                import sys
                import os
                current_dir = os.path.dirname(os.path.abspath(__file__))
                if current_dir not in sys.path:
                    sys.path.insert(0, current_dir)
                
                # 动态导入server模块中的extract_chats函数
                import server
                chats = server.extract_chats()
                
                # 查找在创建时间之后的最新对话
                latest_chat = None
                latest_time = 0
                
                for chat in chats:
                    chat_time = chat.get('date', 0)
                    if chat_time > creation_time - 10:  # 允许10秒的时间差
                        if chat_time > latest_time:
                            latest_time = chat_time
                            latest_chat = chat
                
                if latest_chat and 'session' in latest_chat and latest_chat['session']:
                    session_id = latest_chat['session'].get('composerId')
                    if session_id:
                        logger.info(f"找到最新创建的对话ID: {session_id}")
                        return True, session_id
                
                logger.warning("未找到最新创建的对话ID")
                return True, None
                
            except Exception as e:
                logger.error(f"查找最新对话ID时出错: {e}")
                return True, None
        else:
            logger.error("新对话准备失败")
            return False, None
    
    # 正常发送消息流程
    result = automator.send_to_cursor(text, skip_activation=skip_activation)
    return result, None

def switch_cursor_project(root_path: str):
    """切换Cursor到指定项目目录"""
    automator = CursorAutomation()
    return automator.switch_cursor_project(root_path)

def open_ai_sidebar(skip_activation: bool = False):
    """打开AI侧边栏
    
    Args:
        skip_activation: 是否跳过激活步骤
    """
    automator = CursorAutomation()
    return automator.open_ai_sidebar(skip_activation=skip_activation)

if __name__ == "__main__":
    main()