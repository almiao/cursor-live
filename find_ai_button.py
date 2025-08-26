#!/usr/bin/env python3
"""
专门搜索Cursor中AI面板切换按钮的脚本
"""

import time
import logging
from cursor_window_detector import CursorWindowDetector

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def search_ai_toggle_button():
    """搜索AI面板切换按钮"""
    try:
        from ApplicationServices import (  # type: ignore
            AXUIElementCopyAttributeValue,  # type: ignore
            kAXRoleAttribute,  # type: ignore
            kAXTitleAttribute,  # type: ignore
            kAXValueAttribute,  # type: ignore
            kAXChildrenAttribute,  # type: ignore
            kAXPositionAttribute,  # type: ignore
            kAXSizeAttribute,  # type: ignore
            kAXErrorSuccess  # type: ignore
        )
    except ImportError:
        logger.error("无法导入ApplicationServices模块")
        return
    
    detector = CursorWindowDetector()
    
    def search_buttons_recursive(elements, depth=0, max_depth=15, path=""):
        """递归搜索所有按钮元素"""
        if not elements or depth > max_depth:
            return
        
        logger.info(f"搜索深度 {depth}: 检查 {len(elements)} 个元素")
        
        for i, element in enumerate(elements):
            try:
                # 获取元素角色
                role_error, role = AXUIElementCopyAttributeValue(element, kAXRoleAttribute, None)
                if role_error != kAXErrorSuccess:
                    logger.debug(f"无法获取元素 {i} 的角色")
                    continue
                
                current_path = f"{path}[{i}]{role}"
                logger.debug(f"检查元素: {current_path}")
                
                # 如果是按钮，检查详细信息
                if role == 'AXButton':
                    # 获取标题
                    title_error, title = AXUIElementCopyAttributeValue(element, kAXTitleAttribute, None)
                    element_title = title if title_error == kAXErrorSuccess else ""
                    
                    # 获取值
                    value_error, value = AXUIElementCopyAttributeValue(element, kAXValueAttribute, None)
                    element_value = value if value_error == kAXErrorSuccess else ""
                    
                    # 获取位置
                    position_error, position = AXUIElementCopyAttributeValue(element, kAXPositionAttribute, None)
                    element_position = position if position_error == kAXErrorSuccess else None
                    
                    # 获取大小
                    size_error, size = AXUIElementCopyAttributeValue(element, kAXSizeAttribute, None)
                    element_size = size if size_error == kAXErrorSuccess else None
                    
                    # 分析位置
                    x_pos = y_pos = 0
                    if element_position:
                        try:
                            pos_str = str(element_position)
                            if 'x:' in pos_str and 'y:' in pos_str:
                                x_pos = float(pos_str.split('x:')[1].split('.')[0])
                                y_pos = float(pos_str.split('y:')[1].split('.')[0])
                        except:
                            pass
                    
                    # 获取更多元素属性信息
                    element_description = getattr(element, 'AXDescription', '')
                    element_help = getattr(element, 'AXHelp', '')
                    element_identifier = getattr(element, 'AXIdentifier', '')
                    element_role_description = getattr(element, 'AXRoleDescription', '')
                    element_subrole = getattr(element, 'AXSubrole', '')
                    element_enabled = getattr(element, 'AXEnabled', None)
                    element_focused = getattr(element, 'AXFocused', None)
                    
                    # 显示完整的按钮信息
                    button_info = f"路径: {current_path}"
                    if element_title:
                        button_info += f"\n  标题: '{element_title}'"
                    if element_value:
                        button_info += f"\n  值: '{element_value}'"
                    if element_description:
                        button_info += f"\n  描述: '{element_description}'"
                    if element_help:
                        button_info += f"\n  帮助: '{element_help}'"
                    if element_identifier:
                        button_info += f"\n  标识符: '{element_identifier}'"
                    if element_role_description:
                        button_info += f"\n  角色描述: '{element_role_description}'"
                    if element_subrole:
                        button_info += f"\n  子角色: '{element_subrole}'"
                    if element_enabled is not None:
                        button_info += f"\n  启用状态: {element_enabled}"
                    if element_focused is not None:
                        button_info += f"\n  焦点状态: {element_focused}"
                    if element_position:
                        button_info += f"\n  位置: ({x_pos}, {y_pos})"
                    if element_size:
                        button_info += f"\n  大小: {element_size}"
                    
                    # 🔴 断点位置：显示所有按钮信息并等待用户确认
                    logger.info(f"🔍 发现按钮: {button_info}")
                    
                    # 人工断点：让用户检查每个按钮
                    user_input = input(f"\n📍 断点 - 发现按钮:\n{button_info}\n\n请选择操作:\n1. 继续 (回车)\n2. 标记为AI面板切换按钮 (输入 'ai')\n3. 标记为设置按钮 (输入 'settings')\n4. 退出 (输入 'quit')\n\n你的选择: ")
                    
                    if user_input.lower() == 'quit':
                        logger.info("👋 用户选择退出")
                        return
                    elif user_input.lower() == 'ai':
                        logger.info(f"🚀 **用户标记为AI面板切换按钮!** {button_info}")
                        # 这里可以保存按钮信息或执行点击操作
                    elif user_input.lower() == 'settings':
                        logger.info(f"⚙️ **用户标记为设置按钮!** {button_info}")
                    else:
                        logger.info("➡️ 继续搜索下一个按钮...")
                
                # 继续搜索子元素（跳过菜单栏以提高效率）
                if role != 'AXMenuBar':
                    children_error, children = AXUIElementCopyAttributeValue(element, kAXChildrenAttribute, None)
                    if children_error == kAXErrorSuccess and children:
                        search_buttons_recursive(children, depth + 1, max_depth, current_path + "/")
                
                # 特别检查所有可交互元素（不仅仅是按钮）
                if role in ['AXButton', 'AXMenuButton', 'AXPopUpButton', 'AXCheckBox', 'AXRadioButton', 'AXLink', 'AXImage', 'AXGroup', 'AXScrollArea']:
                    # 获取位置信息
                    position_error, position = AXUIElementCopyAttributeValue(element, kAXPositionAttribute, None)
                    if position_error == kAXErrorSuccess and position:
                        try:
                            pos_str = str(position)
                            if 'x:' in pos_str and 'y:' in pos_str:
                                x_pos = float(pos_str.split('x:')[1].split('.')[0])
                                y_pos = float(pos_str.split('y:')[1].split('.')[0])
                                
                                # 专门寻找右上角区域的所有可交互元素
                                if x_pos > 1200 and y_pos < 100:
                                    # 获取所有可能的属性
                                    title_error, title = AXUIElementCopyAttributeValue(element, kAXTitleAttribute, None)
                                    element_title = title if title_error == kAXErrorSuccess else ""
                                    
                                    value_error, value = AXUIElementCopyAttributeValue(element, kAXValueAttribute, None)
                                    element_value = value if value_error == kAXErrorSuccess else ""
                                    
                                    # 尝试获取描述属性
                                    try:
                                        desc_error, description = AXUIElementCopyAttributeValue(element, 'AXDescription', None)
                                        element_description = description if desc_error == kAXErrorSuccess else ""
                                    except:
                                        element_description = ""
                                    
                                    # 尝试获取帮助属性
                                    try:
                                        help_error, help_text = AXUIElementCopyAttributeValue(element, 'AXHelp', None)
                                        element_help = help_text if help_error == kAXErrorSuccess else ""
                                    except:
                                        element_help = ""
                                    
                                    all_text = f"{element_title} {element_value} {element_description} {element_help}".lower()
                                    
                                    logger.info(f"🎯 **右上角可交互元素** [{role}]: 位置({x_pos}, {y_pos}) | 标题:'{element_title}' | 值:'{element_value}' | 描述:'{element_description}' | 帮助:'{element_help}'")
                        except Exception as e:
                            logger.debug(f"解析位置信息失败: {e}")
                    
            except Exception as e:
                logger.debug(f"搜索元素时出错: {e}")
    
    while True:
        try:
            logger.info("\n" + "="*60)
            logger.info("🔍 开始搜索Cursor中的AI面板切换按钮...")
            
            # 获取Cursor窗口
            windows_info = detector.get_cursor_windows()
            if not windows_info:
                logger.warning("未找到Cursor窗口")
                time.sleep(5)
                continue
            
            logger.info(f"找到 {len(windows_info)} 个Cursor窗口")
            
            # 直接使用窗口信息中的element
            windows = [w['element'] for w in windows_info if w.get('element')]
            
            if not windows:
                logger.warning("没有可用的窗口引用")
                time.sleep(5)
                continue
                
            for i, window in enumerate(windows):
                logger.info(f"\n🪟 检查窗口 {i+1}:")
                
                # 获取窗口的所有子元素
                try:
                    children_error, children = AXUIElementCopyAttributeValue(window, kAXChildrenAttribute, None)
                    if children_error == kAXErrorSuccess and children:
                        logger.info(f"窗口有 {len(children)} 个直接子元素")
                        search_buttons_recursive(children, 0, 8, "窗口/")
                    else:
                        logger.warning("无法获取窗口子元素")
                except Exception as e:
                    logger.error(f"获取窗口子元素时出错: {e}")
            
            logger.info("\n⏱️ 等待5秒后继续检测... (按Ctrl+C停止)")
            time.sleep(5)
            
        except KeyboardInterrupt:
            logger.info("\n👋 检测已停止")
            break
        except Exception as e:
            logger.error(f"检测过程中出错: {e}")
            time.sleep(5)

if __name__ == "__main__":
    search_ai_toggle_button()