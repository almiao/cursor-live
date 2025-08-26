#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
专门搜索Cursor应用程序右上角区域的UI元素
"""

import logging
import time
from cursor_window_detector import CursorWindowDetector
from Cocoa import *
from ApplicationServices import *

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_all_elements_in_area(element, min_x=1200, max_x=2000, min_y=0, max_y=100, depth=0, max_depth=20):
    """
    获取指定区域内的所有UI元素
    """
    elements_found = []
    
    if depth > max_depth:
        return elements_found
    
    try:
        # 获取元素位置
        position = getattr(element, 'AXPosition', None)
        if position:
            x_pos = position.x
            y_pos = position.y
            
            # 检查是否在目标区域内
            if min_x <= x_pos <= max_x and min_y <= y_pos <= max_y:
                role = getattr(element, 'AXRole', 'Unknown')
                title = getattr(element, 'AXTitle', '')
                value = getattr(element, 'AXValue', '')
                description = getattr(element, 'AXDescription', '')
                
                element_info = {
                    'role': role,
                    'position': (x_pos, y_pos),
                    'title': title,
                    'value': value,
                    'description': description,
                    'depth': depth
                }
                elements_found.append(element_info)
                
                logger.info(f"🎯 找到右上角元素 [{role}]: 位置({x_pos}, {y_pos}) | 标题:'{title}' | 值:'{value}' | 描述:'{description}' | 深度:{depth}")
        
        # 递归搜索子元素
        children = getattr(element, 'AXChildren', [])
        if children:
            for child in children:
                child_elements = get_all_elements_in_area(child, min_x, max_x, min_y, max_y, depth + 1, max_depth)
                elements_found.extend(child_elements)
                
    except Exception as e:
        logger.debug(f"处理元素时出错 (深度 {depth}): {e}")
    
    return elements_found

def main():
    """
    主函数：搜索Cursor右上角的UI元素
    """
    logger.info("🔍 开始搜索Cursor应用程序右上角的UI元素...")
    
    detector = CursorWindowDetector()
    
    while True:
        try:
            # 获取Cursor窗口
            windows = detector.get_cursor_windows()
            
            if not windows:
                logger.warning("⚠️ 未找到Cursor窗口")
                time.sleep(2)
                continue
            
            logger.info(f"📱 找到 {len(windows)} 个Cursor窗口")
            
            for window_info in windows:
                window_element = window_info['element']
                window_title = window_info['title']
                
                logger.info(f"🔍 搜索窗口: {window_title}")
                
                # 搜索右上角区域的元素
                right_corner_elements = get_all_elements_in_area(
                    window_element,
                    min_x=1200,  # 右侧区域
                    max_x=2000,  # 窗口右边界
                    min_y=0,     # 顶部
                    max_y=100,   # 上方区域
                    max_depth=25
                )
                
                if right_corner_elements:
                    logger.info(f"✅ 在窗口 '{window_title}' 中找到 {len(right_corner_elements)} 个右上角元素")
                    
                    # 按深度排序显示
                    right_corner_elements.sort(key=lambda x: x['depth'])
                    
                    for elem in right_corner_elements:
                        if 'ai' in elem['title'].lower() or 'toggle' in elem['title'].lower() or 'pane' in elem['title'].lower():
                            logger.info(f"🚀 **可能的AI面板切换按钮**: {elem}")
                        elif 'setting' in elem['title'].lower() or 'gear' in elem['title'].lower():
                            logger.info(f"⚙️ **设置按钮**: {elem}")
                else:
                    logger.info(f"❌ 在窗口 '{window_title}' 中未找到右上角元素")
            
            logger.info("\n⏱️ 等待5秒后继续检测... (按Ctrl+C停止)")
            time.sleep(5)
            
        except KeyboardInterrupt:
            logger.info("\n👋 用户中断，程序退出")
            break
        except Exception as e:
            logger.error(f"❌ 搜索过程中出错: {e}")
            time.sleep(2)

if __name__ == "__main__":
    main()