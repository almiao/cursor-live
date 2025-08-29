import pyautogui
# 移除 ImageNotFoundException 导入，因为已改为数据库检测
import time
import subprocess
import platform
import logging
import os
from typing import Optional, Dict, Any

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import AppKit

    NSWorkspace = AppKit.NSWorkspace  # type: ignore

    import ApplicationServices

    AXUIElementCreateApplication = getattr(ApplicationServices, 'AXUIElementCreateApplication', None)
    kAXWindowsAttribute = getattr(ApplicationServices, 'kAXWindowsAttribute', "AXWindows")
    kAXTitleAttribute = getattr(ApplicationServices, 'kAXTitleAttribute', "AXTitle")
    kAXRoleAttribute = getattr(ApplicationServices, 'kAXRoleAttribute', "AXRole")
    kAXSubroleAttribute = getattr(ApplicationServices, 'kAXSubroleAttribute', "AXSubrole")
    kAXChildrenAttribute = getattr(ApplicationServices, 'kAXChildrenAttribute', "AXChildren")
    kAXValueAttribute = getattr(ApplicationServices, 'kAXValueAttribute', "AXValue")
    AXUIElementCopyAttributeValue = getattr(ApplicationServices, 'AXUIElementCopyAttributeValue', None)
    kAXErrorSuccess = getattr(ApplicationServices, 'kAXErrorSuccess', 0)
    AXIsProcessTrusted = getattr(ApplicationServices, 'AXIsProcessTrusted', None)

    MAC_OS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"macOS框架不可用: {e}")
    MAC_OS_AVAILABLE = False
    # 使用占位符函数
    NSWorkspace = type('NSWorkspace', (), {'sharedWorkspace': lambda: None})  # type: ignore
    AXUIElementCreateApplication = lambda x: None  # type: ignore
    AXUIElementCopyAttributeValue = lambda x, y, z: (1, None)  # type: ignore
    AXIsProcessTrusted = lambda: False  # type: ignore

# 向后兼容
MACOS_AVAILABLE = MAC_OS_AVAILABLE

