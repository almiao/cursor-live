#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进的Cursor AI对话框聚焦状态检测器
修复了Accessibility权限问题和检测逻辑问题
"""

import logging
import time
import subprocess
import json
from typing import Dict, Any, Optional, List
import psutil

# 尝试导入Accessibility API
try:
    from ApplicationServices import (
        AXUIElementCreateSystemWide,
        AXUIElementCreateApplication,
        AXUIElementCopyAttributeValue,
        AXUIElementGetPid,
        AXIsProcessTrusted,
        kAXFocusedUIElementAttribute,
        kAXTitleAttribute,
        kAXRoleAttribute,
        kAXValueAttribute,
        kAXDescriptionAttribute,
        kAXIdentifierAttribute,
        kAXChildrenAttribute,
        kAXWindowsAttribute,
        kAXErrorSuccess
    )
    ACCESSIBILITY_AVAILABLE = True
except ImportError:
    ACCESSIBILITY_AVAILABLE = False

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ImprovedCursorFocusDetector:
    """改进的Cursor AI对话框聚焦状态检测器"""
    
    def __init__(self):
        self.cursor_pids = set()
        self.last_focused_info = None
        self._update_cursor_pids()
    
    def _update_cursor_pids(self):
        """更新Cursor进程ID列表"""
        try:
            self.cursor_pids.clear()
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    if 'cursor' in proc.info['name'].lower():
                        self.cursor_pids.add(proc.info['pid'])
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            logger.debug(f"找到Cursor进程: {self.cursor_pids}")
        except Exception as e:
            logger.error(f"更新Cursor进程ID失败: {e}")
    
    def check_accessibility_permission(self) -> bool:
        """
        检查并尝试获取Accessibility权限
        
        Returns:
            bool: 是否有权限
        """
        if not ACCESSIBILITY_AVAILABLE:
            logger.error("Accessibility API不可用")
            return False
        
        try:
            # 检查当前权限状态
            is_trusted = AXIsProcessTrusted()
            if is_trusted:
                logger.info("✅ Accessibility权限已授权")
                return True
            
            # 尝试请求权限
            logger.warning("⚠️  Accessibility权限未授权，尝试请求权限...")
            
            # 创建一个请求权限的对话框
            script = """
            tell application "System Events"
                display dialog "需要Accessibility权限来检测Cursor AI对话框状态。\\n\\n请在系统偏好设置中授权：\\n系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能" buttons {"取消", "打开设置"} default button "打开设置"
                if button returned of result is "打开设置" then
                    tell application "System Preferences"
                        activate
                        set current pane to pane "com.apple.preference.security"
                        reveal anchor "Privacy_Accessibility" of pane "com.apple.preference.security"
                    end tell
                end if
            end tell
            """
            
            try:
                subprocess.run(['osascript', '-e', script], check=False, timeout=30)
            except subprocess.TimeoutExpired:
                logger.info("用户取消了权限设置")
            except Exception as e:
                logger.debug(f"显示权限请求对话框失败: {e}")
            
            return False
            
        except Exception as e:
            logger.error(f"检查Accessibility权限失败: {e}")
            return False
    
    def get_focused_element_fallback(self) -> Dict[str, Any]:
        """
        fallback方法：通过AppleScript获取聚焦元素信息
        
        Returns:
            Dict[str, Any]: 聚焦元素信息
        """
        result = {
            'success': False,
            'element_info': {},
            'error': None,
            'method': 'applescript'
        }
        
        script = '''
        tell application "System Events"
            try
                set frontApp to first application process whose frontmost is true
                set appName to name of frontApp
                set appPID to unix id of frontApp
                
                try
                    set focusedElement to focused UI element of frontApp
                    set elementRole to role of focusedElement as string
                    set elementValue to ""
                    set elementDescription to ""
                    set elementTitle to ""
                    
                    try
                        set elementValue to value of focusedElement as string
                    end try
                    
                    try
                        set elementDescription to description of focusedElement as string
                    end try
                    
                    try
                        set elementTitle to title of focusedElement as string
                    end try
                    
                    return "app_name:" & appName & "|app_pid:" & appPID & "|role:" & elementRole & "|value:" & elementValue & "|description:" & elementDescription & "|title:" & elementTitle
                on error
                    return "app_name:" & appName & "|app_pid:" & appPID & "|error:no_focused_element"
                end try
            on error errMsg
                return "error:" & errMsg
            end try
        end tell
        '''
        
        try:
            proc = subprocess.run(['osascript', '-e', script], 
                                capture_output=True, text=True, timeout=5)
            
            if proc.returncode == 0:
                output = proc.stdout.strip()
                if output:
                    try:
                        # 简单的JSON解析（AppleScript返回的不是完美的JSON）
                        info = self._parse_applescript_output(output)
                        result['success'] = True
                        result['element_info'] = info
                        logger.debug(f"AppleScript获取聚焦元素成功: {info}")
                    except Exception as e:
                        result['error'] = f"解析AppleScript输出失败: {e}"
                        logger.debug(f"AppleScript输出: {output}")
                else:
                    result['error'] = "AppleScript无输出"
            else:
                result['error'] = f"AppleScript执行失败: {proc.stderr}"
                
        except subprocess.TimeoutExpired:
            result['error'] = "AppleScript执行超时"
        except Exception as e:
            result['error'] = f"AppleScript异常: {e}"
        
        return result
    
    def _parse_applescript_output(self, output: str) -> Dict[str, Any]:
        """解析AppleScript输出"""
        info = {}
        
        # 按|分割输出
        parts = output.strip().split('|')
        
        for part in parts:
            if ':' in part:
                key, value = part.split(':', 1)
                if key == 'app_pid':
                    try:
                        info[key] = int(value)
                    except ValueError:
                        info[key] = value
                else:
                    info[key] = value
        
        return info
    
    def get_focused_element_accessibility(self) -> Dict[str, Any]:
        """
        通过Accessibility API获取聚焦元素信息
        
        Returns:
            Dict[str, Any]: 聚焦元素信息
        """
        result = {
            'success': False,
            'element_info': {},
            'error': None,
            'method': 'accessibility'
        }
        
        if not ACCESSIBILITY_AVAILABLE:
            result['error'] = 'Accessibility API不可用'
            return result
        
        if not self.check_accessibility_permission():
            result['error'] = 'Accessibility权限不足'
            return result
        
        try:
            sys_element = AXUIElementCreateSystemWide()
            error_code, focused_element = AXUIElementCopyAttributeValue(
                sys_element,
                kAXFocusedUIElementAttribute,
                None
            )
            
            if error_code == kAXErrorSuccess and focused_element:
                element_info = self._get_element_detailed_info(focused_element)
                result['success'] = True
                result['element_info'] = element_info
                logger.debug(f"Accessibility API获取聚焦元素成功")
            else:
                result['error'] = f'获取聚焦元素失败，错误码: {error_code}'
                
        except Exception as e:
            result['error'] = f'Accessibility API异常: {e}'
        
        return result
    
    def _get_element_detailed_info(self, element) -> Dict[str, Any]:
        """获取元素的详细信息（Accessibility API）"""
        info = {
            'app_pid': None,
            'role': '',
            'title': '',
            'value': '',
            'description': '',
            'identifier': '',
        }
        
        if not element:
            return info
        
        # 获取进程ID
        try:
            info['app_pid'] = AXUIElementGetPid(element)
        except Exception:
            pass
        
        # 获取各种属性
        attributes = {
            'role': kAXRoleAttribute,
            'title': kAXTitleAttribute,
            'value': kAXValueAttribute,
            'description': kAXDescriptionAttribute,
            'identifier': kAXIdentifierAttribute
        }
        
        for attr_name, attr_constant in attributes.items():
            try:
                error_code, value = AXUIElementCopyAttributeValue(element, attr_constant, None)
                if error_code == kAXErrorSuccess and value:
                    info[attr_name] = str(value)
            except Exception:
                pass
        
        return info
    
    def get_focused_element(self) -> Dict[str, Any]:
        """
        获取聚焦元素信息，优先使用Accessibility API，fallback到AppleScript
        
        Returns:
            Dict[str, Any]: 聚焦元素信息
        """
        # 首先尝试Accessibility API
        result = self.get_focused_element_accessibility()
        
        if result['success']:
            return result
        
        # fallback到AppleScript
        logger.debug("Accessibility API失败，尝试AppleScript fallback")
        fallback_result = self.get_focused_element_fallback()
        
        if fallback_result['success']:
            return fallback_result
        
        # 两种方法都失败
        return {
            'success': False,
            'element_info': {},
            'error': f"Accessibility: {result['error']}, AppleScript: {fallback_result['error']}",
            'method': 'both_failed'
        }
    
    def is_cursor_ai_dialog_focused(self, element_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        判断是否聚焦在Cursor AI对话框
        
        Args:
            element_info: 元素信息
            
        Returns:
            Dict[str, Any]: 分析结果
        """
        analysis = {
            'is_cursor_focused': False,
            'is_ai_dialog': False,
            'confidence': 0.0,
            'reasons': [],
            'element_summary': ''
        }
        
        if not element_info:
            return analysis
        
        # 检查是否为Cursor进程
        app_pid = element_info.get('app_pid')
        app_name = element_info.get('app_name', '')
        
        is_cursor_app = False
        if app_pid and app_pid in self.cursor_pids:
            is_cursor_app = True
        elif 'cursor' in app_name.lower():
            is_cursor_app = True
        
        analysis['is_cursor_focused'] = is_cursor_app
        
        if not is_cursor_app:
            analysis['element_summary'] = f"非Cursor应用: {app_name} (PID: {app_pid})"
            return analysis
        
        analysis['confidence'] += 0.5
        analysis['reasons'].append(f"聚焦在Cursor应用 ({app_name})")
        
        # 检查元素类型和内容
        role = element_info.get('role', '').lower()
        value = element_info.get('value', '').lower()
        title = element_info.get('title', '').lower()
        description = element_info.get('description', '').lower()
        
        # 合并所有文本内容进行分析
        all_text = ' '.join([role, value, title, description])
        analysis['element_summary'] = f"角色: {role}, 值: {value[:50]}"
        
        # 检查是否为输入控件
        input_roles = ['text field', 'text area', 'combo box', 'axtextfield', 'axtextarea']
        is_input = any(input_role in role for input_role in input_roles)
        
        if is_input:
            analysis['confidence'] += 0.3
            analysis['reasons'].append(f"输入控件类型: {role}")
        
        # AI对话框相关关键词检测（更宽松的匹配）
        ai_keywords = [
            # 英文关键词
            'chat', 'ai', 'assistant', 'copilot', 'conversation',
            'message', 'input', 'prompt', 'query', 'ask', 'help',
            'composer', 'generate', 'code', 'cmd+k', 'ctrl+k',
            # 可能的占位符文本
            'ask', 'type', 'message', 'search', 'command',
            # Cursor特有的
            'cursor', 'edit', 'explain', 'fix'
        ]
        
        found_keywords = []
        for keyword in ai_keywords:
            if keyword in all_text:
                found_keywords.append(keyword)
        
        if found_keywords:
            analysis['confidence'] += 0.2 * len(found_keywords)
            analysis['reasons'].append(f"包含AI关键词: {found_keywords}")
        
        # 特殊规则：如果是Cursor的输入框且包含任何相关文本，很可能是AI对话框
        if is_cursor_app and is_input:
            if any(word in all_text for word in ['message', 'chat', 'ask', 'help', 'command']):
                analysis['confidence'] += 0.2
                analysis['reasons'].append("Cursor输入框包含对话相关词汇")
        
        # 最终判断
        analysis['is_ai_dialog'] = analysis['confidence'] >= 0.7
        
        return analysis
    
    def check_cursor_ai_focus(self) -> Dict[str, Any]:
        """
        检查用户是否正在Cursor的AI对话框中输入
        
        Returns:
            Dict[str, Any]: 检测结果
        """
        self._update_cursor_pids()
        
        result = {
            'is_ai_dialog_focused': False,
            'cursor_detected': len(self.cursor_pids) > 0,
            'element_info': {},
            'analysis': {},
            'method': 'unknown',
            'error': None
        }
        
        if not result['cursor_detected']:
            result['error'] = 'Cursor未运行'
            return result
        
        # 获取聚焦元素
        focused_result = self.get_focused_element()
        result['method'] = focused_result.get('method', 'unknown')
        
        if not focused_result['success']:
            result['error'] = focused_result['error']
            return result
        
        result['element_info'] = focused_result['element_info']
        
        # 分析是否为AI对话框
        analysis = self.is_cursor_ai_dialog_focused(focused_result['element_info'])
        result['analysis'] = analysis
        result['is_ai_dialog_focused'] = analysis['is_ai_dialog']
        
        return result
    
    def monitor_focus(self, callback=None, interval=1.0, duration=None):
        """
        持续监控聚焦状态
        
        Args:
            callback: 状态变化时的回调函数
            interval: 检查间隔（秒）
            duration: 监控时长（秒），None表示无限期
        """
        logger.info("🔍 开始监控Cursor AI对话框聚焦状态...")
        
        last_state = False
        start_time = time.time()
        
        try:
            while True:
                if duration and (time.time() - start_time) > duration:
                    break
                
                result = self.check_cursor_ai_focus()
                current_state = result['is_ai_dialog_focused']
                
                # 状态变化时触发回调和日志
                if current_state != last_state:
                    if current_state:
                        logger.info("🎯 用户开始在Cursor AI对话框中输入！")
                        logger.info(f"   检测方法: {result['method']}")
                        logger.info(f"   置信度: {result['analysis'].get('confidence', 0):.2f}")
                        logger.info(f"   原因: {result['analysis'].get('reasons', [])}")
                    else:
                        logger.info("📤 用户离开了Cursor AI对话框")
                    
                    if callback:
                        callback(result)
                    
                    last_state = current_state
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("\n👋 监控已停止")

def main():
    """主函数：演示检测功能"""
    detector = ImprovedCursorFocusDetector()
    
    print("🔍 改进的Cursor AI对话框聚焦检测")
    print("="*50)
    
    # 单次检测
    result = detector.check_cursor_ai_focus()
    
    print(f"Cursor运行状态: {result['cursor_detected']}")
    print(f"检测方法: {result['method']}")
    print(f"AI对话框聚焦: {result['is_ai_dialog_focused']}")
    
    if result['error']:
        print(f"错误: {result['error']}")
    
    if result['element_info']:
        print(f"当前聚焦: {result['analysis'].get('element_summary', 'N/A')}")
        if result['analysis'].get('reasons'):
            print(f"分析原因: {result['analysis']['reasons']}")
    
    # 询问是否持续监控
    try:
        response = input("\n是否开始持续监控? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            def focus_callback(result):
                if result['is_ai_dialog_focused']:
                    print("✅ AI对话框已聚焦")
                else:
                    print("❌ AI对话框未聚焦")
            
            detector.monitor_focus(callback=focus_callback, interval=0.5)
    except (KeyboardInterrupt, EOFError):
        print("\n👋 检测结束")

if __name__ == "__main__":
    main()