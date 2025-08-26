#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor AI对话框聚焦状态检测器
使用macOS Accessibility API检测用户是否正在Cursor的AI对话框中输入
"""

import logging
try:
    from ApplicationServices import *
except ImportError:
    try:
        from Quartz import *
    except ImportError:
        print("警告: 无法导入Accessibility API，请确保在macOS上运行")
        # 定义占位符常量和函数
        kAXFocusedUIElementAttribute = "AXFocusedUIElement"
        kAXTitleAttribute = "AXTitle"
        kAXRoleAttribute = "AXRole"
        kAXValueAttribute = "AXValue"
        kAXDescriptionAttribute = "AXDescription"
        kAXIdentifierAttribute = "AXIdentifier"
        kAXErrorSuccess = 0
        
        def AXUIElementCreateSystemWide():
            return None
        
        def AXUIElementCopyAttributeValue(element, attribute, value):
            return (1, None)  # 返回错误码和None值
        
        def AXUIElementGetPid(element):
            return None
import psutil

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class CursorFocusDetector:
    """
    Cursor AI对话框聚焦状态检测器
    """
    
    def __init__(self):
        """
        初始化检测器
        """
        self.cursor_pids = set()
        self._update_cursor_pids()
    
    def _update_cursor_pids(self):
        """
        更新Cursor进程ID列表
        """
        try:
            self.cursor_pids.clear()
            for proc in psutil.process_iter(['pid', 'name']):
                if 'cursor' in proc.info['name'].lower():
                    self.cursor_pids.add(proc.info['pid'])
            logger.debug(f"找到Cursor进程: {self.cursor_pids}")
        except Exception as e:
            logger.error(f"更新Cursor进程ID失败: {e}")
    
    def get_focused_element(self):
        """
        获取当前聚焦的UI元素
        
        Returns:
            tuple: (element, success) - UI元素和是否成功获取
        """
        try:
            sys_element = AXUIElementCreateSystemWide()
            error, focused_element = AXUIElementCopyAttributeValue(
                sys_element, 
                kAXFocusedUIElementAttribute, 
                None
            )
            
            if error == kAXErrorSuccess and focused_element:
                return focused_element, True
            else:
                logger.debug(f"获取聚焦元素失败，错误码: {error}")
                return None, False
                
        except Exception as e:
            logger.error(f"获取聚焦元素异常: {e}")
            return None, False
    
    def get_element_info(self, element):
        """
        获取UI元素的详细信息
        
        Args:
            element: AXUIElement对象
            
        Returns:
            dict: 元素信息字典
        """
        if not element:
            return {}
        
        info = {}
        
        # 获取各种属性
        attributes = {
            'title': kAXTitleAttribute,
            'role': kAXRoleAttribute,
            'value': kAXValueAttribute,
            'description': kAXDescriptionAttribute,
            'identifier': kAXIdentifierAttribute
        }
        
        for attr_name, attr_constant in attributes.items():
            try:
                error, value = AXUIElementCopyAttributeValue(element, attr_constant, None)
                if error == kAXErrorSuccess and value:
                    info[attr_name] = str(value)
                else:
                    info[attr_name] = ''
            except Exception as e:
                logger.debug(f"获取属性 {attr_name} 失败: {e}")
                info[attr_name] = ''
        
        # 获取进程ID
        try:
            pid = AXUIElementGetPid(element)
            info['pid'] = pid
        except Exception as e:
            logger.debug(f"获取进程ID失败: {e}")
            info['pid'] = None
        
        return info
    
    def is_cursor_element(self, element_info):
        """
        判断元素是否属于Cursor应用
        
        Args:
            element_info (dict): 元素信息
            
        Returns:
            bool: 是否属于Cursor
        """
        if not element_info or not element_info.get('pid'):
            return False
        
        return element_info['pid'] in self.cursor_pids
    
    def is_ai_chat_input(self, element_info):
        """
        判断元素是否是AI对话框的输入控件
        
        Args:
            element_info (dict): 元素信息
            
        Returns:
            bool: 是否是AI对话框输入控件
        """
        if not element_info:
            return False
        
        # 检查角色类型
        role = element_info.get('role', '').lower()
        if role not in ['axtextfield', 'axtextarea', 'axcombobox']:
            return False
        
        # 检查标识符、标题、描述等是否包含AI相关关键词
        text_fields = [
            element_info.get('identifier', ''),
            element_info.get('title', ''),
            element_info.get('description', ''),
            element_info.get('value', '')
        ]
        
        combined_text = ' '.join(text_fields).lower()
        
        # AI对话框相关关键词
        ai_keywords = [
            'chat', 'ai', 'assistant', 'copilot', 'conversation',
            'message', 'input', 'prompt', 'query', 'ask'
        ]
        
        return any(keyword in combined_text for keyword in ai_keywords)
    
    def check_cursor_ai_focus(self):
        """
        检查用户是否正在Cursor的AI对话框中输入
        
        Returns:
            dict: 检测结果
                {
                    'is_focused': bool,  # 是否聚焦在AI对话框
                    'element_info': dict,  # 聚焦元素信息
                    'cursor_detected': bool,  # 是否检测到Cursor
                    'ai_input_detected': bool  # 是否检测到AI输入框
                }
        """
        # 更新Cursor进程列表
        self._update_cursor_pids()
        
        # 获取当前聚焦元素
        focused_element, success = self.get_focused_element()
        
        result = {
            'is_focused': False,
            'element_info': {},
            'cursor_detected': False,
            'ai_input_detected': False
        }
        
        if not success or not focused_element:
            logger.debug("未获取到聚焦元素")
            return result
        
        # 获取元素信息
        element_info = self.get_element_info(focused_element)
        result['element_info'] = element_info
        
        # 检查是否属于Cursor
        is_cursor = self.is_cursor_element(element_info)
        result['cursor_detected'] = is_cursor
        
        if not is_cursor:
            logger.debug(f"聚焦元素不属于Cursor应用，PID: {element_info.get('pid')}")
            return result
        
        # 检查是否是AI输入框
        is_ai_input = self.is_ai_chat_input(element_info)
        result['ai_input_detected'] = is_ai_input
        
        # 最终判断
        result['is_focused'] = is_cursor and is_ai_input
        
        if result['is_focused']:
            logger.info(f"✅ 用户正在Cursor AI对话框中输入: {element_info}")
        else:
            logger.debug(f"❌ 用户未在Cursor AI对话框中，当前聚焦: {element_info}")
        
        return result
    
    def monitor_focus(self, callback=None, interval=0.1):
        """
        持续监控聚焦状态
        
        Args:
            callback (function): 状态变化时的回调函数
            interval (float): 检查间隔（秒）
        """
        import time
        
        last_focus_state = False
        
        logger.info("🔍 开始监控Cursor AI对话框聚焦状态...")
        
        try:
            while True:
                result = self.check_cursor_ai_focus()
                current_focus_state = result['is_focused']
                
                # 状态发生变化时触发回调
                if current_focus_state != last_focus_state:
                    logger.info(f"📍 聚焦状态变化: {last_focus_state} -> {current_focus_state}")
                    
                    if callback:
                        callback(result)
                    
                    last_focus_state = current_focus_state
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("\n👋 监控已停止")

def main():
    """
    主函数：演示聚焦检测功能
    """
    detector = CursorFocusDetector()
    
    def focus_callback(result):
        """
        聚焦状态变化回调函数
        """
        if result['is_focused']:
            print("🎯 用户开始在Cursor AI对话框中输入！")
        else:
            print("📤 用户离开了Cursor AI对话框")
    
    # 开始监控
    detector.monitor_focus(callback=focus_callback, interval=0.1)

if __name__ == "__main__":
    main()