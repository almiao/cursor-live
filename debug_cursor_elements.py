#!/usr/bin/env python3
"""
Cursor UI元素调试脚本
循环打印Cursor的所有子窗口和UI元素，帮助识别对话框
"""

import time
import logging
from cursor_window_detector import CursorWindowDetector

# 设置日志级别
logging.basicConfig(
    level=logging.WARNING,  # 减少日志输出
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def search_all_buttons(elements, depth=0, max_depth=8, indent=""):
    """递归搜索所有按钮元素，特别关注AI面板切换按钮"""
    if not elements or depth > max_depth:
        return
    
    for i, element in enumerate(elements):
        try:
            # 获取基本属性
            role_error, role = AXUIElementCopyAttributeValue(element, kAXRoleAttribute, None)  # type: ignore
            element_role = role if role_error == kAXErrorSuccess else "Unknown"  # type: ignore
            
            # 只关注按钮元素
            if element_role == 'AXButton':
                title_error, title = AXUIElementCopyAttributeValue(element, kAXTitleAttribute, None)  # type: ignore
                value_error, value = AXUIElementCopyAttributeValue(element, kAXValueAttribute, None)  # type: ignore
                
                element_title = title if title_error == kAXErrorSuccess else ""  # type: ignore
                element_value = value if value_error == kAXErrorSuccess else ""  # type: ignore
                
                # 获取位置信息
                try:
                    from ApplicationServices import kAXPositionAttribute  # type: ignore
                    position_error, position = AXUIElementCopyAttributeValue(element, kAXPositionAttribute, None)
                    element_position = position if position_error == kAXErrorSuccess else None  # type: ignore
                except:
                    element_position = None
                
                # 检查是否为AI面板切换按钮
                is_toggle_ai_panel = False
                toggle_keywords = ['toggle', 'ai', 'panel', 'chat', 'assistant']
                text_to_check = f"{element_title} {element_value}".lower()
                
                # 检查位置（右上角区域）
                is_right_area = False
                if element_position:
                    try:
                        pos_str = str(element_position)
                        if 'x:' in pos_str and 'y:' in pos_str:
                            x_pos = float(pos_str.split('x:')[1].split('.')[0])
                            y_pos = float(pos_str.split('y:')[1].split('.')[0])
                            # 右上角区域判断：x > 1000 且 y < 100
                            is_right_area = x_pos > 1000 and y_pos < 100
                    except:
                        pass
                
                # 检查关键词
                has_toggle_keywords = any(keyword in text_to_check for keyword in toggle_keywords)
                
                if is_right_area or has_toggle_keywords:
                    is_toggle_ai_panel = True
                
                # 显示按钮信息
                button_info = f"按钮: {element_title}" if element_title else "按钮: (无标题)"
                if element_value:
                    button_info += f" | 值: {element_value}"
                if element_position:
                    button_info += f" | 位置: {element_position}"
                
                if is_toggle_ai_panel:
                    print(f"{indent}🚀 **找到AI面板切换按钮!** {button_info}")
                elif is_right_area:
                    print(f"{indent}📍 右上角按钮: {button_info}")
                else:
                    print(f"{indent}🔘 按钮: {button_info}")
            
            # 继续搜索子元素
            try:
                children_error, children = AXUIElementCopyAttributeValue(element, kAXChildrenAttribute, None)  # type: ignore
                if children_error == kAXErrorSuccess and children:  # type: ignore
                    search_all_buttons(children, depth + 1, max_depth, indent + "  ")
            except:
                pass
                
        except Exception as e:
            print(f"{indent}❌ 搜索按钮时出错: {e}")

def print_element_tree(elements, depth=0, max_depth=5):
    """
    递归打印UI元素树结构
    
    Args:
        elements: UI元素列表
        depth: 当前深度
        max_depth: 最大递归深度
    """
    if not elements or depth > max_depth:
        return
    
    try:
        from ApplicationServices import (  # type: ignore
            AXUIElementCopyAttributeValue,  # type: ignore
            kAXRoleAttribute,  # type: ignore
            kAXTitleAttribute,  # type: ignore
            kAXValueAttribute,  # type: ignore
            kAXChildrenAttribute,  # type: ignore
            kAXSubroleAttribute,  # type: ignore
            kAXErrorSuccess  # type: ignore
        )
        
        indent = "  " * depth
        
        for i, element in enumerate(elements):
            try:
                # 获取元素角色
                role_error, role = AXUIElementCopyAttributeValue(
                    element, 
                    kAXRoleAttribute, 
                    None
                )
                element_role = role if role_error == kAXErrorSuccess else "未知角色"
                
                # 获取元素子角色
                subrole_error, subrole = AXUIElementCopyAttributeValue(
                    element, 
                    kAXSubroleAttribute, 
                    None
                )
                element_subrole = subrole if subrole_error == kAXErrorSuccess else None
                
                # 获取元素标题
                title_error, title = AXUIElementCopyAttributeValue(
                    element, 
                    kAXTitleAttribute, 
                    None
                )
                element_title = title if title_error == kAXErrorSuccess else None
                
                # 获取元素值
                value_error, value = AXUIElementCopyAttributeValue(
                    element, 
                    kAXValueAttribute, 
                    None
                )
                element_value = value if value_error == kAXErrorSuccess else None
                
                # 获取更多属性信息
                try:
                     from ApplicationServices import (  # type: ignore
                         kAXDescriptionAttribute,  # type: ignore
                         kAXHelpAttribute,  # type: ignore
                         kAXIdentifierAttribute,  # type: ignore
                         kAXEnabledAttribute,  # type: ignore
                         kAXFocusedAttribute,  # type: ignore
                         kAXSizeAttribute,  # type: ignore
                         kAXPositionAttribute  # type: ignore
                     )
                     
                     description_error, description = AXUIElementCopyAttributeValue(
                         element, kAXDescriptionAttribute, None
                     )
                     element_description = description if description_error == kAXErrorSuccess else None
                     
                     identifier_error, identifier = AXUIElementCopyAttributeValue(
                         element, kAXIdentifierAttribute, None
                     )
                     element_identifier = identifier if identifier_error == kAXErrorSuccess else None
                     
                     enabled_error, enabled = AXUIElementCopyAttributeValue(
                         element, kAXEnabledAttribute, None
                     )
                     element_enabled = enabled if enabled_error == kAXErrorSuccess else None
                     
                     focused_error, focused = AXUIElementCopyAttributeValue(
                         element, kAXFocusedAttribute, None
                     )
                     element_focused = focused if focused_error == kAXErrorSuccess else None
                     
                     size_error, size = AXUIElementCopyAttributeValue(
                         element, kAXSizeAttribute, None
                     )
                     element_size = size if size_error == kAXErrorSuccess else None
                     
                     position_error, position = AXUIElementCopyAttributeValue(
                         element, kAXPositionAttribute, None
                     )
                     element_position = position if position_error == kAXErrorSuccess else None
                     
                except ImportError:
                    element_description = None
                    element_identifier = None
                    element_enabled = None
                    element_focused = None
                    element_size = None
                    element_position = None
                
                # 构建显示信息
                info_parts = [f"[{i}] {element_role}"]
                if element_subrole:
                    info_parts.append(f"({element_subrole})")
                if element_title:
                    info_parts.append(f"标题: '{element_title}'")
                if element_value:
                    # 限制值的长度
                    value_str = str(element_value)
                    if len(value_str) > 50:
                        value_str = value_str[:47] + "..."
                    info_parts.append(f"值: '{value_str}'")
                if element_description:
                    info_parts.append(f"描述: '{element_description}'")
                if element_identifier:
                    info_parts.append(f"标识符: '{element_identifier}'")
                if element_enabled is not None:
                    info_parts.append(f"启用: {element_enabled}")
                if element_focused is not None:
                    info_parts.append(f"聚焦: {element_focused}")
                if element_size:
                    info_parts.append(f"大小: {element_size}")
                if element_position:
                    info_parts.append(f"位置: {element_position}")
                
                print(f"{indent}{' | '.join(info_parts)}")
                
                # 检查是否可能是对话框相关元素
                dialog_keywords = ['dialog', 'sheet', 'panel', 'popup', 'menu', 'textfield', 'textarea']
                ai_keywords = ['ai', 'chat', 'dialog', 'assistant', 'copilot', 'send', 'message', 'prompt', 'toggle']
                
                is_dialog_element = False
                is_ai_element = False
                is_toggle_ai_panel = False
                
                # 检查是否为AI面板切换按钮
                if element_role == 'AXButton':
                    toggle_keywords = ['toggle', 'ai', 'panel', 'chat', 'assistant']
                    text_to_check = f"{element_title} {element_value} {element_description} {element_identifier}".lower()
                    
                    # 检查位置（右上角区域）
                    is_right_area = False
                    if element_position:
                        try:
                            # 解析位置信息，寻找右上角区域的按钮
                            pos_str = str(element_position)
                            if 'x:' in pos_str and 'y:' in pos_str:
                                x_pos = float(pos_str.split('x:')[1].split('.')[0])
                                y_pos = float(pos_str.split('y:')[1].split('.')[0])
                                # 右上角区域判断：x > 1000 且 y < 100
                                is_right_area = x_pos > 1000 and y_pos < 100
                        except:
                            pass
                    
                    # 检查关键词
                    has_toggle_keywords = any(keyword in text_to_check for keyword in toggle_keywords)
                    
                    if is_right_area or has_toggle_keywords:
                        is_toggle_ai_panel = True
                
                # 检查角色
                if element_role and any(keyword in str(element_role).lower() for keyword in dialog_keywords):
                    is_dialog_element = True
                
                # 检查标题
                if element_title:
                    title_lower = str(element_title).lower()
                    if any(keyword in title_lower for keyword in ai_keywords):
                        is_ai_element = True
                    elif any(keyword in title_lower for keyword in dialog_keywords):
                        is_dialog_element = True
                
                # 检查值
                if element_value:
                    value_lower = str(element_value).lower()
                    if any(keyword in value_lower for keyword in ai_keywords):
                        is_ai_element = True
                    elif any(keyword in value_lower for keyword in dialog_keywords):
                        is_dialog_element = True
                
                # 显示标记
                if is_toggle_ai_panel:
                    print(f"{indent}  🚀 **AI面板切换按钮!** (状态: {element_value})")
                elif is_ai_element:
                    print(f"{indent}  🎯 **可能的AI对话框元素!**")
                elif is_dialog_element:
                    print(f"{indent}  ⭐ 可能的对话框相关元素")
                elif element_role in ['AXButton', 'AXTextField', 'AXTextArea']:
                    print(f"{indent}  🔘 交互元素")
                elif element_role == 'AXGroup':
                    print(f"{indent}  📦 组元素 (可能包含重要内容)")
                    # 对于AXGroup元素，显示更多详细信息
                    if element_identifier or element_description:
                        print(f"{indent}      详细信息可能有助于识别功能")
                
                # 获取子元素
                children_error, children = AXUIElementCopyAttributeValue(
                    element, 
                    kAXChildrenAttribute, 
                    None
                )
                
                if children_error == kAXErrorSuccess and children:
                    child_count = len(children)
                    print(f"{indent}  └─ 子元素数量: {child_count}")
                    
                    # 对于AXGroup元素，特别关注其子元素
                    if element_role == 'AXGroup' and child_count > 0:
                        print(f"{indent}      AXGroup子元素预览:")
                        # 显示前几个子元素的基本信息
                        for j, child in enumerate(children[:3]):
                            try:
                                child_role_error, child_role = AXUIElementCopyAttributeValue(
                                    child, kAXRoleAttribute, None
                                )
                                child_title_error, child_title = AXUIElementCopyAttributeValue(
                                    child, kAXTitleAttribute, None
                                )
                                child_role_str = child_role if child_role_error == kAXErrorSuccess else "未知"
                                child_title_str = child_title if child_title_error == kAXErrorSuccess else ""
                                title_info = f" - '{child_title_str}'" if child_title_str else ""
                                print(f"{indent}        [{j}] {child_role_str}{title_info}")
                            except:
                                print(f"{indent}        [{j}] 无法获取子元素信息")
                        if child_count > 3:
                            print(f"{indent}        ... 还有 {child_count - 3} 个子元素")
                    
                    if depth < max_depth and child_count > 0:
                        print_element_tree(children, depth + 1, max_depth)
                
                # 对于主窗口组，特别搜索所有按钮元素
                 if depth == 1 and element_role == 'AXGroup' and children:
                     print(f"{indent}  🔍 深度搜索所有按钮元素...")
                     search_all_buttons(children, depth + 1, max_depth + 2, indent + "    ")
                
            except Exception as e:
                print(f"{indent}[{i}] 处理元素时出错: {e}")
                
    except ImportError:
        print("无法导入ApplicationServices框架")
    except Exception as e:
        print(f"打印元素树时出错: {e}")

def debug_cursor_elements():
    """
    主调试函数：循环检测并打印Cursor的UI元素
    """
    detector = CursorWindowDetector()
    
    print("=" * 80)
    print("🔍 Cursor UI元素调试器 - 增强版")
    print("📝 寻找AI对话框相关的UI元素")
    print("⌨️  按 Ctrl+C 停止监控")
    print("=" * 80)
    
    try:
        iteration = 0
        while True:
            iteration += 1
            print(f"\n{'='*60}")
            print(f"🔄 第 {iteration} 次检测 - {time.strftime('%H:%M:%S')}")
            print(f"{'='*60}")
            
            # 检查Cursor是否运行
            cursor_pid = detector.find_cursor_process()
            if not cursor_pid:
                print("❌ 未找到Cursor进程，请确保Cursor正在运行")
                time.sleep(3)
                continue
            
            print(f"✅ Cursor进程 (PID: {cursor_pid})")
            
            # 获取应用引用
            if not detector.get_cursor_app_ref():
                print("❌ 无法获取Cursor应用引用")
                time.sleep(3)
                continue
            
            # 获取窗口列表
            windows = detector.get_cursor_windows()
            if not windows:
                print("❌ 未找到Cursor窗口")
                time.sleep(3)
                continue
            
            print(f"\n📋 发现 {len(windows)} 个Cursor窗口:")
            
            for idx, window_info in enumerate(windows):
                print(f"\n🪟 窗口 {idx+1}: {window_info['title']} ({window_info['role']})")
                print("─" * 70)
                
                try:
                    from ApplicationServices import (  # type: ignore
                        AXUIElementCopyAttributeValue,  # type: ignore
                        kAXChildrenAttribute,  # type: ignore
                        kAXErrorSuccess  # type: ignore
                    )
                    
                    # 获取窗口的子元素
                    children_error, children = AXUIElementCopyAttributeValue(
                        window_info['element'], 
                        kAXChildrenAttribute, 
                        None
                    )
                    
                    if children_error == kAXErrorSuccess and children:
                        print(f"📦 窗口子元素 ({len(children)} 个):")
                        print_element_tree(children, depth=0, max_depth=4)
                    else:
                        print("📦 窗口没有子元素或无法访问")
                        
                except ImportError:
                    print("❌ 无法导入ApplicationServices框架")
                except Exception as e:
                    print(f"❌ 分析窗口元素时出错: {e}")
            
            print(f"\n⏱️  等待5秒后继续检测... (按Ctrl+C停止)")
            time.sleep(5)
            
    except KeyboardInterrupt:
        print("\n\n👋 调试器已停止")
        print("💡 提示: 查找标记为 🎯 的元素，这些最可能是AI对话框相关的UI组件")
    except Exception as e:
        print(f"\n❌ 调试器运行出错: {e}")

if __name__ == "__main__":
    debug_cursor_elements()