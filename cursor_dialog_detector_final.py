#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor AI对话框检测器 - 最终版
整合多种检测方法，提供最可靠的AI对话框状态检测
"""

import subprocess
import psutil
import time
import logging
import json
from typing import Dict, Any, List, Optional, Callable
from enum import Enum

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DetectionMethod(Enum):
    """检测方法枚举"""
    PROCESS_FOCUS = "process_focus"
    WINDOW_ANALYSIS = "window_analysis"
    ELEMENT_FOCUS = "element_focus"
    HEURISTIC = "heuristic"

class CursorDialogDetector:
    """Cursor AI对话框检测器"""
    
    def __init__(self):
        self.cursor_pids = set()
        self.last_detection_result = None
        self.detection_history = []
        self._update_cursor_pids()
    
    def _update_cursor_pids(self):
        """更新Cursor进程ID列表"""
        try:
            self.cursor_pids.clear()
            cursor_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'create_time']):
                try:
                    name = proc.info['name'].lower()
                    if 'cursor' in name:
                        self.cursor_pids.add(proc.info['pid'])
                        cursor_processes.append({
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'create_time': proc.info['create_time']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            logger.debug(f"找到 {len(cursor_processes)} 个Cursor进程")
            return cursor_processes
            
        except Exception as e:
            logger.error(f"获取Cursor进程失败: {e}")
            return []
    
    def detect_frontmost_app(self) -> Dict[str, Any]:
        """检测前台应用 (方法1: 进程聚焦检测)"""
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
        
        result = {
            'method': DetectionMethod.PROCESS_FOCUS.value,
            'success': False,
            'is_cursor_front': False,
            'app_name': '',
            'app_pid': None,
            'confidence': 0.0
        }
        
        try:
            proc_result = subprocess.run(['osascript', '-e', script], 
                                       capture_output=True, text=True, timeout=2)
            
            if proc_result.returncode == 0:
                output = proc_result.stdout.strip()
                parts = output.split('|')
                
                if len(parts) >= 2 and parts[0] != 'error':
                    result['success'] = True
                    result['app_name'] = parts[0]
                    result['app_pid'] = int(parts[1]) if parts[1].isdigit() else None
                    
                    # 判断是否为Cursor
                    is_cursor_by_name = 'cursor' in parts[0].lower()
                    is_cursor_by_pid = result['app_pid'] in self.cursor_pids if result['app_pid'] else False
                    
                    result['is_cursor_front'] = is_cursor_by_name or is_cursor_by_pid
                    result['confidence'] = 0.9 if result['is_cursor_front'] else 0.0
                    
                    logger.debug(f"前台应用: {result['app_name']} (PID: {result['app_pid']}, Cursor: {result['is_cursor_front']})")
        
        except Exception as e:
            logger.debug(f"检测前台应用失败: {e}")
        
        return result
    
    def analyze_cursor_windows(self) -> Dict[str, Any]:
        """分析Cursor窗口内容 (方法2: 窗口分析)"""
        script = '''
        tell application "System Events"
            try
                tell process "Cursor"
                    set windowInfo to {}
                    repeat with w in windows
                        try
                            set windowName to name of w
                            set windowInfo to windowInfo & {windowName}
                        on error
                            set windowInfo to windowInfo & {"Untitled"}
                        end try
                    end repeat
                    
                    set text item delimiters to "|"
                    set result to windowInfo as string
                    set text item delimiters to ""
                    return result
                end tell
            on error errMsg
                return "error:" & errMsg
            end try
        end tell
        '''
        
        result = {
            'method': DetectionMethod.WINDOW_ANALYSIS.value,
            'success': False,
            'window_titles': [],
            'ai_indicators': [],
            'confidence': 0.0
        }
        
        try:
            proc_result = subprocess.run(['osascript', '-e', script], 
                                       capture_output=True, text=True, timeout=2)
            
            if proc_result.returncode == 0:
                output = proc_result.stdout.strip()
                
                if not output.startswith('error:'):
                    window_titles = [t.strip() for t in output.split('|') if t.strip()]
                    result['success'] = True
                    result['window_titles'] = window_titles
                    
                    # 分析窗口标题中的AI指示器
                    ai_keywords = ['chat', 'ai', 'assistant', 'conversation', 'copilot', 'composer']
                    ai_indicators = []
                    
                    for title in window_titles:
                        title_lower = title.lower()
                        for keyword in ai_keywords:
                            if keyword in title_lower:
                                ai_indicators.append({'title': title, 'keyword': keyword})
                    
                    result['ai_indicators'] = ai_indicators
                    result['confidence'] = min(0.8, len(ai_indicators) * 0.3)
                    
                    logger.debug(f"窗口分析: {len(window_titles)} 个窗口, {len(ai_indicators)} 个AI指示器")
        
        except Exception as e:
            logger.debug(f"分析Cursor窗口失败: {e}")
        
        return result
    
    def detect_focused_element(self) -> Dict[str, Any]:
        """检测聚焦的UI元素 (方法3: 元素聚焦检测)"""
        script = '''
        tell application "System Events"
            try
                tell process "Cursor"
                    try
                        set focusedElement to focused UI element
                        set elementRole to role of focusedElement as string
                        set elementValue to ""
                        set elementDescription to ""
                        set elementTitle to ""
                        set elementHelp to ""
                        
                        try
                            set elementValue to value of focusedElement as string
                        end try
                        
                        try
                            set elementDescription to description of focusedElement as string
                        end try
                        
                        try
                            set elementTitle to title of focusedElement as string
                        end try
                        
                        try
                            set elementHelp to help of focusedElement as string
                        end try
                        
                        return elementRole & "|" & elementValue & "|" & elementDescription & "|" & elementTitle & "|" & elementHelp
                    on error
                        return "no_focus||||"
                    end try
                end tell
            on error errMsg
                return "error|" & errMsg & "|||"
            end try
        end tell
        '''
        
        result = {
            'method': DetectionMethod.ELEMENT_FOCUS.value,
            'success': False,
            'element_info': {},
            'is_input_element': False,
            'ai_likelihood': 0.0,
            'confidence': 0.0
        }
        
        try:
            proc_result = subprocess.run(['osascript', '-e', script], 
                                       capture_output=True, text=True, timeout=2)
            
            if proc_result.returncode == 0:
                output = proc_result.stdout.strip()
                parts = output.split('|')
                
                if len(parts) >= 5:
                    role, value, description, title, help_text = parts[:5]
                    
                    result['success'] = True
                    result['element_info'] = {
                        'role': role,
                        'value': value,
                        'description': description,
                        'title': title,
                        'help': help_text
                    }
                    
                    # 判断是否为输入元素
                    input_roles = ['text field', 'text area', 'combo box']
                    result['is_input_element'] = any(input_role in role.lower() for input_role in input_roles)
                    
                    # 分析AI相关性
                    all_text = f"{role} {value} {description} {title} {help_text}".lower()
                    
                    ai_keywords = ['chat', 'message', 'ask', 'help', 'input', 'prompt', 'ai', 'assistant', 
                                 'generate', 'explain', 'code', 'command', 'search']
                    
                    ai_matches = [keyword for keyword in ai_keywords if keyword in all_text]
                    
                    if result['is_input_element']:
                        result['ai_likelihood'] = min(1.0, 0.3 + len(ai_matches) * 0.2)
                        result['confidence'] = result['ai_likelihood'] * 0.8
                    else:
                        result['ai_likelihood'] = min(0.5, len(ai_matches) * 0.1)
                        result['confidence'] = result['ai_likelihood'] * 0.5
                    
                    logger.debug(f"聚焦元素: {role}, AI可能性: {result['ai_likelihood']:.2f}")
        
        except Exception as e:
            logger.debug(f"检测聚焦元素失败: {e}")
        
        return result
    
    def heuristic_analysis(self, previous_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """启发式分析 (方法4: 综合启发式判断)"""
        result = {
            'method': DetectionMethod.HEURISTIC.value,
            'success': True,
            'factors': {},
            'confidence': 0.0
        }
        
        # 分析之前的检测结果
        frontmost_result = next((r for r in previous_results if r.get('method') == DetectionMethod.PROCESS_FOCUS.value), {})
        window_result = next((r for r in previous_results if r.get('method') == DetectionMethod.WINDOW_ANALYSIS.value), {})
        element_result = next((r for r in previous_results if r.get('method') == DetectionMethod.ELEMENT_FOCUS.value), {})
        
        # 因子1: Cursor是否在前台
        cursor_frontmost = frontmost_result.get('is_cursor_front', False)
        result['factors']['cursor_frontmost'] = cursor_frontmost
        
        # 因子2: 窗口中是否有AI指示器
        ai_windows = len(window_result.get('ai_indicators', []))
        result['factors']['ai_windows_count'] = ai_windows
        
        # 因子3: 聚焦元素是否为输入框
        is_input_focused = element_result.get('is_input_element', False)
        result['factors']['input_focused'] = is_input_focused
        
        # 因子4: AI相关性评分
        ai_likelihood = element_result.get('ai_likelihood', 0.0)
        result['factors']['ai_likelihood'] = ai_likelihood
        
        # 启发式规则计算总置信度
        confidence = 0.0
        
        if cursor_frontmost:
            confidence += 0.3
        
        if ai_windows > 0:
            confidence += min(0.4, ai_windows * 0.2)
        
        if is_input_focused:
            confidence += 0.3
            if ai_likelihood > 0.5:
                confidence += 0.2
        
        # 历史一致性检查
        if len(self.detection_history) > 0:
            recent_detections = self.detection_history[-3:]  # 最近3次检测
            positive_rate = sum(1 for d in recent_detections if d.get('is_ai_dialog_active', False)) / len(recent_detections)
            
            if positive_rate > 0.5:
                confidence += 0.1
            
        result['confidence'] = min(1.0, confidence)
        
        logger.debug(f"启发式分析: 置信度 {result['confidence']:.2f}, 因子: {result['factors']}")
        
        return result
    
    def comprehensive_detection(self) -> Dict[str, Any]:
        """综合检测方法"""
        self._update_cursor_pids()
        
        results = {
            'timestamp': time.time(),
            'cursor_running': len(self.cursor_pids) > 0,
            'detection_methods': [],
            'is_ai_dialog_active': False,
            'overall_confidence': 0.0,
            'primary_evidence': [],
            'details': {}
        }
        
        if not results['cursor_running']:
            results['details']['error'] = 'Cursor未运行'
            return results
        
        # 执行各种检测方法
        detection_results = []
        
        # 方法1: 前台应用检测
        frontmost_result = self.detect_frontmost_app()
        detection_results.append(frontmost_result)
        results['detection_methods'].append(frontmost_result)
        
        # 方法2: 窗口分析
        window_result = self.analyze_cursor_windows()
        detection_results.append(window_result)
        results['detection_methods'].append(window_result)
        
        # 方法3: 聚焦元素检测
        element_result = self.detect_focused_element()
        detection_results.append(element_result)
        results['detection_methods'].append(element_result)
        
        # 方法4: 启发式分析
        heuristic_result = self.heuristic_analysis(detection_results)
        detection_results.append(heuristic_result)
        results['detection_methods'].append(heuristic_result)
        
        # 计算整体置信度 (加权平均)
        weights = {
            DetectionMethod.PROCESS_FOCUS.value: 0.2,
            DetectionMethod.WINDOW_ANALYSIS.value: 0.3,
            DetectionMethod.ELEMENT_FOCUS.value: 0.3,
            DetectionMethod.HEURISTIC.value: 0.2
        }
        
        total_confidence = 0.0
        total_weight = 0.0
        
        for method_result in detection_results:
            method = method_result.get('method')
            confidence = method_result.get('confidence', 0.0)
            weight = weights.get(method, 0.0)
            
            if method_result.get('success', False):
                total_confidence += confidence * weight
                total_weight += weight
        
        results['overall_confidence'] = total_confidence / total_weight if total_weight > 0 else 0.0
        
        # 判断AI对话框是否活跃 (阈值可调整)
        results['is_ai_dialog_active'] = results['overall_confidence'] >= 0.6
        
        # 收集主要证据
        if frontmost_result.get('is_cursor_front'):
            results['primary_evidence'].append('Cursor是前台应用')
        
        if window_result.get('ai_indicators'):
            results['primary_evidence'].append(f'检测到AI相关窗口: {len(window_result["ai_indicators"])}个')
        
        if element_result.get('is_input_element') and element_result.get('ai_likelihood', 0) > 0.5:
            results['primary_evidence'].append('聚焦在可能的AI输入框')
        
        # 保存详细信息
        results['details'] = {
            'frontmost_app': frontmost_result.get('app_name', ''),
            'window_count': len(window_result.get('window_titles', [])),
            'focused_element': element_result.get('element_info', {}),
            'heuristic_factors': heuristic_result.get('factors', {})
        }
        
        # 更新历史记录
        self.detection_history.append(results)
        if len(self.detection_history) > 10:  # 保持最近10次记录
            self.detection_history.pop(0)
        
        self.last_detection_result = results
        
        return results
    
    def monitor(self, callback: Optional[Callable] = None, interval: float = 1.0, 
                min_confidence: float = 0.6, verbose: bool = True):
        """持续监控AI对话框状态"""
        logger.info(f"🔍 开始监控Cursor AI对话框状态 (置信度阈值: {min_confidence})")
        
        last_state = False
        state_change_count = 0
        
        try:
            while True:
                result = self.comprehensive_detection()
                
                current_state = result['is_ai_dialog_active']
                confidence = result['overall_confidence']
                
                # 状态变化时的处理
                if current_state != last_state:
                    state_change_count += 1
                    
                    if current_state:
                        logger.info(f"🎯 检测到AI对话框活动! (置信度: {confidence:.2f})")
                        if verbose and result['primary_evidence']:
                            logger.info(f"   证据: {', '.join(result['primary_evidence'])}")
                    else:
                        logger.info(f"📤 AI对话框活动结束 (置信度: {confidence:.2f})")
                    
                    if callback:
                        callback(result)
                    
                    last_state = current_state
                
                # 定期输出状态 (每30次检测)
                elif verbose and state_change_count % 30 == 0:
                    status = "活跃" if current_state else "非活跃"
                    logger.debug(f"📊 状态: {status}, 置信度: {confidence:.2f}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info(f"\n👋 监控已停止 (共检测到 {state_change_count} 次状态变化)")

def main():
    """主函数"""
    detector = CursorDialogDetector()
    
    print("🔍 Cursor AI对话框检测器 - 最终版")
    print("="*50)
    
    # 执行单次检测
    result = detector.comprehensive_detection()
    
    print(f"Cursor运行状态: {result['cursor_running']}")
    print(f"AI对话框活跃: {result['is_ai_dialog_active']}")
    print(f"整体置信度: {result['overall_confidence']:.2f}")
    
    if result['primary_evidence']:
        print(f"主要证据: {', '.join(result['primary_evidence'])}")
    
    # 显示各方法的详细结果
    print(f"\n各检测方法结果:")
    for method_result in result['detection_methods']:
        method_name = method_result['method']
        success = method_result.get('success', False)
        confidence = method_result.get('confidence', 0.0)
        print(f"  {method_name}: {'✅' if success else '❌'} (置信度: {confidence:.2f})")
    
    # 询问是否开始监控
    try:
        print(f"\n详细信息:")
        details = result['details']
        print(f"  前台应用: {details.get('frontmost_app', 'N/A')}")
        print(f"  窗口数量: {details.get('window_count', 0)}")
        
        focused = details.get('focused_element', {})
        if focused.get('role'):
            print(f"  聚焦元素: {focused['role']} - {focused.get('description', 'N/A')}")
        
        response = input("\n开始持续监控? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            
            def detection_callback(detection_result):
                print(f"📍 状态变化: {'活跃' if detection_result['is_ai_dialog_active'] else '非活跃'} "
                      f"(置信度: {detection_result['overall_confidence']:.2f})")
            
            detector.monitor(callback=detection_callback, interval=0.5, verbose=False)
            
    except (KeyboardInterrupt, EOFError):
        print("\n👋 检测结束")

if __name__ == "__main__":
    main()