class CursorAutomation:
    def __init__(self):
        self.system = platform.system()
        self.modifier = 'command' if self.system == 'Darwin' else 'ctrl'
        self.alt_modifier = 'option' if self.system == 'Darwin' else 'alt'
        
        # 移除图像文件路径定义，因为已改为数据库检测
        
        # 设置pyautogui的置信度
        pyautogui.FAILSAFE = True

    def is_cursor_frontmost(self) -> Dict[str, Any]:
        """
        检查Cursor是否为前台应用

        Returns:
            Dict[str, Any]: 检查结果
        """
        if not MACOS_AVAILABLE:
            return {
                'is_front': False,
                'error': 'macOS frameworks not available',
                'status': 'error'
            }

        try:
            logger.info("检查Cursor是否为前台应用...")

            ws = NSWorkspace.sharedWorkspace()  # type: ignore
            if not ws:
                logger.error("无法获取NSWorkspace实例")
                return {
                    'is_front': False,
                    'error': 'Cannot get NSWorkspace instance',
                    'status': 'error'
                }

            frontmost_app = ws.frontmostApplication()  # type: ignore

            if frontmost_app:
                app_name = frontmost_app.localizedName()
                bundle_id = frontmost_app.bundleIdentifier()

                logger.info(f"前台应用: {app_name} (Bundle ID: {bundle_id})")

                is_cursor_front = (
                        (app_name and "Cursor" in app_name) or
                        (bundle_id and "cursor" in bundle_id.lower())
                )

                return {
                    'is_front': is_cursor_front,
                    'front_app': app_name,
                    'bundle_id': bundle_id,
                    'status': 'success'
                }
            else:
                logger.warning("无法获取前台应用信息")
                return {
                    'is_front': False,
                    'error': 'Cannot get frontmost application',
                    'status': 'error'
                }

        except Exception as e:
            logger.error(f"检查前台应用时发生异常: {e}")
            return {
                'is_front': False,
                'error': str(e),
                'status': 'error'
            }
        
    def detect_dialog_state(self, workspace_id: str = None) -> str:
        """检测当前对话框状态（基于workbench.auxiliaryBar.hidden）
        
        Args:
            workspace_id: 工作空间ID（必需，用于检查特定工作空间的侧边栏状态）
            
        Returns:
            str: 'dialogue' - 检测到对话框, 'empty' - 检测到空白界面, 'unknown' - 未检测到已知状态
        """
        try:
            if workspace_id:
                logger.info(f"开始检测对话框状态 (workspace_id: {workspace_id})...")
            else:
                logger.warning("未提供workspace_id，无法检测对话框状态")
                return 'unknown'
            
            # 参考 /api/cursor/status 的实现，使用 workbench.auxiliaryBar.hidden 检查
            try:
                import sys
                import os
                import sqlite3
                import json
                import pathlib
                import platform
                
                current_dir = os.path.dirname(os.path.abspath(__file__))
                if current_dir not in sys.path:
                    sys.path.insert(0, current_dir)
                
                # 获取Cursor根目录
                def cursor_root() -> pathlib.Path:
                    h = pathlib.Path.home()
                    s = platform.system()
                    if s == "Darwin":   return h / "Library" / "Application Support" / "Cursor"
                    if s == "Windows":  return h / "AppData" / "Roaming" / "Cursor"
                    if s == "Linux":    return h / ".config" / "Cursor"
                    raise RuntimeError(f"Unsupported OS: {s}")
                
                # 辅助函数：查询数据库
                def j(cur: sqlite3.Cursor, table: str, key: str):
                    cur.execute(f"SELECT value FROM {table} WHERE key=?", (key,))
                    row = cur.fetchone()
                    if row:
                        try:    return json.loads(row[0])
                        except Exception as e: 
                            logger.debug(f"Failed to parse JSON for {key}: {e}")
                    return None
                
                # 获取Cursor根目录
                base = cursor_root()
                workspace_storage = base / "User" / "workspaceStorage"
                
                # 构建workspace数据库路径
                workspace_db = workspace_storage / workspace_id / "state.vscdb"
                
                if workspace_db.exists():
                    # 连接数据库并查询侧边栏状态
                    con = None
                    try:
                        con = sqlite3.connect(f"file:{workspace_db}?mode=ro", uri=True)
                        cur = con.cursor()
                        
                        # 查询workbench.auxiliaryBar.hidden的值
                        auxiliary_bar_hidden = j(cur, "ItemTable", "workbench.auxiliaryBar.hidden")
                        
                        # 如果值为None，默认认为侧边栏是隐藏的
                        is_hidden = auxiliary_bar_hidden if auxiliary_bar_hidden is not None else True
                        
                        if not is_hidden:
                            logger.info("检测到AI侧边栏已打开")
                            return 'dialogue'
                        else:
                            logger.info("检测到AI侧边栏已隐藏")
                            return 'empty'
                        
                    except Exception as db_error:
                        logger.warning(f"数据库查询失败: {db_error}")
                        return 'unknown'
                    finally:
                        if con:
                            con.close()
                else:
                    logger.warning(f"Workspace数据库不存在: {workspace_id}")
                    return 'unknown'
                    
            except Exception as e:
                logger.error(f"检测对话框状态时出错: {e}")
                return 'unknown'
            
        except Exception as e:
            logger.error(f"对话框状态检测失败: {e}")
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
    
    def open_chat_dialog(self, skip_activation: bool = False, new_chat: bool = False) -> bool:
        """调出聊天对话框或新对话
        
        Args:
            skip_activation: 是否跳过激活步骤
            new_chat: 是否在已打开的对话框中创建新对话（True使用Command+T，False使用Command+I）
        """
        try:
            # 确保Cursor是活动窗口（如果不跳过激活）
            if not skip_activation:
                self.activate_cursor()
                time.sleep(1)  # 等待窗口激活
            else:
                logger.info("跳过对话框激活步骤")
                time.sleep(0.5)  # 短暂等待
            
            if new_chat:
                # 如果要创建新对话，先检查对话框是否已打开
                current_state = self.detect_dialog_state()
                if current_state != 'dialogue':
                    logger.warning("对话框未打开，无法创建新对话，先打开对话框")
                    # 先打开对话框
                    pyautogui.hotkey(self.modifier, 'i')
                    logger.info("已发送快捷键 Command+I 打开聊天对话框")
                    time.sleep(2)  # 等待对话框打开
                
                # 发送快捷键：Command/Ctrl + T（在对话框中创建新对话）
                pyautogui.hotkey(self.modifier, 't')
                logger.info("已发送快捷键 Command+T 在对话框中创建新对话")
            else:
                # 检测当前对话框状态
                current_state = self.detect_dialog_state()
                if current_state == 'dialogue':
                    logger.info("对话框已经打开，无需重复打开")
                    return True
                
                # 发送快捷键：Command/Ctrl + I（打开聊天对话框）
                pyautogui.hotkey(self.modifier, 'i')
                logger.info("已发送快捷键 Command+I 打开聊天对话框")
            
            # 等待对话框打开并验证
            if self.wait_for_dialog_state('dialogue', timeout=5):
                logger.info("对话框操作成功")
                return True
            else:
                logger.warning("对话框操作可能未成功")
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
                if not self.open_chat_dialog(new_chat=False):
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
    
    def send_to_cursor(self, text: str, max_retries: int = 3, skip_activation: bool = False, new_chat: bool = False) -> bool:
        """完整的发送流程
        
        Args:
            text: 要发送的文本
            max_retries: 最大重试次数
            skip_activation: 是否跳过激活步骤（当刚切换项目后使用）
            new_chat: 是否打开新对话（True使用Command+T，False使用Command+I）
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
                dialog_result = self.open_chat_dialog(skip_activation=skip_activation, new_chat=new_chat)
                logger.info(f"对话框打开结果: {'成功' if dialog_result else '失败'}")
                
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
        result = automator.send_to_cursor("", skip_activation=skip_activation, new_chat=True)
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

