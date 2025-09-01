#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
新API接口使用示例
"""

import requests
import json
import time

def create_new_chat(workspace_id: str, root_path: str = None):
    """创建新对话"""
    print("🔄 创建新对话...")

    url = "http://127.0.0.1:5004/api/create-new-chat"
    data = {"workspace_id": workspace_id}

    if root_path:
        data["rootPath"] = root_path

    response = requests.post(url, json=data)

    if response.status_code == 200:
        result = response.json()
        print(f"✅ 新对话创建成功: {result}")
        return result
    else:
        print(f"❌ 创建失败: {response.status_code} - {response.text}")
        return None

def send_message(workspace_id: str, message: str, session_id: str = None):
    """发送消息"""
    print(f"📤 发送消息: {message}")

    url = "http://127.0.0.1:5004/api/send-message"
    data = {
        "workspace_id": workspace_id,
        "message": message
    }

    if session_id:
        data["session_id"] = session_id

    response = requests.post(url, json=data)

    if response.status_code == 200:
        result = response.json()
        print(f"✅ 消息发送成功: {result}")
        return result
    else:
        print(f"❌ 发送失败: {response.status_code} - {response.text}")
        return None

def main():
    """主函数演示完整流程"""

    # 配置参数
    workspace_id = "1a5189dda9c18775c252e8711653f64d"
    project_path = "/Users/dxm/IdeaProjects/github/cursor-live"

    print("🚀 新API接口使用示例")
    print("=" * 50)
    print(f"工作区ID: {workspace_id}")
    print(f"项目路径: {project_path}")
    print()

    # 步骤1: 创建新对话
    print("步骤1: 创建新对话")
    create_result = create_new_chat(workspace_id, project_path)

    if create_result and create_result.get("success"):
        print("✅ Cursor已激活，对话框已准备就绪")
        print("   前端页面可以使用以下URL:")
        print(f"   http://127.0.0.1:5004/chat/{workspace_id}")
        print()

        # 等待几秒让Cursor准备就绪
        print("⏳ 等待Cursor准备就绪...")
        time.sleep(5)

        # 步骤2: 发送第一条消息（没有session_id）
        print("步骤2: 发送第一条消息（自动获取session_id）")
        first_message = "你好，这是一个测试消息"
        send_result1 = send_message(workspace_id, first_message)

        session_id = None
        if send_result1 and send_result1.get("success"):
            session_id = send_result1.get("session_id")
            print(f"📝 获取到Session ID: {session_id}")
            print()

            # 等待几秒
            time.sleep(3)

            # 步骤3: 发送第二条消息（使用已知的session_id）
            print("步骤3: 发送第二条消息（使用已知session_id）")
            second_message = "这是第二条测试消息，现在我有了session_id"
            send_result2 = send_message(workspace_id, second_message, session_id)

            if send_result2 and send_result2.get("success"):
                print("✅ 第二条消息发送成功")
                print("🎉 演示完成！")
            else:
                print("❌ 第二条消息发送失败")
        else:
            print("❌ 第一条消息发送失败")

    else:
        print("❌ 创建新对话失败")
        print("可能的原因:")
        print("1. Cursor应用未安装或未运行")
        print("2. pyautogu.py模块配置不正确")
        print("3. 系统权限不足")

    print("\n" + "=" * 50)
    print("示例运行完毕")

if __name__ == "__main__":
    main()
