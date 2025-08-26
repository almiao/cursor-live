#!/usr/bin/env python3
"""
性能测试脚本：比较新旧检测方法的性能
"""

import time
import requests
import statistics
from typing import List

def test_api_performance(url: str, num_requests: int = 10) -> List[float]:
    """测试API响应时间
    
    Args:
        url: API端点URL
        num_requests: 请求次数
        
    Returns:
        响应时间列表（毫秒）
    """
    response_times = []
    
    print(f"开始测试 {url}，共 {num_requests} 次请求...")
    
    for i in range(num_requests):
        start_time = time.time()
        try:
            response = requests.get(url, timeout=5)
            end_time = time.time()
            
            if response.status_code == 200:
                response_time_ms = (end_time - start_time) * 1000
                response_times.append(response_time_ms)
                print(f"请求 {i+1}: {response_time_ms:.2f}ms")
            else:
                print(f"请求 {i+1}: 失败 (状态码: {response.status_code})")
                
        except Exception as e:
            print(f"请求 {i+1}: 异常 - {e}")
            
        # 避免请求过于频繁
        time.sleep(0.1)
    
    return response_times

def analyze_performance(response_times: List[float]) -> None:
    """分析性能数据
    
    Args:
        response_times: 响应时间列表
    """
    if not response_times:
        print("没有有效的响应时间数据")
        return
        
    avg_time = statistics.mean(response_times)
    min_time = min(response_times)
    max_time = max(response_times)
    median_time = statistics.median(response_times)
    
    print(f"\n=== 性能分析结果 ===")
    print(f"总请求数: {len(response_times)}")
    print(f"平均响应时间: {avg_time:.2f}ms")
    print(f"最快响应时间: {min_time:.2f}ms")
    print(f"最慢响应时间: {max_time:.2f}ms")
    print(f"中位数响应时间: {median_time:.2f}ms")
    
    if len(response_times) > 1:
        std_dev = statistics.stdev(response_times)
        print(f"标准差: {std_dev:.2f}ms")

def main():
    """主函数"""
    print("=== Cursor状态检测API性能测试 ===")
    print("测试新的Accessibility API检测器性能...\n")
    
    # 测试状态检测API
    status_url = "http://localhost:5001/api/cursor/status"
    response_times = test_api_performance(status_url, num_requests=20)
    
    analyze_performance(response_times)
    
    print("\n=== 测试完成 ===")
    print("新的Accessibility API检测器相比原有的图像识别方法应该有显著的性能提升：")
    print("- 原方法：每次检测约700-800ms（图像识别耗时）")
    print("- 新方法：预期每次检测约50-100ms（系统API调用）")

if __name__ == "__main__":
    main()