import pyautogui
from pyautogui import ImageNotFoundException
import time
import subprocess
import platform
import logging
import os
import sqlite3
import json
import pathlib
from typing import Optional

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CursorAutomation:
    def __init__(self):
        self.system = platform.system()
        self.modifier = 'command' if self.system == 'Darwin' else 'ctrl'
        self.alt_modifier = 'option' if self.system == 'Darwin' else 'alt'
        
        # 设置pyautogui的置信度
        pyautogui.FAILSAFE = True
        
    def cursor_root(self) -> pathlib.Path:
        """获取Cursor根目录路径"""
        h = pathlib.Path.home()
        s = platform.system()
        if s == "Darwin":   return h / "Library" / "Application Support" / "Cursor"
        if s == "Windows":  return h / "AppData" / "Roaming" / "Cursor"
        if s == "Linux":    return h / ".config" / "CursorA j"
        raise RuntimeError(f"Unsupported OS: {s}")
    
    def j(self, cur: sqlite3.Cursor, table: str, key: str):
        """查询数据库中的JSON配置值"""
        cur.execute(f"SELECT value FROM {table} WHERE key=?", (key,))
        row = cur.fetchone()
        if row:
            try:
                return json.loads(row[0])
            except Exception as e:
                logger.debug(f"Failed to parse JSON for {key}: {e}")
        return None
    
    def get_workspace_id(self) -> Optional[str]:
        """获取当前工作区的ID"""
        try:
            # 获取Cursor根目录
            base = self.cursor_root()
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

    def get_latest_session_id(self, workspace_id: str = None) -> Optional[str]:
        """获取最新的session_id（composerId）
        
        Args:
            workspace_id: 目标workspace ID，如果为None则使用最新的
            
        Returns:
            Optional[str]: 最新的session_id，如果未找到返回None
        """
        try:
            logger.info("=== 开始获取最新session_id ===")
            
            # 如果没有指定workspace_id，获取最新的
            if not workspace_id:
                workspace_id = self.get_workspace_id()
                if not workspace_id:
                    logger.error("无法获取workspace_id")
                    return None
            
            logger.info(f"目标workspace_id: {workspace_id}")
            
            # 获取Cursor根目录
            base = self.cursor_root()
            workspace_db_path = base / "User" / "workspaceStorage" / workspace_id / "state.vscdb"
            
            if not workspace_db_path.exists():
                logger.error(f"Workspace数据库不存在: {workspace_db_path}")
                return None
            
            # 连接数据库
            con = sqlite3.connect(f"file:{workspace_db_path}?mode=ro", uri=True)
            cur = con.cursor()
            
            # 获取最新的composer数据
            composer_data = self.j(cur, "ItemTable", "composer.composerData")
            if composer_data and "allComposers" in composer_data:
                composers = composer_data["allComposers"]
                if composers:
                    # 按lastUpdatedAt排序，获取最新的
                    latest_composer = max(composers, key=lambda x: x.get("lastUpdatedAt", 0))
                    session_id = latest_composer.get("composerId")
                    logger.info(f"找到最新session_id: {session_id}")
                    con.close()
                    return session_id
            
            # 如果没有找到composer数据，尝试从chat data获取
            chat_data = self.j(cur, "ItemTable", "workbench.panel.aichat.view.aichat.chatdata")
            if chat_data and "tabs" in chat_data:
                tabs = chat_data["tabs"]
                if tabs:
                    # 获取最新的tab
                    latest_tab = max(tabs, key=lambda x: x.get("lastUpdatedAt", 0))
                    session_id = latest_tab.get("tabId")
                    logger.info(f"从chat data找到最新session_id: {session_id}")
                    con.close()
                    return session_id
            
            con.close()
            logger.warning("未找到任何session_id")
            return None
            
        except Exception as e:
            logger.error(f"获取最新session_id失败: {e}")
            return None
    
    def detect_dialog_state(self, workspace_id: str = None) -> str:
        try:
            logger.info("开始基于数据库的对话框状态检测...")
            
            # 如果没有传入workspace_id，则获取最新的
            if not workspace_id:
                workspace_id = self.get_workspace_id()
                logger.info(f"使用默认workspace ID: {workspace_id}")
            
            if not workspace_id:
                logger.warning("无法获取workspace ID，使用默认状态")
                return 'unknown'
            
            # 获取Cursor根目录∫
            base = self.cursor_root()
            workspace_storage = base / "User" / "workspaceStorage"
            workspace_db = workspace_storage / workspace_id / "state.vscdb"
            
            if not workspace_db.exists():
                logger.warning(f"Workspace数据库不存在: {workspace_db}")
                return 'unknown'
            
            # 连接数据库并查询侧边栏状态
            con = None
            try:
                con = sqlite3.connect(f"file:{workspace_db}?mode=ro", uri=True)
                cur = con.cursor()
                
                # 查询workbench.auxiliaryBar.hidden的值
                auxiliary_bar_hidden = self.j(cur, "ItemTable", "workbench.auxiliaryBar.hidden")
                
                # 如果值为None，默认认为侧边栏是隐藏的
                is_hidden = auxiliary_bar_hidden if auxiliary_bar_hidden is not None else True
                
                if is_hidden:
                    logger.info("数据库检测：辅助栏是隐藏的，返回 'empty'")
                    return 'empty'
                else:
                    logger.info("数据库检测：辅助栏是显示的，返回 'dialogue'")
                    return 'dialogue'
                    
            except Exception as db_error:
                logger.error(f"数据库查询失败: {db_error}")
                return 'unknown'
            finally:
                if con:
                    con.close()
                    
        except Exception as e:
            logger.error(f"对话框状态检测失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return 'unknown'
    
    def wait_for_dialog_state(self, expected_state: str, timeout: int = 20, workspace_id: str = None) -> bool:
        """等待特定的对话框状态
        
        Args:
            expected_state: 期望的状态 ('dialogue', 'empty')
            timeout: 超时时间（秒）
            workspace_id: 目标workspace ID，如果为None则使用最新的
            
        Returns:
            bool: 是否检测到期望状态
        """
        start_time = time.time()
        while time.time() - start_time < timeout:
            current_state = self.detect_dialog_state(workspace_id)
            if current_state == expected_state:
                logger.info(f"成功检测到期望状态: {expected_state}")
                return True
            time.sleep(0.5)
        
        logger.warning(f"等待状态 {expected_state} 超时")
        return False
        
    def close_cursor(self) -> bool:
        """关闭Cursor应用"""
        try:
            logger.info("=== 开始关闭Cursor应用 ===")
            
            if self.system == 'Darwin':
                # macOS: 使用AppleScript关闭Cursor
                script = '''
                tell application "Cursor"
                    quit
                end tell
                '''
                result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info("✓ 成功关闭Cursor应用")
                    time.sleep(3)  # 等待应用完全关闭
                    return True
                else:
                    logger.error(f"✗ 关闭Cursor失败: {result.stderr}")
                    return False
            else:
                # Windows/Linux: 使用进程管理关闭
                try:
                    import psutil
                    for proc in psutil.process_iter(['pid', 'name']):
                        try:
                            if 'cursor' in proc.info['name'].lower():
                                proc.terminate()
                                logger.info(f"✓ 已终止Cursor进程 (PID: {proc.info['pid']})")
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            continue
                    
                    time.sleep(3)  # 等待进程完全关闭
                    return True
                except ImportError:
                    logger.warning("psutil模块未安装，无法优雅关闭Cursor")
                    return True  # 假设关闭成功
                except Exception as e:
                    logger.error(f"关闭Cursor进程失败: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"关闭Cursor应用失败: {e}")
            return False

    def open_cursor(self) -> bool:
        """打开Cursor应用"""
        try:
            logger.info("=== 开始打开Cursor应用 ===")
            
            if self.system == 'Darwin':
                # macOS: 使用AppleScript打开Cursor
                script = '''
                tell application "Cursor"
                    activate
                end tell
                '''
                result = subprocess.run(['osascript', '-e', script], capture_output=True, text=True)
                if result.returncode == 0:
                    logger.info("✓ 成功打开Cursor应用")
                    time.sleep(5)  # 等待应用完全启动
                    return True
                else:
                    logger.error(f"✗ 打开Cursor失败: {result.stderr}")
                    return False
            else:
                # Windows/Linux: 使用subprocess打开
                try:
                    subprocess.Popen(['cursor'], shell=True)
                    logger.info("✓ 成功启动Cursor应用")
                    time.sleep(5)  # 等待应用完全启动
                    return True
                except Exception as e:
                    logger.error(f"启动Cursor失败: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"打开Cursor应用失败: {e}")
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
    
    def open_chat_dialog(self, skip_activation: bool = False, workspace_id: str = None) -> bool:
        """调出聊天对话框（Mac: Option+Command+B, Windows/Linux: Ctrl+I）
        
        Args:
            skip_activation: 是否跳过激活步骤
            workspace_id: 目标workspace ID，如果为None则使用最新的
        """
        try:
            # 检测当前对话框状态
            current_state = self.detect_dialog_state(workspace_id)
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
            
            # 清除可能的输入缓冲区
            logger.info("清除输入缓冲区")
            pyautogui.press('escape')  # 按ESC清除可能的输入状态
            time.sleep(0.5)
            
            # 根据系统发送不同的快捷键
            if self.system == 'Darwin':
                # Mac: Option+Command+B
                pyautogui.hotkey('option', 'command', 'b')
                logger.info("已发送快捷键 Option+Command+B 打开聊天对话框")
            else:
                # Windows/Linux: Ctrl+I
                pyautogui.hotkey(self.modifier, 'i')
                logger.info("已发送快捷键 Ctrl+I 打开聊天对话框")
            
            # 等待对话框打开并验证
            if self.wait_for_dialog_state('dialogue', timeout=5, workspace_id=workspace_id):
                logger.info("对话框成功打开")
                # 再次清除可能的输入
                time.sleep(0.5)
                pyautogui.press('escape')
                time.sleep(0.5)
                return True
            else:
                logger.warning("对话框可能未成功打开")
                return False
            
        except Exception as e:
            logger.error(f"打开聊天对话框失败: {e}")
            return False

    def create_new_chat(self, skip_activation: bool = False, workspace_id: str = None) -> bool:
        """创建新对话（Command+T）
        
        Args:
            skip_activation: 是否跳过激活步骤
            workspace_id: 目标workspace ID，如果为None则使用最新的
        """
        try:
            logger.info("=== 开始创建新对话 ===")
            
            # 确保Cursor是活动窗口（如果不跳过激活）
            if not skip_activation:
                self.activate_cursor()
                time.sleep(1)  # 等待窗口激活
            else:
                logger.info("跳过激活步骤")
                time.sleep(0.5)  # 短暂等待
            
            # 清除可能的输入缓冲区
            logger.info("清除输入缓冲区")
            pyautogui.press('escape')  # 按ESC清除可能的输入状态
            time.sleep(0.5)
            
            # 发送Command+T创建新对话
            pyautogui.hotkey(self.modifier, 't')
            logger.info(f"已发送快捷键 {self.modifier.upper()}+T 创建新对话")
            
            # 等待新对话创建完成
            time.sleep(2)
            
            # 再次清除可能的输入
            logger.info("清除新对话创建后的输入")
            pyautogui.press('escape')
            time.sleep(0.5)
            
            logger.info("新对话创建完成")
            return True
            
        except Exception as e:
            logger.error(f"创建新对话失败: {e}")
            return False
    
    def open_ai_sidebar(self, skip_activation: bool = False) -> bool:
        """打开AI侧边栏（Command/Ctrl + Shift + A）
        
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
            
            # 发送快捷键：Command/Ctrl + Shift + A
            pyautogui.hotkey(self.modifier, 'shift', 'a')
            logger.info("已发送快捷键 Command+Shift+A 打开AI侧边栏")
            
            # 等待侧边栏打开
            time.sleep(2)
            logger.info("AI侧边栏应该已经打开")
            return True
            
        except Exception as e:
            logger.error(f"打开AI侧边栏失败: {e}")
            return False
    
    def input_text(self, text: str, workspace_id: str = None) -> bool:
        """
        在Cursor聊天对话框中输入文本
        
        Args:
            text: 要输入的文本
            workspace_id: 目标workspace ID，如果为None则使用最新的
            
        Returns:
            bool: 输入成功返回True，失败返回False
        """
        try:
            logger.info(f"开始输入文本: {text[:50]}...")
            
            # 检测对话框状态
            current_state = self.detect_dialog_state(workspace_id)
            if current_state != 'dialogue':
                logger.warning(f"当前状态不是对话框状态: {current_state}，尝试重新打开对话框")
                if not self.open_chat_dialog(workspace_id=workspace_id):
                    logger.error("无法打开对话框，输入文本失败")
                    return False
            
            # 等待对话框稳定
            time.sleep(1)
            
            # 清除可能的输入缓冲区
            logger.info("清除输入缓冲区")
            pyautogui.press('escape')  # 按ESC清除可能的输入状态
            time.sleep(0.5)
            
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
    
    def send_to_cursor(self, text: str, max_retries: int = 1, skip_activation: bool = False, workspace_id: str = None, force_restart: bool = False, create_new_chat: bool = False) -> tuple[bool, Optional[str]]:
        """完整的发送流程
        
        Args:
            text: 要发送的文本
            max_retries: 最大重试次数
            skip_activation: 是否跳过激活步骤（当刚切换项目后使用）
            workspace_id: 目标workspace ID，如果为None则使用最新的
            force_restart: 是否强制重启Cursor（首次发送时使用）
            create_new_chat: 是否创建新对话
            
        Returns:
            tuple[bool, Optional[str]]: (是否成功, session_id)
        """
        logger.info("=== 开始消息发送流程 ===")
        logger.info(f"目标消息: {text[:50]}{'...' if len(text) > 50 else ''}")
        logger.info(f"最大重试次数: {max_retries}")
        logger.info(f"跳过激活: {skip_activation}")
        logger.info(f"强制重启: {force_restart}")
        
        # 如果强制重启且没有跳过激活（说明不是刚切换项目），先关闭再打开Cursor
        if force_restart and not skip_activation:
            logger.info("=== 执行强制重启流程 ===")
            logger.info("步骤1: 关闭Cursor应用")
            close_success = self.close_cursor()
            if not close_success:
                logger.warning("关闭Cursor失败，但继续尝试")
            
            logger.info("步骤2: 等待Cursor完全关闭")
            time.sleep(3)
            
            logger.info("步骤3: 重新打开Cursor应用")
            open_success = self.open_cursor()
            if not open_success:
                logger.error("重新打开Cursor失败")
                return False
            
            logger.info("步骤4: 等待Cursor完全启动")
            time.sleep(5)
            logger.info("=== 强制重启完成 ===")
        
        for attempt in range(max_retries):
            try:
                logger.info(f"\n--- 第 {attempt + 1} 次发送尝试 ---")
                # 步骤1: 激活或打开Cursor（如果不跳过激活且没有强制重启）
                logger.info("步骤1: 处理Cursor窗口激活")
                if not skip_activation and not force_restart:
                    logger.info("执行操作: 激活Cursor窗口")
                    activation_result = self.activate_cursor()
                    logger.info(f"激活结果: {'成功' if activation_result else '失败'}")
                    if not activation_result:
                        logger.warning("激活失败，跳过此次尝试")
                        continue
                else:
                    if force_restart:
                        logger.info("执行操作: 跳过激活步骤（已强制重启）")
                    else:
                        logger.info("执行操作: 跳过激活步骤，使用当前Cursor窗口")
                    time.sleep(2)  # 等待Cursor稳定
                    logger.info("等待2秒让Cursor窗口稳定")
                
                # 步骤2: 打开聊天对话框
                logger.info("步骤2: 打开聊天对话框")
                pre_dialog_state = self.detect_dialog_state(workspace_id)
                logger.info(f"打开对话框前的状态: {pre_dialog_state}")
                
                logger.info("执行操作: 调用open_chat_dialog方法")
                dialog_result = self.open_chat_dialog(skip_activation=skip_activation or force_restart, workspace_id=workspace_id)
                logger.info(f"对话框打开结果: {'成功' if dialog_result else '失败'}")
                
                if dialog_result:
                    post_dialog_state = self.detect_dialog_state(workspace_id)
                    logger.info(f"打开对话框后的状态: {post_dialog_state}")
                else:
                    logger.warning("对话框打开失败，跳过此次尝试")
                    continue
                
                # 步骤2.5: 如果需要创建新对话
                if create_new_chat:
                    logger.info("步骤2.5: 创建新对话")
                    new_chat_result = self.create_new_chat(skip_activation=True, workspace_id=workspace_id)
                    logger.info(f"新对话创建结果: {'成功' if new_chat_result else '失败'}")
                    
                    if not new_chat_result:
                        logger.warning("新对话创建失败，跳过此次尝试")
                        continue
                
                # 步骤3: 输入文本
                logger.info("步骤3: 输入文本内容")
                logger.info(f"执行操作: 输入文本内容 (长度: {len(text)} 字符)")
                input_result = self.input_text(text, workspace_id=workspace_id)
                logger.info(f"文本输入结果: {'成功' if input_result else '失败'}")
                
                if not input_result:
                    logger.warning("文本输入失败，跳过此次尝试")
                    continue
                
                # 步骤5: 提交消息
                logger.info("步骤4: 提交消息")
                logger.info("执行操作: 调用submit_message方法")
                submit_result = self.submit_message()
                logger.info(f"消息提交结果: {'成功' if submit_result else '失败'}")
                
                if not submit_result:
                    logger.warning("消息提交失败，跳过此次尝试")
                    continue
                
                # 步骤6: 验证最终状态
                logger.info("步骤5: 验证发送完成状态")
                final_state = self.detect_dialog_state(workspace_id)
                logger.info(f"最终页面状态: {final_state}")
                
                # 步骤7: 如果需要获取session_id
                session_id = None
                if create_new_chat:
                    logger.info("步骤6: 获取新创建的session_id")
                    session_id = self.get_latest_session_id(workspace_id)
                    if session_id:
                        logger.info(f"获取到新session_id: {session_id}")
                    else:
                        logger.warning("无法获取新session_id")
                
                logger.info("=== 消息发送成功！===")
                return True, session_id
                
            except Exception as e:
                logger.error(f"第 {attempt + 1} 次尝试发生异常: {e}")
                import traceback
                logger.error(f"异常详情: {traceback.format_exc()}")
                time.sleep(2)  # 失败后等待一会儿再重试
                logger.info(f"等待2秒后进行下一次尝试")
        
        logger.error(f"=== 所有 {max_retries} 次尝试都失败 ===")
        return False, None
    
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
            
            # 步骤1: 关闭当前Cursor实例
            logger.info("步骤1: 关闭当前Cursor实例")
            close_success = self.close_cursor()
            if not close_success:
                logger.warning("关闭Cursor失败，但继续尝试切换项目")
            
            # 步骤2: 等待一段时间确保完全关闭
            logger.info("步骤2: 等待Cursor完全关闭")
            time.sleep(2)
            
            # 步骤3: 使用命令行打开新项目
            logger.info("步骤3: 打开新项目")
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
                    time.sleep(8)  # 增加等待时间，确保Cursor完全启动
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
                         time.sleep(8)  # 增加等待时间
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
                            time.sleep(8)  # 增加等待时间
                            return True
                        except Exception as final_e:
                            logger.error(f"✗ 执行cursor.cmd失败: {final_e}")
                            return False
                    else: # Linux
                        logger.error("✗ 'cursor' command not found. Please add it to your PATH.")
                        return False

                logger.info(f"✓ 成功执行: {' '.join(command)}")
                time.sleep(8)  # 增加等待时间
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
        workspace_id: 目标workspace ID，如果为None则使用最新的
        force_restart: 是否强制重启Cursor（首次发送时使用）
        create_new_chat: 是否创建新对话
        
    Returns:
        tuple[bool, Optional[str]]: (是否成功, session_id)
    """
    automator = CursorAutomation()
    return automator.send_to_cursor(text, skip_activation=skip_activation, workspace_id=workspace_id, force_restart=force_restart, create_new_chat=create_new_chat)

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