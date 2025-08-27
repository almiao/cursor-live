#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版Cursor AI对话框检测器
避开复杂的Accessibility API问题，使用更直接的方法
"""

import subprocess
import psutil
import time
import logging
from typing import Dict, Any, Optional

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimpleCursorDetector:
    """简化的Cursor检测器"""
    
    def __init__(self):
        self.cursor_pids = set()
        self._update_cursor_pids()
    
    def _update_cursor_pids(self):
        """更新Cursor进程ID"""
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
            logger.error(f"获取Cursor进程失败: {e}")
    
    def get_frontmost_app_info(self) -> Dict[str, Any]:
        """获取前台应用信息"""
        script = '''
        tell application "System Events"
            try
                set frontApp to first application process whose frontmost is true
                set appName to name of frontApp
                set appPID to unix id of frontApp
                return appName & "|" & appPID
            on error errMsg
                return "error|" & errMsg
            end try
        end tell
        '''
        
        try:
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                parts = output.split('|')
                if len(parts) >= 2 and parts[0] != 'error':
                    return {
                        'success': True,
                        'app_name': parts[0],
                        'app_pid': int(parts[1]) if parts[1].isdigit() else parts[1],
                        'is_cursor': 'cursor' in parts[0].lower() or int(parts[1]) in self.cursor_pids if parts[1].isdigit() else False
                    }
            
            return {'success': False, 'error': f'AppleScript失败: {result.stderr}'}
        
        except Exception as e:
            return {'success': False, 'error': f'执行异常: {e}'}
    
    def check_cursor_window_content(self) -> Dict[str, Any]:
        """通过窗口内容检查是否可能是AI对话框"""
        # 获取Cursor窗口标题
        script = '''
        tell application "System Events"
            try
                tell process "Cursor"
                    set windowTitles to {}
                    repeat with w in windows
                        try
                            set windowTitles to windowTitles & {name of w}
                        end try
                    end repeat
                    return my list_to_string(windowTitles, "|")
                end tell
            on error errMsg
                return "error:" & errMsg
            end try
        end tell
        
        on list_to_string(lst, delim)
            set text item delimiters to delim
            set result to lst as string
            set text item delimiters to ""
            return result
        end list_to_string
        '''
        
        try:
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                if not output.startswith('error:'):
                    window_titles = output.split('|') if output else []
                    
                    # 分析窗口标题，推测是否可能有AI对话框打开
                    ai_indicators = []
                    for title in window_titles:
                        title_lower = title.lower()
                        if any(keyword in title_lower for keyword in 
                               ['chat', 'ai', 'assistant', 'conversation', 'composer']):
                            ai_indicators.append(title)
                    
                    return {
                        'success': True,
                        'window_titles': window_titles,
                        'ai_indicators': ai_indicators,
                        'likely_ai_dialog': len(ai_indicators) > 0
                    }
            
            return {'success': False, 'error': f'获取窗口信息失败: {result.stderr}'}
            
        except Exception as e:
            return {'success': False, 'error': f'检查窗口异常: {e}'}
    
    def check_cursor_focused_element_simple(self) -> Dict[str, Any]:
        """简化的聚焦元素检查"""
        script = '''
        tell application "System Events"
            try
                tell process "Cursor"
                    try
                        set focusedElement to focused UI element
                        set elementRole to role of focusedElement as string
                        set elementDescription to ""
                        set elementValue to ""
                        
                        try
                            set elementDescription to description of focusedElement as string
                        end try
                        
                        try
                            set elementValue to value of focusedElement as string
                        end try
                        
                        return elementRole & "|" & elementDescription & "|" & elementValue
                    on error
                        return "no_focus||"
                    end try
                end tell
            on error errMsg
                return "error|" & errMsg & "|"
            end try
        end tell
        '''
        
        try:
            result = subprocess.run(['osascript', '-e', script], 
                                  capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0:
                output = result.stdout.strip()
                parts = output.split('|')
                
                if len(parts) >= 3:
                    role, description, value = parts[0], parts[1], parts[2]
                    
                    # 分析是否可能是AI输入框
                    is_input = role.lower() in ['text field', 'text area']
                    
                    all_text = (role + ' ' + description + ' ' + value).lower()
                    has_ai_keywords = any(keyword in all_text for keyword in 
                                        ['chat', 'message', 'ask', 'help', 'input', 'prompt'])
                    
                    return {
                        'success': True,
                        'role': role,
                        'description': description,
                        'value': value,
                        'is_input': is_input,
                        'has_ai_keywords': has_ai_keywords,
                        'likely_ai_input': is_input and (has_ai_keywords or 'text' in role.lower())
                    }
            
            return {'success': False, 'error': f'获取聚焦元素失败: {result.stderr}'}
            
        except Exception as e:
            return {'success': False, 'error': f'检查聚焦元素异常: {e}'}
    
    def detect_cursor_ai_dialog(self) -> Dict[str, Any]:
        """检测Cursor AI对话框状态"""
        result = {
            'cursor_running': len(self.cursor_pids) > 0,
            'cursor_frontmost': False,
            'ai_dialog_detected': False,
            'confidence': 0.0,
            'evidence': [],
            'details': {}
        }
        
        self._update_cursor_pids()
        result['cursor_running'] = len(self.cursor_pids) > 0
        
        if not result['cursor_running']:
            result['details']['error'] = 'Cursor未运行'
            return result
        
        # 检查前台应用
        frontmost_info = self.get_frontmost_app_info()
        if frontmost_info['success']:
            result['cursor_frontmost'] = frontmost_info['is_cursor']
            result['details']['frontmost_app'] = frontmost_info
            
            if result['cursor_frontmost']:
                result['confidence'] += 0.3
                result['evidence'].append('Cursor是前台应用')
        
        # 检查窗口内容
        window_info = self.check_cursor_window_content()
        if window_info['success']:
            result['details']['window_info'] = window_info
            
            if window_info['likely_ai_dialog']:
                result['confidence'] += 0.4
                result['evidence'].append(f'检测到AI相关窗口: {window_info["ai_indicators"]}')
        
        # 检查聚焦元素
        focus_info = self.check_cursor_focused_element_simple()
        if focus_info['success']:
            result['details']['focus_info'] = focus_info
            
            if focus_info['likely_ai_input']:
                result['confidence'] += 0.5
                result['evidence'].append(f'检测到可能的AI输入框: {focus_info["role"]}')
        
        # 最终判断
        result['ai_dialog_detected'] = result['confidence'] >= 0.6
        
        return result
    
    def monitor(self, callback=None, interval=1.0):
        """监控AI对话框状态"""
        logger.info("🔍 开始监控Cursor AI对话框状态...")
        
        last_state = False
        
        try:
            while True:
                result = self.detect_cursor_ai_dialog()
                current_state = result['ai_dialog_detected']
                
                if current_state != last_state:
                    if current_state:
                        logger.info(f"🎯 检测到AI对话框活动! 置信度: {result['confidence']:.2f}")
                        logger.info(f"   证据: {', '.join(result['evidence'])}")
                    else:
                        logger.info("📤 AI对话框活动结束")
                    
                    if callback:
                        callback(result)
                    
                    last_state = current_state
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("\n👋 监控已停止")

def main():
    """主函数"""
    detector = SimpleCursorDetector()
    
    print("🔍 简化版Cursor AI对话框检测器")
    print("="*50)
    
    # 单次检测
    result = detector.detect_cursor_ai_dialog()
    
    print(f"Cursor运行: {result['cursor_running']}")
    print(f"Cursor前台: {result['cursor_frontmost']}")
    print(f"AI对话框检测: {result['ai_dialog_detected']}")
    print(f"置信度: {result['confidence']:.2f}")
    
    if result['evidence']:
        print(f"证据: {', '.join(result['evidence'])}")
    
    # 显示详细信息
    if result['details'].get('focus_info', {}).get('success'):
        focus = result['details']['focus_info']
        print(f"聚焦元素: {focus.get('role', 'N/A')} - {focus.get('description', 'N/A')}")
    
    # 询问是否监控
    try:
        response = input("\n开始持续监控? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            detector.monitor(interval=0.5)
    except (KeyboardInterrupt, EOFError):
        print("\n👋 检测结束")

if __name__ == "__main__":
    main()