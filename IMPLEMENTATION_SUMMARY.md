# Cursor View 智能重启功能实现总结

## 功能概述

根据用户需求，我们实现了在切换项目或首次发送消息时，总是先关闭Cursor再重新打开的功能，以确保聚焦点正确。

## 实现的功能

### 1. 智能重启逻辑
- **首次发送消息**：自动重启Cursor以确保正确的聚焦点
- **切换项目**：重启Cursor以加载正确的项目上下文
- **避免重复关闭**：通过逻辑判断避免在切换项目时重复关闭Cursor

### 2. 新对话功能
- **创建新对话**：通过Command+T快捷键创建新对话
- **获取session_id**：自动获取新创建的session_id
- **前端导航**：创建后自动跳转到新对话页面
- **实时刷新**：基于新的session_id刷新chatDetail

### 3. 输入问题修复
- **首次输入问题**：修复首次输入时出现意外字符的问题
- **输入缓冲区清除**：在关键操作前自动清除输入缓冲区
- **多重保护**：在打开对话框、创建新对话、输入文本前都进行清除

### 2. 平台兼容性
- **macOS**：使用AppleScript优雅地关闭和打开Cursor
- **Windows/Linux**：使用psutil管理Cursor进程

### 3. 错误处理
- 优雅的关闭失败处理
- 超时处理
- 详细的日志记录

## 代码修改

### 1. pyautogu.py
- 添加了 `close_cursor()` 方法
- 改进了 `open_cursor()` 方法
- 修改了 `switch_cursor_project()` 方法，在切换时先关闭再打开
- 修改了 `send_to_cursor()` 方法，添加了 `force_restart` 和 `create_new_chat` 参数
- 修改了 `receive_from_app()` 函数，支持强制重启和新对话参数
- 添加了 `create_new_chat()` 方法
- 添加了 `get_latest_session_id()` 方法
- 修复了首次输入问题，添加了输入缓冲区清除功能

### 2. server.py
- 修改了 `send_to_cursor()` API端点
- 添加了首次发送消息的检测逻辑
- 优化了项目切换和强制重启的逻辑判断
- 添加了新对话创建的支持
- 返回新创建的session_id给前端

### 3. requirements.txt
- 添加了 `psutil>=5.8.0` 依赖

### 4. 前端修改
- 修改了 `ChatDetail.js`，添加了新对话按钮
- 添加了 `handleCreateNewChat()` 函数
- 支持Shift+Enter快捷键创建新对话
- 自动导航到新创建的对话页面

## 重启流程

### 首次发送消息流程
1. 检测到 `current_workspace_id` 为 `None`
2. 设置 `force_restart = True`
3. 调用 `receive_from_app()` 时执行强制重启
4. 关闭Cursor → 等待3秒 → 重新打开Cursor → 等待5秒
5. 继续正常的消息发送流程

### 切换项目流程
1. 检测到 `workspace_id` 与 `current_workspace_id` 不同
2. 调用 `switch_cursor_project()` 方法
3. 关闭Cursor → 等待2秒 → 使用命令行打开新项目 → 等待8秒
4. 设置 `project_switched = True`，跳过后续的激活步骤
5. 调用 `receive_from_app()` 时不执行强制重启（避免重复关闭）

## 新对话流程

### 创建新对话流程
1. 前端发送请求时设置 `create_new_chat = True`
2. 打开AI对话框
3. 使用Command+T创建新对话
4. 输入并发送消息
5. 获取最新session_id
6. 返回session_id给前端
7. 前端自动跳转到新对话页面

## 测试验证

### 逻辑测试
- 首次发送消息：`force_restart=True, skip_activation=False` → 执行重启
- 切换项目后：`force_restart=False, skip_activation=True` → 不执行重启
- 正常发送：`force_restart=False, skip_activation=False` → 不执行重启

### 功能测试
- 创建了 `test_cursor_restart.py` 用于完整功能测试
- 创建了 `test_restart_fix.py` 用于逻辑验证
- 创建了 `test_new_chat.py` 用于新对话功能测试
- 创建了 `test_first_input_fix.py` 用于首次输入问题修复测试

## 优势

1. **确保聚焦点正确**：重启确保Cursor窗口处于正确的状态
2. **避免上下文混乱**：每次切换项目都会重新加载，避免项目上下文混乱
3. **提高发送成功率**：通过重启确保AI对话框能够正确打开
4. **避免重复操作**：智能判断避免不必要的重复关闭操作
5. **平台兼容性**：支持macOS、Windows和Linux
6. **新对话管理**：支持创建新对话并自动导航
7. **实时反馈**：前端能够实时获取新对话的session_id并刷新
8. **输入稳定性**：修复首次输入问题，确保输入内容正确

## 注意事项

1. **权限要求**：
   - macOS需要AppleScript执行权限
   - Windows/Linux需要进程管理权限

2. **依赖要求**：
   - 需要安装psutil包
   - Cursor命令行工具需要在PATH中

3. **时间开销**：
   - 首次发送：约8秒（关闭3秒 + 启动5秒）
   - 切换项目：约10秒（关闭2秒 + 启动8秒）

## 未来改进

1. **配置化**：允许用户配置是否启用自动重启功能
2. **智能检测**：根据Cursor状态智能决定是否需要重启
3. **并行处理**：优化等待时间，提高响应速度
4. **错误恢复**：增强错误处理和恢复机制
