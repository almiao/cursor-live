#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor窗口检测器
使用macOS的AppKit和Quartz框架来检测Cursor应用的窗口状态
比图像识别更高效和准确
"""

import logging
from typing import Optional, List, Dict, Any, Union

# 类型定义
NSWorkspaceType = Any
AXUIElementType = Any

# macOS框架导入和常量定义
MAC_OS_AVAILABLE = False
NSWorkspace = None
AXUIElementCreateApplication = None
kAXWindowsAttribute = "AXWindows"
kAXTitleAttribute = "AXTitle"
kAXRoleAttribute = "AXRole"
kAXSubroleAttribute = "AXSubrole"
kAXChildrenAttribute = "AXChildren"
kAXValueAttribute = "AXValue"
AXUIElementCopyAttributeValue = None
kAXErrorSuccess = 0
AXIsProcessTrusted = None

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

logger = logging.getLogger(__name__)

class CursorWindowDetector:
    """
    Cursor窗口检测器
    使用macOS的Accessibility API来检测Cursor应用的窗口和对话框状态
    """
    
    def __init__(self):
        self.cursor_pid: Optional[int] = None
        self.app_ref: Optional[AXUIElementType] = None
        self._check_accessibility_permissions()
        
    def _check_accessibility_permissions(self) -> bool:
        """
        检查Accessibility权限
        
        Returns:
            bool: 是否有权限
        """
        if not MACOS_AVAILABLE:
            return False
            
        try:
            from ApplicationServices import AXIsProcessTrusted  # type: ignore
            is_trusted = AXIsProcessTrusted()
            if not is_trusted:
                logger.warning("Accessibility权限未授予")
                logger.warning("请在系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能中添加此应用的权限")
                return False
            return True
        except ImportError:
            logger.warning("无法检查Accessibility权限")
            return False
        except Exception as e:
            logger.error(f"检查Accessibility权限时发生错误: {e}")
            return False
        
    def find_cursor_process(self) -> Optional[int]:
        """
        查找Cursor进程的PID
        
        Returns:
            Optional[int]: Cursor进程的PID，如果未找到返回None
        """
        if not MACOS_AVAILABLE:
            logger.error("macOS框架不可用，无法检测Cursor进程")
            return None
            
        try:
            logger.info("开始查找Cursor进程...")
            ws = NSWorkspace.sharedWorkspace()  # type: ignore
            if not ws:
                logger.error("无法获取NSWorkspace实例")
                return None
                
            apps = ws.runningApplications()  # type: ignore
            
            cursor_pid = None
            for app in apps:
                app_name = app.localizedName()
                bundle_id = app.bundleIdentifier()
                pid = app.processIdentifier()
                
                logger.debug(f"检查应用: {app_name} (Bundle ID: {bundle_id}, PID: {pid})")
                
                # 检查应用名称或Bundle ID，优先选择主Cursor应用
                if app_name == "Cursor" or (bundle_id and bundle_id == "com.todesktop.230313mzl4w4u92"):
                    cursor_pid = pid
                    logger.info(f"找到主Cursor进程: {app_name} (PID: {pid}, Bundle ID: {bundle_id})")
                    break
                elif (app_name and "Cursor" in app_name) or (bundle_id and "cursor" in bundle_id.lower()):
                    # 如果没有找到主应用，记录备选项
                    if not cursor_pid:
                        cursor_pid = pid
                        logger.info(f"找到Cursor相关进程: {app_name} (PID: {pid}, Bundle ID: {bundle_id})")
            
            if not cursor_pid:
                logger.warning("未找到Cursor进程")
                return None
                
            self.cursor_pid = cursor_pid
            return cursor_pid
            
        except Exception as e:
            logger.error(f"查找Cursor进程时发生异常: {e}")
            return None
    
    def get_cursor_app_ref(self) -> bool:
        """
        获取Cursor应用的AXUIElement引用
        
        Returns:
            bool: 成功获取返回True，失败返回False
        """
        if not self.cursor_pid:
            if not self.find_cursor_process():
                return False
        
        try:
            logger.info(f"创建Cursor应用的AXUIElement引用 (PID: {self.cursor_pid})")
            self.app_ref = AXUIElementCreateApplication(self.cursor_pid)  # type: ignore
            logger.info("成功创建AXUIElement引用")
            return True
            
        except Exception as e:
            logger.error(f"创建AXUIElement引用失败: {e}")
            return False
    
    def get_cursor_windows(self) -> List[Dict[str, Any]]:
        """
        获取Cursor的所有窗口信息
        
        Returns:
            List[Dict[str, Any]]: 窗口信息列表
        """
        if not self.app_ref:
            if not self.get_cursor_app_ref():
                logger.error("无法获取Cursor应用引用")
                return []
        
        try:
            logger.info("开始获取Cursor窗口列表...")
            
            # 获取窗口列表
            error_code, windows = AXUIElementCopyAttributeValue(  # type: ignore
                self.app_ref, 
                kAXWindowsAttribute,  # type: ignore
                None
            )
            
            if error_code != kAXErrorSuccess:  # type: ignore
                if error_code == -25204:
                    logger.error(f"获取窗口列表失败，错误代码: {error_code} - Accessibility权限被拒绝")
                    logger.error("请在系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能中添加此应用的权限")
                else:
                    logger.error(f"获取窗口列表失败，错误代码: {error_code}")
                return []
            
            if not windows:
                logger.warning("Cursor没有可见窗口")
                return []
            
            window_info_list = []
            logger.info(f"找到 {len(windows)} 个Cursor窗口")
            
            for i, window in enumerate(windows):
                try:
                    # 获取窗口标题
                    title_error, title = AXUIElementCopyAttributeValue(  # type: ignore
                        window, 
                        kAXTitleAttribute,  # type: ignore
                        None
                    )
                    
                    window_title = title if title_error == kAXErrorSuccess else "未知标题"  # type: ignore
                    
                    # 获取窗口角色
                    role_error, role = AXUIElementCopyAttributeValue(  # type: ignore
                        window, 
                        kAXRoleAttribute,  # type: ignore
                        None
                    )
                    
                    window_role = role if role_error == kAXErrorSuccess else "未知角色"  # type: ignore
                    
                    window_info = {
                        'index': i,
                        'title': window_title,
                        'role': window_role,
                        'element': window
                    }
                    
                    window_info_list.append(window_info)
                    logger.info(f"窗口 {i}: 标题='{window_title}', 角色='{window_role}'")
                    
                except Exception as e:
                    logger.warning(f"获取窗口 {i} 信息时发生异常: {e}")
                    continue
            
            return window_info_list
            
        except Exception as e:
            logger.error(f"获取Cursor窗口列表时发生异常: {e}")
            return []
    
    def detect_dialog_state_via_accessibility(self) -> Dict[str, Any]:
        """
        AI对话框状态检测 - 现在使用workbench.auxiliaryBar.hidden检查
        
        Returns:
            Dict[str, Any]: 检测结果
        """
        logger.info("AI对话框检测已更新为使用workbench.auxiliaryBar.hidden")
        
        return {
            'dialog_state': 'unknown',
            'is_dialog_open': False,
            'is_empty': True,
            'status': 'success',
            'method': 'workbench.auxiliaryBar.hidden',
            'message': '请使用/api/cursor/status?workspace_id=<workspace_id>来检查AI侧边栏状态'
        }
    
    def _search_dialog_elements(self, elements, depth: int = 0, max_depth: int = 3) -> List[Dict[str, Any]]:
        """
        递归搜索对话框相关的UI元素
        
        Args:
            elements: UI元素列表
            depth: 当前递归深度
            max_depth: 最大递归深度
            
        Returns:
            List[Dict[str, Any]]: 找到的对话框相关元素
        """
        if depth > max_depth:
            return []
        
        dialog_elements = []
        
        for element in elements:
            try:
                # 获取元素角色
                role_error, role = AXUIElementCopyAttributeValue(  # type: ignore
                    element, 
                    kAXRoleAttribute,  # type: ignore
                    None
                )
                
                # 获取元素值（如果有）
                value_error, value = AXUIElementCopyAttributeValue(  # type: ignore
                    element, 
                    kAXValueAttribute,  # type: ignore
                    None
                )
                
                element_role = role if role_error == kAXErrorSuccess else None  # type: ignore
                element_value = value if value_error == kAXErrorSuccess else None  # type: ignore
                
                logger.debug(f"{'  ' * depth}元素角色: {element_role}, 值: {element_value}")
                
                # 检查是否是对话框相关的元素
                if element_role and self._is_dialog_related_element(element_role, element_value):
                    dialog_info = {
                        'role': element_role,
                        'value': element_value,
                        'depth': depth
                    }
                    dialog_elements.append(dialog_info)
                    logger.info(f"{'  ' * depth}找到对话框相关元素: {dialog_info}")
                
                # 递归检查子元素
                children_error, children = AXUIElementCopyAttributeValue(  # type: ignore
                    element, 
                    kAXChildrenAttribute,  # type: ignore
                    None
                )
                
                if children_error == kAXErrorSuccess and children:  # type: ignore
                    child_dialog_elements = self._search_dialog_elements(
                        children, 
                        depth + 1, 
                        max_depth
                    )
                    dialog_elements.extend(child_dialog_elements)
                
            except Exception as e:
                logger.debug(f"{'  ' * depth}检查元素时发生异常: {e}")
                continue
        
        return dialog_elements
    
    def _is_dialog_related_element(self, role: str, value: Any) -> bool:
        """
        判断UI元素是否与对话框相关
        
        Args:
            role: 元素角色
            value: 元素值
            
        Returns:
            bool: 是否为对话框相关元素
        """
        if not role:
            return False
        
        # 对话框相关的角色
        dialog_roles = [
            'AXTextField',  # 文本输入框
            'AXTextArea',   # 文本区域
            'AXButton',     # 按钮
            'AXStaticText', # 静态文本
            'AXGroup'       # 组合元素
        ]
        
        if role in dialog_roles:
            # 如果有值，检查值是否包含对话框相关的关键词
            if value and isinstance(value, str):
                dialog_keywords = [
                    'chat', 'dialog', 'conversation', 'message', 
                    'send', 'submit', 'ask', 'query', 'prompt',
                    '对话', '聊天', '消息', '发送', '提交', '询问'
                ]
                
                value_lower = value.lower()
                for keyword in dialog_keywords:
                    if keyword in value_lower:
                        return True
            
            # 即使没有明确的关键词，某些角色也可能表示对话框
            return role in ['AXTextField', 'AXTextArea']
        
        return False
    
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


def test_cursor_detection():
    """
    测试Cursor检测功能
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    detector = CursorWindowDetector()
    
    print("=== 测试Cursor进程检测 ===")
    pid = detector.find_cursor_process()
    if pid:
        print(f"✓ 找到Cursor进程，PID: {pid}")
    else:
        print("✗ 未找到Cursor进程")
        return
    
    print("\n=== 测试前台应用检测 ===")
    frontmost_result = detector.is_cursor_frontmost()
    print(f"前台检测结果: {frontmost_result}")
    
    print("\n=== 测试窗口列表获取 ===")
    windows = detector.get_cursor_windows()
    if windows:
        print(f"✓ 找到 {len(windows)} 个Cursor窗口")
        for window in windows:
            print(f"  - {window['title']} ({window['role']})")
    else:
        print("✗ 未找到Cursor窗口")
    
    print("\n=== 测试对话框状态检测 ===")
    dialog_result = detector.detect_dialog_state_via_accessibility()
    print(f"对话框检测结果: {dialog_result}")


if __name__ == "__main__":
    test_cursor_detection()