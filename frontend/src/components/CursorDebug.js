import React, { useState, useEffect, useCallback } from 'react';
import './CursorDebug.css';

/**
 * Cursor调试页面组件
 * 实现实时监控Cursor状态并提供操作功能
 */
const CursorDebug = () => {
  const [status, setStatus] = useState({
    window: { is_front: false, front_app: '', status: 'loading' },
    dialog: { dialog_state: 'unknown', is_dialog_open: false, is_empty: false, status: 'loading' },
    focus: { is_focused: false, cursor_detected: false, ai_input_detected: false, element_info: {}, status: 'loading' },
    timestamp: ''
  });
  const [isRefreshing, setIsRefreshing] = useState(true);
  const [operations, setOperations] = useState({
    opening: false,
    activating: false,
    openingDialog: false,
    closingDialog: false,
    quitting: false,
    screenshotWindow: false,
    screenshotFullscreen: false
  });
  const [lastError, setLastError] = useState(null);
  const [lastScreenshot, setLastScreenshot] = useState(null);
  const [currentWorkspaceId, setCurrentWorkspaceId] = useState(null);

  // API基础URL - 使用代理，所以使用空字符串
  const API_BASE = process.env.REACT_APP_API_BASE || '';

  /**
   * 获取聚焦状态
   */
  const fetchFocusStatus = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/cursor/focus`);
      if (response.ok) {
        const data = await response.json();
        return { ...data, status: 'success' };
      } else {
        throw new Error(`HTTP ${response.status}`);
      }
    } catch (error) {
      console.error('获取聚焦状态失败:', error);
      return {
        is_focused: false,
        cursor_detected: false,
        ai_input_detected: false,
        element_info: {},
        status: 'error',
        error: error.message
      };
    }
  }, [API_BASE]);

  /**
   * 获取最新的workspace_id
   */
  const fetchLatestWorkspaceId = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/api/chats`);
      if (response.ok) {
        const chats = await response.json();
        if (chats && chats.length > 0) {
          // 获取最新聊天的workspace_id
          const latestWorkspaceId = chats[0].workspace_id;
          setCurrentWorkspaceId(latestWorkspaceId);
          return latestWorkspaceId;
        }
      }
    } catch (error) {
      console.error('获取workspace_id失败:', error);
    }
    return null;
  }, [API_BASE]);

  /**
   * 获取Cursor状态
   */
  const fetchStatus = useCallback(async () => {
    try {
      // 确保有workspace_id
      let workspaceId = currentWorkspaceId;
      if (!workspaceId) {
        workspaceId = await fetchLatestWorkspaceId();
      }
      
      // 构建状态API URL，如果有workspace_id则传递
      const statusUrl = workspaceId 
        ? `${API_BASE}/api/cursor/status?workspace_id=${workspaceId}`
        : `${API_BASE}/api/cursor/status`;
      
      // 并行获取窗口/对话框状态和聚焦状态
      const [statusResponse, focusData] = await Promise.all([
        fetch(statusUrl),
        fetchFocusStatus()
      ]);
      
      if (statusResponse.ok) {
        const statusData = await statusResponse.json();
        setStatus({
          ...statusData,
          focus: focusData
        });
        setLastError(null);
      } else {
        throw new Error(`HTTP ${statusResponse.status}`);
      }
    } catch (error) {
      console.error('获取状态失败:', error);
      setLastError(error.message);
      setStatus(prev => ({
        ...prev,
        window: { ...prev.window, status: 'error' },
        dialog: { ...prev.dialog, status: 'error' },
        focus: { ...prev.focus, status: 'error' }
      }));
    }
  }, [API_BASE, currentWorkspaceId, fetchLatestWorkspaceId, fetchFocusStatus]);

  /**
   * 执行操作的通用函数
   */
  const executeOperation = async (endpoint, operationKey, successMessage) => {
    setOperations(prev => ({ ...prev, [operationKey]: true }));
    try {
      const response = await fetch(`${API_BASE}/api/cursor/${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });
      
      const result = await response.json();
      
      if (result.success) {
        console.log(successMessage);
        // 操作成功后立即刷新状态
        setTimeout(fetchStatus, 500);
      } else {
        throw new Error(result.message || result.error || '操作失败');
      }
      
      return result;
    } catch (error) {
      console.error(`${successMessage}失败:`, error);
      setLastError(error.message);
      throw error;
    } finally {
      setOperations(prev => ({ ...prev, [operationKey]: false }));
    }
  };

  // 操作函数
  const openCursor = () => executeOperation('open', 'opening', '打开Cursor');
  const activateCursor = () => executeOperation('activate', 'activating', '激活Cursor');
  const openDialog = () => executeOperation('dialog/open', 'openingDialog', '打开AI对话框');
  const closeDialog = () => executeOperation('dialog/close', 'closingDialog', '关闭AI对话框');
  const quitCursor = () => executeOperation('quit', 'quitting', '退出Cursor');

  /**
   * 截图功能
   */
  const takeScreenshot = async (type = 'window') => {
    const operationKey = type === 'window' ? 'screenshotWindow' : 'screenshotFullscreen';
    setOperations(prev => ({ ...prev, [operationKey]: true }));
    
    try {
      const response = await fetch(`${API_BASE}/api/cursor/screenshot`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type })
      });
      
      const result = await response.json();
      
      if (result.success) {
        setLastScreenshot({
          type,
          imageData: result.image_data,
          filename: result.filename,
          timestamp: result.timestamp
        });
        console.log(`${type === 'window' ? '窗口' : '全屏'}截图成功`);
        setLastError(null);
      } else {
        throw new Error(result.message || result.error || '截图失败');
      }
      
      return result;
    } catch (error) {
      console.error('截图失败:', error);
      setLastError(error.message);
      throw error;
    } finally {
      setOperations(prev => ({ ...prev, [operationKey]: false }));
    }
  };

  const takeWindowScreenshot = () => takeScreenshot('window');
  const takeFullscreenScreenshot = () => takeScreenshot('fullscreen');

  /**
   * 下载截图
   */
  const downloadScreenshot = () => {
    if (!lastScreenshot) return;
    
    const link = document.createElement('a');
    link.href = lastScreenshot.imageData;
    link.download = lastScreenshot.filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  /**
   * 切换自动刷新
   */
  const toggleRefresh = () => {
    setIsRefreshing(!isRefreshing);
  };

  /**
   * 手动刷新
   */
  const manualRefresh = () => {
    fetchStatus();
  };

  // 初始化时获取workspace_id
  useEffect(() => {
    fetchLatestWorkspaceId();
  }, [fetchLatestWorkspaceId]);

  // 设置定时刷新（1000ms）
  useEffect(() => {
    let interval;
    if (isRefreshing) {
      interval = setInterval(fetchStatus, 1000);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isRefreshing, fetchStatus]);

  // 初始加载
  useEffect(() => {
    fetchStatus();
  }, [fetchStatus]);

  /**
   * 获取状态指示器样式
   */
  const getStatusClass = (isActive, isLoading = false) => {
    if (isLoading) return 'status-loading';
    return isActive ? 'status-active' : 'status-inactive';
  };

  /**
   * 格式化时间戳
   */
  const formatTimestamp = (timestamp) => {
    if (!timestamp) return '';
    return new Date(timestamp).toLocaleTimeString('zh-CN', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3
    });
  };

  return (
    <div className="cursor-debug">
      <div className="debug-header">
        <h2>Cursor 调试面板</h2>
        <div className="refresh-controls">
          <button 
            className={`refresh-toggle ${isRefreshing ? 'active' : ''}`}
            onClick={toggleRefresh}
          >
            {isRefreshing ? '⏸️ 暂停刷新' : '▶️ 开始刷新'}
          </button>
          <button className="manual-refresh" onClick={manualRefresh}>
            🔄 手动刷新
          </button>
        </div>
      </div>

      {lastError && (
        <div className="error-banner">
          ⚠️ 错误: {lastError}
        </div>
      )}

      <div className="status-grid">
        {/* 窗口状态 */}
        <div className="status-card">
          <h3>窗口状态</h3>
          <div className="status-item">
            <span className="status-label">前台状态:</span>
            <span className={`status-indicator ${getStatusClass(status.window.is_front, status.window.status === 'loading')}`}>
              {status.window.status === 'loading' ? '检测中...' : 
               status.window.is_front ? '✅ 在前台' : '❌ 不在前台'}
            </span>
          </div>
          <div className="status-item">
            <span className="status-label">当前前台应用:</span>
            <span className="status-value">{status.window.front_app || '未知'}</span>
          </div>
        </div>

        {/* 对话框状态 */}
        <div className="status-card">
          <h3>AI对话框状态</h3>
          <div className="status-item">
            <span className="status-label">对话框:</span>
            <span className={`status-indicator ${getStatusClass(status.dialog.is_dialog_open, status.dialog.status === 'loading')}`}>
              {status.dialog.status === 'loading' ? '检测中...' : 
               status.dialog.is_dialog_open ? '✅ 已打开' : '❌ 未打开'}
            </span>
          </div>
          <div className="status-item">
            <span className="status-label">界面状态:</span>
            <span className="status-value">
              {status.dialog.dialog_state === 'dialogue' ? '对话模式' :
               status.dialog.dialog_state === 'empty' ? '空白界面' : '未知状态'}
            </span>
          </div>
        </div>

        {/* 聚焦状态 */}
        <div className="status-card">
          <h3>AI输入聚焦状态</h3>
          <div className="status-item">
            <span className="status-label">聚焦状态:</span>
            <span className={`status-indicator ${getStatusClass(status.focus.is_focused, status.focus.status === 'loading')}`}>
              {status.focus.status === 'loading' ? '检测中...' : 
               status.focus.is_focused ? '🎯 正在输入' : '📤 未聚焦'}
            </span>
          </div>
          <div className="status-item">
            <span className="status-label">Cursor检测:</span>
            <span className={`status-indicator ${getStatusClass(status.focus.cursor_detected, status.focus.status === 'loading')}`}>
              {status.focus.status === 'loading' ? '检测中...' : 
               status.focus.cursor_detected ? '✅ 已检测' : '❌ 未检测'}
            </span>
          </div>
          <div className="status-item">
            <span className="status-label">AI输入框:</span>
            <span className={`status-indicator ${getStatusClass(status.focus.ai_input_detected, status.focus.status === 'loading')}`}>
              {status.focus.status === 'loading' ? '检测中...' : 
               status.focus.ai_input_detected ? '✅ 已识别' : '❌ 未识别'}
            </span>
          </div>
          {status.focus.element_info && status.focus.element_info.role && (
            <div className="status-item">
              <span className="status-label">元素类型:</span>
              <span className="status-value">{status.focus.element_info.role}</span>
            </div>
          )}
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="operations-grid">
        <div className="operation-group">
          <h3>应用操作</h3>
          <div className="button-row">
            <button 
              className="operation-btn open"
              onClick={openCursor}
              disabled={operations.opening}
            >
              {operations.opening ? '打开中...' : '🚀 打开Cursor'}
            </button>
            <button 
              className="operation-btn activate"
              onClick={activateCursor}
              disabled={operations.activating}
            >
              {operations.activating ? '激活中...' : '🔝 激活窗口'}
            </button>
            <button 
              className="operation-btn quit"
              onClick={quitCursor}
              disabled={operations.quitting}
            >
              {operations.quitting ? '退出中...' : '❌ 退出Cursor'}
            </button>
          </div>
        </div>

        <div className="operation-group">
          <h3>对话框操作</h3>
          <div className="button-row">
            <button 
              className="operation-btn dialog-open"
              onClick={openDialog}
              disabled={operations.openingDialog}
            >
              {operations.openingDialog ? '打开中...' : '💬 打开对话框'}
            </button>
            <button 
              className="operation-btn dialog-close"
              onClick={closeDialog}
              disabled={operations.closingDialog}
            >
              {operations.closingDialog ? '关闭中...' : '🚫 关闭对话框'}
            </button>
          </div>
        </div>

        <div className="operation-group">
          <h3>截图功能</h3>
          <div className="button-row">
            <button 
              className="operation-btn screenshot-window"
              onClick={takeWindowScreenshot}
              disabled={operations.screenshotWindow}
            >
              {operations.screenshotWindow ? '截图中...' : '🖼️ 窗口截图'}
            </button>
            <button 
              className="operation-btn screenshot-fullscreen"
              onClick={takeFullscreenScreenshot}
              disabled={operations.screenshotFullscreen}
            >
              {operations.screenshotFullscreen ? '截图中...' : '🖥️ 全屏截图'}
            </button>
            {lastScreenshot && (
              <button 
                className="operation-btn download"
                onClick={downloadScreenshot}
              >
                💾 下载截图
              </button>
            )}
          </div>
        </div>
      </div>

      {/* 状态信息 */}
      <div className="status-info">
        <div className="timestamp">
          最后更新: {formatTimestamp(status.timestamp)}
        </div>
        <div className="refresh-rate">
          刷新频率: {isRefreshing ? '1s' : '已暂停'}
        </div>
      </div>

      {/* 截图预览 */}
      {lastScreenshot && (
        <div className="screenshot-preview">
          <h3>最新截图预览</h3>
          <div className="screenshot-info">
            <span>类型: {lastScreenshot.type === 'window' ? '窗口截图' : '全屏截图'}</span>
            <span>时间: {formatTimestamp(lastScreenshot.timestamp)}</span>
            <span>文件: {lastScreenshot.filename}</span>
          </div>
          <div className="screenshot-container">
            <img 
              src={lastScreenshot.imageData} 
              alt="截图预览" 
              className="screenshot-image"
              onClick={downloadScreenshot}
              title="点击下载截图"
            />
          </div>
        </div>
      )}
    </div>
  );
};

export default CursorDebug;