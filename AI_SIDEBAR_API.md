# AI侧边栏API功能说明

本文档介绍了新增的AI侧边栏状态检测和打开功能的API接口。

## 功能概述

根据用户需求，我们添加了以下功能：

1. **侧边栏状态检测**：检查指定workspace中`workbench.auxiliaryBar.hidden`的值
2. **侧边栏打开功能**：当侧边栏隐藏时，通过快捷键自动打开AI侧边栏

## API接口

### 1. 检测AI侧边栏状态

**接口地址：** `GET /api/cursor/sidebar/status`

**参数：**
- `workspace_id` (必需): workspace的ID

**响应示例：**
```json
{
    "success": true,
    "workspace_id": "c27e103d94c8551d951a6e721a27b5f5",
    "auxiliary_bar_hidden": false,
    "needs_open_command": false
}
```

**字段说明：**
- `auxiliary_bar_hidden`: 侧边栏是否隐藏（true=隐藏，false=显示）
- `needs_open_command`: 是否需要执行打开命令（与auxiliary_bar_hidden值相同）

### 2. 打开AI侧边栏

**接口地址：** `POST /api/cursor/sidebar/open`

**请求体：**
```json
{
    "skip_activation": false
}
```

**参数说明：**
- `skip_activation` (可选): 是否跳过激活Cursor窗口的步骤，默认为false

**响应示例：**
```json
{
    "success": true,
    "message": "AI sidebar opened successfully"
}
```

## 使用流程

### 典型使用场景

当Cursor首次打开或激活项目时，按以下流程操作：

1. **检测侧边栏状态**
   ```bash
   curl "http://127.0.0.1:5000/api/cursor/sidebar/status?workspace_id=YOUR_WORKSPACE_ID"
   ```

2. **根据检测结果决定是否打开侧边栏**
   - 如果`needs_open_command`为`true`，则调用打开API
   - 如果`needs_open_command`为`false`，则跳过打开步骤

3. **打开侧边栏（如需要）**
   ```bash
   curl -X POST -H "Content-Type: application/json" \
        -d '{"skip_activation": false}' \
        http://127.0.0.1:5000/api/cursor/sidebar/open
   ```

### 快捷键说明

打开AI侧边栏使用的快捷键：
- **macOS**: `Command + Shift + A`
- **Windows/Linux**: `Ctrl + Shift + A`

## 测试工具

我们提供了一个测试脚本 `test_sidebar_api.py` 来验证功能：

```bash
python3 test_sidebar_api.py <workspace_id>
```

**示例：**
```bash
python3 test_sidebar_api.py c27e103d94c8551d951a6e721a27b5f5
```

## 技术实现

### 后端实现

1. **状态检测**：通过读取workspace的SQLite数据库（`state.vscdb`）中的`workbench.auxiliaryBar.hidden`键值
2. **侧边栏打开**：使用pyautogui库发送快捷键`Command/Ctrl + Shift + A`

### 文件修改

- `server.py`: 添加了两个新的API路由
- `pyautogu.py`: 添加了`open_ai_sidebar()`方法和对应的导出函数
- `test_sidebar_api.py`: 新增的测试脚本

## 错误处理

### 常见错误

1. **workspace_id不存在**
   ```json
   {
       "error": "Workspace database not found: invalid_workspace_id"
   }
   ```

2. **pyautogui模块不可用**
   ```json
   {
       "error": "Cursor automation not available. Please ensure pyautogu.py is properly configured."
   }
   ```

3. **Cursor应用不可访问**
   ```json
   {
       "error": "Failed to open AI sidebar. Please ensure Cursor is running and accessible."
   }
   ```

## 注意事项

1. 确保Cursor应用正在运行
2. 确保有足够的系统权限执行自动化操作
3. 在macOS上可能需要授予辅助功能权限
4. 建议在切换项目后使用`skip_activation: true`参数以避免重复激活

## 日志记录

所有API调用都会记录详细的日志信息，包括：
- 请求来源IP
- workspace_id
- 操作结果
- 错误信息（如有）

日志可以帮助调试和监控API的使用情况。