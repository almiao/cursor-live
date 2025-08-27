#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cursor聚焦检测调试脚本
增强的调试工具，用于排查Accessibility API问题
"""

import logging
import time
import sys
import traceback
from typing import Optional, Dict, Any

# 设置详细的日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 尝试导入Accessibility相关模块
try:
    from ApplicationServices import (
        AXUIElementCreateSystemWide,
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
        kAXErrorSuccess
    )
    ACCESSIBILITY_AVAILABLE = True
    logger.info("✅ ApplicationServices导入成功")
except ImportError as e:
    logger.error(f"❌ ApplicationServices导入失败: {e}")
    ACCESSIBILITY_AVAILABLE = False

try:
    import psutil
    PSUTIL_AVAILABLE = True
    logger.info("✅ psutil导入成功")
except ImportError as e:
    logger.error(f"❌ psutil导入失败: {e}")
    PSUTIL_AVAILABLE = False

class EnhancedCursorDebugger:
    """增强的Cursor调试器"""
    
    def __init__(self):
        self.cursor_pids = set()
        self.debug_info = {}
    
    def check_system_requirements(self) -> Dict[str, Any]:
        """检查系统要求和权限"""
        results = {
            'accessibility_available': ACCESSIBILITY_AVAILABLE,
            'psutil_available': PSUTIL_AVAILABLE,
            'accessibility_trusted': False,
            'cursor_running': False,
            'cursor_pids': []
        }
        
        logger.info("=== 系统要求检查 ===")
        
        # 检查Accessibility权限
        if ACCESSIBILITY_AVAILABLE:
            try:
                results['accessibility_trusted'] = AXIsProcessTrusted()
                if results['accessibility_trusted']:
                    logger.info("✅ Accessibility权限已授权")
                else:
                    logger.warning("⚠️  Accessibility权限未授权")
                    logger.warning("请在 系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能 中添加此应用")
            except Exception as e:
                logger.error(f"❌ 检查Accessibility权限失败: {e}")
        
        # 检查Cursor进程
        if PSUTIL_AVAILABLE:
            try:
                for proc in psutil.process_iter(['pid', 'name', 'exe']):
                    try:
                        name = proc.info['name'].lower()
                        if 'cursor' in name:
                            results['cursor_pids'].append({
                                'pid': proc.info['pid'],
                                'name': proc.info['name'],
                                'exe': proc.info.get('exe', 'N/A')
                            })
                            self.cursor_pids.add(proc.info['pid'])
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                results['cursor_running'] = len(results['cursor_pids']) > 0
                
                if results['cursor_running']:
                    logger.info(f"✅ 找到 {len(results['cursor_pids'])} 个Cursor进程:")
                    for proc_info in results['cursor_pids']:
                        logger.info(f"  - PID: {proc_info['pid']}, 名称: {proc_info['name']}")
                else:
                    logger.warning("⚠️  未找到Cursor进程，请确保Cursor正在运行")
                    
            except Exception as e:
                logger.error(f"❌ 检查Cursor进程失败: {e}")
        
        return results
    
    def get_focused_element_detailed(self) -> Dict[str, Any]:
        """获取详细的聚焦元素信息"""
        result = {
            'success': False,
            'element': None,
            'error': None,
            'element_info': {}
        }
        
        if not ACCESSIBILITY_AVAILABLE:
            result['error'] = 'Accessibility API不可用'
            return result
        
        try:
            logger.debug("获取系统级UI元素...")
            sys_element = AXUIElementCreateSystemWide()
            
            logger.debug("获取当前聚焦元素...")
            error_code, focused_element = AXUIElementCopyAttributeValue(
                sys_element,
                kAXFocusedUIElementAttribute,
                None
            )
            
            logger.debug(f"AXUIElementCopyAttributeValue返回码: {error_code}")
            
            if error_code == kAXErrorSuccess and focused_element:
                result['success'] = True
                result['element'] = focused_element
                result['element_info'] = self._get_element_detailed_info(focused_element)
                logger.info(f"✅ 成功获取聚焦元素: {result['element_info'].get('role', 'Unknown')}")
            else:
                result['error'] = f'获取聚焦元素失败，错误码: {error_code}'
                logger.warning(result['error'])
                
        except Exception as e:
            result['error'] = f'异常: {str(e)}'
            logger.error(f"❌ 获取聚焦元素异常: {e}")
            logger.debug(traceback.format_exc())
        
        return result
    
    def _get_element_detailed_info(self, element) -> Dict[str, Any]:
        """获取元素的详细信息"""
        info = {
            'pid': None,
            'role': '',
            'title': '',
            'value': '',
            'description': '',
            'identifier': '',
            'children_count': 0,
            'is_cursor': False,
            'raw_attributes': {}
        }
        
        if not element:
            return info
        
        # 获取进程ID
        try:
            info['pid'] = AXUIElementGetPid(element)
            info['is_cursor'] = info['pid'] in self.cursor_pids
            logger.debug(f"元素PID: {info['pid']}, 是否为Cursor: {info['is_cursor']}")
        except Exception as e:
            logger.debug(f"获取PID失败: {e}")
        
        # 获取所有标准属性
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
                    info['raw_attributes'][attr_name] = value
                    logger.debug(f"  {attr_name}: {info[attr_name]}")
                else:
                    logger.debug(f"  {attr_name}: 无法获取 (错误码: {error_code})")
            except Exception as e:
                logger.debug(f"获取属性 {attr_name} 失败: {e}")
        
        # 获取子元素数量
        try:
            error_code, children = AXUIElementCopyAttributeValue(element, kAXChildrenAttribute, None)
            if error_code == kAXErrorSuccess and children:
                info['children_count'] = len(children)
                logger.debug(f"  子元素数量: {info['children_count']}")
        except Exception as e:
            logger.debug(f"获取子元素失败: {e}")
        
        return info
    
    def analyze_cursor_ai_possibility(self, element_info: Dict[str, Any]) -> Dict[str, Any]:
        """分析元素是否可能是Cursor AI对话框"""
        analysis = {
            'is_cursor_process': False,
            'is_input_element': False,
            'has_ai_keywords': False,
            'confidence_score': 0.0,
            'reasons': [],
            'all_text': ''
        }
        
        if not element_info:
            return analysis
        
        # 检查是否为Cursor进程
        analysis['is_cursor_process'] = element_info.get('is_cursor', False)
        if analysis['is_cursor_process']:
            analysis['confidence_score'] += 0.4
            analysis['reasons'].append("属于Cursor进程")
        
        # 检查是否为输入元素
        role = element_info.get('role', '').lower()
        input_roles = ['axtextfield', 'axtextarea', 'axcombobox']
        analysis['is_input_element'] = role in input_roles
        if analysis['is_input_element']:
            analysis['confidence_score'] += 0.3
            analysis['reasons'].append(f"输入元素类型: {role}")
        
        # 收集所有文本信息进行关键词分析
        text_fields = [
            element_info.get('identifier', ''),
            element_info.get('title', ''),
            element_info.get('description', ''),
            element_info.get('value', '')
        ]
        all_text = ' '.join(text_fields).lower()
        analysis['all_text'] = all_text
        
        # 扩展的AI相关关键词
        ai_keywords = [
            'chat', 'ai', 'assistant', 'copilot', 'conversation',
            'message', 'input', 'prompt', 'query', 'ask',
            'composer', 'generate', 'code', 'help',
            # Cursor特定的关键词
            'cursor', 'cmd+k', 'ctrl+k'
        ]
        
        found_keywords = []
        for keyword in ai_keywords:
            if keyword in all_text:
                found_keywords.append(keyword)
        
        analysis['has_ai_keywords'] = len(found_keywords) > 0
        if analysis['has_ai_keywords']:
            analysis['confidence_score'] += 0.2 * len(found_keywords)
            analysis['reasons'].append(f"找到AI关键词: {found_keywords}")
        
        # 额外的启发式规则
        if 'placeholder' in all_text and ('ask' in all_text or 'help' in all_text):
            analysis['confidence_score'] += 0.1
            analysis['reasons'].append("疑似AI输入框占位符")
        
        return analysis
    
    def continuous_monitor(self, duration: int = 30, interval: float = 0.5):
        """连续监控聚焦状态"""
        logger.info(f"=== 开始连续监控 {duration} 秒 ===")
        
        start_time = time.time()
        last_element_info = None
        
        try:
            while time.time() - start_time < duration:
                print("\n" + "="*50)
                print(f"时间: {time.time() - start_time:.1f}s")
                
                # 获取当前聚焦元素
                focused_result = self.get_focused_element_detailed()
                
                if focused_result['success']:
                    element_info = focused_result['element_info']
                    
                    # 只在元素发生变化时打印详细信息
                    if element_info != last_element_info:
                        print(f"聚焦元素变化:")
                        print(f"  PID: {element_info.get('pid', 'N/A')}")
                        print(f"  角色: {element_info.get('role', 'N/A')}")
                        print(f"  标题: {element_info.get('title', 'N/A')}")
                        print(f"  标识符: {element_info.get('identifier', 'N/A')}")
                        print(f"  值: {element_info.get('value', 'N/A')}")
                        print(f"  是否为Cursor: {element_info.get('is_cursor', False)}")
                        
                        # 分析AI对话框可能性
                        analysis = self.analyze_cursor_ai_possibility(element_info)
                        print(f"  AI对话框可能性: {analysis['confidence_score']:.2f}")
                        print(f"  分析原因: {analysis['reasons']}")
                        
                        last_element_info = element_info.copy()
                    else:
                        print("聚焦元素无变化")
                else:
                    print(f"获取聚焦元素失败: {focused_result['error']}")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            logger.info("\n👋 监控已停止")

def main():
    """主函数"""
    print("🔍 Cursor聚焦检测调试工具")
    print("="*50)
    
    debugger = EnhancedCursorDebugger()
    
    # 检查系统要求
    requirements = debugger.check_system_requirements()
    print(f"\n系统检查结果:")
    print(f"  Accessibility可用: {requirements['accessibility_available']}")
    print(f"  Accessibility权限: {requirements['accessibility_trusted']}")
    print(f"  Cursor运行中: {requirements['cursor_running']}")
    print(f"  Cursor进程数: {len(requirements['cursor_pids'])}")
    
    if not requirements['accessibility_available']:
        print("\n❌ Accessibility API不可用，无法继续")
        return
    
    if not requirements['accessibility_trusted']:
        print("\n⚠️  需要Accessibility权限，请在系统偏好设置中授权")
        print("路径：系统偏好设置 > 安全性与隐私 > 隐私 > 辅助功能")
        return
    
    if not requirements['cursor_running']:
        print("\n⚠️  Cursor未运行，请启动Cursor后再次尝试")
        return
    
    print("\n✅ 所有检查通过，开始测试聚焦检测...")
    
    # 获取当前聚焦元素
    focused_result = debugger.get_focused_element_detailed()
    if focused_result['success']:
        print("\n当前聚焦元素:")
        element_info = focused_result['element_info']
        for key, value in element_info.items():
            if key != 'raw_attributes':
                print(f"  {key}: {value}")
        
        # 分析AI对话框可能性
        analysis = debugger.analyze_cursor_ai_possibility(element_info)
        print(f"\nAI对话框分析:")
        print(f"  可能性评分: {analysis['confidence_score']:.2f}")
        print(f"  分析原因: {analysis['reasons']}")
    else:
        print(f"❌ 无法获取聚焦元素: {focused_result['error']}")
    
    # 询问是否进行连续监控
    try:
        response = input("\n是否进行连续监控? (y/N): ").strip().lower()
        if response in ['y', 'yes']:
            duration = input("监控时长(秒，默认30): ").strip()
            try:
                duration = int(duration) if duration else 30
            except ValueError:
                duration = 30
            
            debugger.continuous_monitor(duration=duration)
    except KeyboardInterrupt:
        print("\n👋 调试已结束")

if __name__ == "__main__":
    main()