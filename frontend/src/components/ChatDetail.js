import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import {
  Container,
  Typography,
  Box,
  Paper,
  CircularProgress,
  Chip,
  Button,
  Avatar,
  alpha,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControlLabel,
  Checkbox,
  DialogContentText,
  Radio,
  RadioGroup,
  FormControl,
  TextField,
  IconButton,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import FolderIcon from '@mui/icons-material/Folder';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import PersonIcon from '@mui/icons-material/Person';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import StorageIcon from '@mui/icons-material/Storage';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import DataObjectIcon from '@mui/icons-material/DataObject';
import FileDownloadIcon from '@mui/icons-material/FileDownload';
import WarningIcon from '@mui/icons-material/Warning';
import SendIcon from '@mui/icons-material/Send';
import RefreshIcon from '@mui/icons-material/Refresh';
import AddIcon from '@mui/icons-material/Add';
import { colors } from '../App';

const ChatDetail = () => {
  const { sessionId } = useParams();
  const [chat, setChat] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [exportModalOpen, setExportModalOpen] = useState(false);
  const [formatDialogOpen, setFormatDialogOpen] = useState(false);
  const [exportFormat, setExportFormat] = useState('html');
  const [dontShowExportWarning, setDontShowExportWarning] = useState(false);
  const [inputText, setInputText] = useState('');
  const [sending, setSending] = useState(false);
  const messagesEndRef = useRef(null);
  
  // 定时刷新相关状态
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(30000); // 默认30秒
  const [lastChatHash, setLastChatHash] = useState(null);
  const [lastChangeTime, setLastChangeTime] = useState(null);
  const refreshTimerRef = useRef(null);
  
  // Cursor状态相关
  const [cursorStatus, setCursorStatus] = useState({
    isActive: false,
    isDialogOpen: false,
    lastCheck: null
  });
  const [statusCheckInterval, setStatusCheckInterval] = useState(5000); // 5秒检查一次状态
  const statusTimerRef = useRef(null);

  // 计算聊天内容的哈希值，用于检测变化
  const calculateChatHash = (chatData) => {
    if (!chatData || !chatData.messages) return null;
    const messagesStr = JSON.stringify(chatData.messages);
    // 使用UTF-8编码处理Unicode字符
    const encoder = new TextEncoder();
    const data = encoder.encode(messagesStr);
    // 简单的哈希计算
    let hash = 0;
    for (let i = 0; i < data.length; i++) {
      hash = ((hash << 5) - hash + data[i]) & 0xffffffff;
    }
    return hash.toString(16);
  };

  // 获取聊天数据
  const fetchChat = useCallback(async () => {
    try {
      const response = await axios.get(`/api/chat/${sessionId}`);
      const newChat = response.data;
      const newHash = calculateChatHash(newChat);
      
      // 检查内容是否发生变化
      if (newHash !== lastChatHash) {
        setChat(newChat);
        setLastChatHash(newHash);
        setLastChangeTime(Date.now());
      }
      
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  }, [sessionId, lastChatHash]);

  // 启动定时刷新
  const startRefreshTimer = useCallback(() => {
    if (refreshTimerRef.current) {
      clearInterval(refreshTimerRef.current);
    }
    
    refreshTimerRef.current = setInterval(() => {
      if (!sending) { // 发送消息时不刷新
        setIsRefreshing(true);
        fetchChat().finally(() => {
          setIsRefreshing(false);
        });
      }
    }, refreshInterval);
  }, [refreshInterval, sending, fetchChat]);

  // 停止定时刷新
  const stopRefreshTimer = () => {
    if (refreshTimerRef.current) {
      clearInterval(refreshTimerRef.current);
      refreshTimerRef.current = null;
    }
  };

  // 手动刷新
  const handleManualRefresh = async () => {
    setIsRefreshing(true);
    await fetchChat();
    setIsRefreshing(false);
  };

  // 检查Cursor状态
  const checkCursorStatus = useCallback(async () => {
    try {
      const workspace_id = chat?.workspace_id;
      const response = await axios.get('/api/cursor-status', {
        params: { workspace_id }
      });
      const status = response.data;
      setCursorStatus({
        isActive: status.isActive,
        isDialogOpen: status.isDialogOpen,
        lastCheck: Date.now()
      });
    } catch (err) {
      console.error('检查Cursor状态失败:', err);
      setCursorStatus(prev => ({
        ...prev,
        isActive: false,
        isDialogOpen: false,
        lastCheck: Date.now()
      }));
    }
  }, [chat?.workspace_id]);

  // 启动状态检查定时器
  const startStatusTimer = useCallback(() => {
    if (statusTimerRef.current) {
      clearInterval(statusTimerRef.current);
    }
    
    statusTimerRef.current = setInterval(() => {
      checkCursorStatus();
    }, statusCheckInterval);
  }, [statusCheckInterval, checkCursorStatus]);

  // 停止状态检查定时器
  const stopStatusTimer = () => {
    if (statusTimerRef.current) {
      clearInterval(statusTimerRef.current);
      statusTimerRef.current = null;
    }
  };

  // 初始化数据获取和定时刷新
  useEffect(() => {
    fetchChat();
    startRefreshTimer();
    startStatusTimer();
    
    // 立即检查一次Cursor状态
    checkCursorStatus();
    
    // Check if user has previously chosen to not show the export warning
    const warningPreference = document.cookie
      .split('; ')
      .find(row => row.startsWith('dontShowExportWarning='));
    
    if (warningPreference) {
      setDontShowExportWarning(warningPreference.split('=')[1] === 'true');
    }

    // 清理函数
    return () => {
      stopRefreshTimer();
      stopStatusTimer();
    };
  }, [sessionId, fetchChat, startRefreshTimer, startStatusTimer, checkCursorStatus]);

  // 当刷新间隔改变时，重启定时器
  useEffect(() => {
    if (refreshInterval) {
      stopRefreshTimer();
      startRefreshTimer();
    }
  }, [refreshInterval, sessionId, startRefreshTimer]);

  // 监听lastChangeTime变化，设置10秒后降低刷新频率的定时器
  useEffect(() => {
    if (lastChangeTime && refreshInterval < 30000) {
      const timer = setTimeout(() => {
        setRefreshInterval(30000); // 10秒后恢复到30秒刷新
        setStatusCheckInterval(5000); // 同时恢复状态检查频率到5秒
      }, 10000);
      
      return () => clearTimeout(timer);
    }
  }, [lastChangeTime, refreshInterval]);

  // 当状态检查间隔改变时，重启状态检查定时器
  useEffect(() => {
    if (statusCheckInterval) {
      stopStatusTimer();
      startStatusTimer();
    }
  }, [statusCheckInterval, startStatusTimer]);

  // 自动滚动到对话底部
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [chat]);

  // Handle format dialog selection
  const handleFormatDialogOpen = () => {
    setFormatDialogOpen(true);
  };

  const handleFormatDialogClose = (confirmed) => {
    setFormatDialogOpen(false);
    
    if (confirmed) {
      // After format selection, show warning dialog or proceed directly
      if (dontShowExportWarning) {
        proceedWithExport(exportFormat);
      } else {
        setExportModalOpen(true);
      }
    }
  };

  // Handle export warning confirmation
  const handleExportWarningClose = (confirmed) => {
    setExportModalOpen(false);
    
    // Save preference in cookies if "Don't show again" is checked
    if (dontShowExportWarning) {
      const expiryDate = new Date();
      expiryDate.setFullYear(expiryDate.getFullYear() + 1); // Cookie lasts 1 year
      document.cookie = `dontShowExportWarning=true; expires=${expiryDate.toUTCString()}; path=/`;
    }
    
    // If confirmed, proceed with export
    if (confirmed) {
      proceedWithExport(exportFormat);
    }
  };

  // Function to initiate export process
  const handleExport = () => {
    // First open format selection dialog
    handleFormatDialogOpen();
  };

  // Function to actually perform the export
  const proceedWithExport = async (format) => {
    try {
      // Request the exported chat as a raw Blob so we can download it directly
      const response = await axios.get(
        `/api/chat/${sessionId}/export?format=${format}`,
        { responseType: 'blob' }
      );

      const blob = response.data;

      // Guard-check to avoid downloading an empty file
      if (!blob || blob.size === 0) {
        throw new Error('Received empty or invalid content from server');
      }

      // Ensure the blob has the correct MIME type
      const mimeType = format === 'json' ? 'application/json;charset=utf-8' : 'text/html;charset=utf-8';
      const typedBlob = blob.type ? blob : new Blob([blob], { type: mimeType });

      // Download Logic
      const extension = format === 'json' ? 'json' : 'html';
      const filename = `cursor-chat-${sessionId.slice(0, 8)}.${extension}`;
      const link = document.createElement('a');
      
      // Create an object URL for the (possibly re-typed) blob
      const url = URL.createObjectURL(typedBlob);
      link.href = url;
      link.download = filename;
      
      // Append link to the body (required for Firefox)
      document.body.appendChild(link);
      
      // Programmatically click the link to trigger the download
      link.click();
      
      // Clean up: remove the link and revoke the object URL
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Export failed:', err);
      alert('Failed to export chat – check console for details');
    }
  };

  // 发送消息到Cursor
  const handleSendMessage = async () => {
    if (!inputText.trim() || sending) return;

    setSending(true);
    try {
      // 使用新的send-message接口
      const payload = {
        message: inputText.trim(),
        workspace_id: chat?.workspace_id
      };

      // 如果已经有session_id，则传递它
      if (chat?.session?.composerId) {
        payload.session_id = chat.session.composerId;
      }

      const response = await axios.post('/api/send-message', payload);

      // 检查响应
      if (response.data.success) {
        console.log('消息发送成功');

        // 如果返回了新的session_id，更新chat状态
        if (response.data.session_id && !chat?.session?.composerId) {
          console.log('收到新session_id:', response.data.session_id);
          // 更新chat状态以包含新的session_id
          setChat(prev => ({
            ...prev,
            session: {
              ...prev.session,
              composerId: response.data.session_id
            }
          }));
        }

        setInputText('');

        // 发送完成后，提高刷新频率到5秒
        setRefreshInterval(5000);
        // 同时提高状态检查频率到2秒
        setStatusCheckInterval(2000);
      } else {
        throw new Error('发送消息失败');
      }

    } catch (err) {
      console.error('发送失败:', err);

      // 检查是否是废弃接口的错误
      if (err.response?.status === 410) {
        alert('API接口已更新，请刷新页面重试');
      } else if (err.response?.status === 400) {
        alert('Cursor未准备好，请先创建新对话');
      } else {
        alert('发送失败，请检查后端服务是否正常运行');
      }
    } finally {
      setSending(false);
    }
  };

  // 创建新对话并发送消息
  const handleCreateNewChat = async () => {
    if (!inputText.trim() || sending) return;

    setSending(true);
    try {
      // 第一步：创建新对话
      const createResponse = await axios.post('/api/create-new-chat', {
        workspace_id: chat?.workspace_id,
        rootPath: chat?.project?.rootPath
      });

      if (createResponse.data.success) {
        console.log('新对话创建成功');

        // 第二步：发送第一条消息
        const messageResponse = await axios.post('/api/send-message', {
          message: inputText.trim(),
          workspace_id: chat?.workspace_id
        });

        if (messageResponse.data.success && messageResponse.data.session_id) {
          console.log('消息发送成功，session_id:', messageResponse.data.session_id);
          // 导航到新的对话页面，使用workspace_id
          window.location.href = `/chat/${chat.workspace_id}`;
        } else {
          console.warn('消息发送失败，但新对话已创建');
          setInputText('');
        }
      } else {
        throw new Error('创建新对话失败');
      }

    } catch (err) {
      console.error('创建新对话失败:', err);

      // 检查是否是废弃接口的错误
      if (err.response?.status === 410) {
        alert('API接口已更新，请刷新页面重试');
      } else {
        alert('创建新对话失败，请检查后端服务是否正常运行');
      }
    } finally {
      setSending(false);
    }
  };

  // 处理回车键发送
  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      // 检查是否按住了Shift键（用于创建新对话）
      if (event.shiftKey) {
        handleCreateNewChat();
      } else {
        handleSendMessage();
      }
    }
  };

  if (loading) {
    return (
      <Container sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '70vh' }}>
        <CircularProgress sx={{ color: colors.highlightColor }} />
      </Container>
    );
  }

  if (error) {
    return (
      <Container>
        <Typography variant="h5" color="error">
          Error: {error}
        </Typography>
      </Container>
    );
  }

  if (!chat) {
    return (
      <Container>
        <Typography variant="h5">
          Chat not found
        </Typography>
      </Container>
    );
  }

  // Format the date safely
  let dateDisplay = 'Unknown date';
  try {
    if (chat.date) {
      const dateObj = new Date(chat.date * 1000);
      // Check if date is valid
      if (!isNaN(dateObj.getTime())) {
        dateDisplay = dateObj.toLocaleString();
      }
    }
  } catch (err) {
    console.error('Error formatting date:', err);
  }

  // Ensure messages exist
  const messages = Array.isArray(chat.messages) ? chat.messages : [];
  const projectName = chat.project?.name || 'Unknown Project';

  return (
    <Container sx={{ mb: 6 }}>
      {/* Format Selection Dialog */}
      <Dialog
        open={formatDialogOpen}
        onClose={() => handleFormatDialogClose(false)}
        aria-labelledby="format-selection-dialog-title"
      >
        <DialogTitle id="format-selection-dialog-title" sx={{ display: 'flex', alignItems: 'center' }}>
          <FileDownloadIcon sx={{ color: colors.highlightColor, mr: 1 }} />
          Export Format
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            Please select the export format for your chat:
          </DialogContentText>
          <FormControl component="fieldset" sx={{ mt: 2 }}>
            <RadioGroup
              aria-label="export-format"
              name="export-format"
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value)}
            >
              <FormControlLabel value="html" control={<Radio />} label="HTML" />
              <FormControlLabel value="json" control={<Radio />} label="JSON" />
            </RadioGroup>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => handleFormatDialogClose(false)} color="highlight">
            Cancel
          </Button>
          <Button onClick={() => handleFormatDialogClose(true)} color="highlight" variant="contained">
            Continue
          </Button>
        </DialogActions>
      </Dialog>

      {/* Export Warning Modal */}
      <Dialog
        open={exportModalOpen}
        onClose={() => handleExportWarningClose(false)}
        aria-labelledby="export-warning-dialog-title"
      >
        <DialogTitle id="export-warning-dialog-title" sx={{ display: 'flex', alignItems: 'center' }}>
          <WarningIcon sx={{ color: 'warning.main', mr: 1 }} />
          Export Warning
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            Please make sure your exported chat doesn't include sensitive data such as API keys and customer information.
          </DialogContentText>
          <FormControlLabel
            control={
              <Checkbox
                checked={dontShowExportWarning}
                onChange={(e) => setDontShowExportWarning(e.target.checked)}
              />
            }
            label="Don't show this warning again"
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => handleExportWarningClose(false)} color="highlight">
            Cancel
          </Button>
          <Button onClick={() => handleExportWarningClose(true)} color="highlight" variant="contained">
            Continue Export
          </Button>
        </DialogActions>
      </Dialog>

      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3, mt: 2 }}>
        <Button
          component={Link}
          to="/"
          startIcon={<ArrowBackIcon />}
          variant="outlined"
          sx={{ 
            borderRadius: 2,
            color: 'white'
          }}
        >
          Back to all chats
        </Button>
        
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          {/* 刷新状态指示器 */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {isRefreshing && (
              <CircularProgress size={16} sx={{ color: colors.highlightColor }} />
            )}
            <Typography variant="caption" color="text.secondary">
              {refreshInterval < 30000 ? '高频刷新中' : '自动刷新'}
            </Typography>
          </Box>
          
          {/* 手动刷新按钮 */}
          <IconButton
            onClick={handleManualRefresh}
            disabled={isRefreshing}
            size="small"
            sx={{
              color: colors.highlightColor,
              '&:hover': {
                backgroundColor: alpha(colors.highlightColor, 0.1),
              }
            }}
          >
            <RefreshIcon />
          </IconButton>
          
          <Button
            onClick={handleExport}
            startIcon={<FileDownloadIcon />}
            variant="contained"
            color="highlight"
            sx={{ 
              borderRadius: 2,
              position: 'relative',
              '&:hover': {
                backgroundColor: alpha(colors.highlightColor, 0.8),
              },
              '&::after': dontShowExportWarning ? null : {
                content: '""',
                position: 'absolute',
                borderRadius: '50%',
                top: '4px',
                right: '4px',
                width: '8px', // Adjusted size for button
                height: '8px' // Adjusted size for button
              },
              // Conditionally add the background color if the warning should be shown
              ...( !dontShowExportWarning && {
                '&::after': { 
                  backgroundColor: 'warning.main'
                }
              })
            }}
          >
            Export
          </Button>
        </Box>
      </Box>

      <Paper 
        sx={{ 
          p: 0, 
          mb: 3, 
          overflow: 'hidden',
          boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
        }}
      >
        <Box sx={{ 
          background: `linear-gradient(90deg, ${colors.highlightColor} 0%, ${colors.highlightColor.light} 100%)`,
          color: 'white',
          px: 3,
          py: 1.5,
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', flexWrap: 'wrap', gap: 1 }}>
            <FolderIcon sx={{ mr: 1, fontSize: 22 }} />
            <Typography variant="h6" fontWeight="600" sx={{ mr: 1.5 }}>
              {projectName}
            </Typography>
            <Chip
              icon={<CalendarTodayIcon />}
              label={dateDisplay}
              size="small"
              sx={{ 
                fontWeight: 500,
                color: 'white',
                '& .MuiChip-icon': { color: 'white' },
                '& .MuiChip-label': { px: 1 }
              }}
            />
          </Box>
        </Box>
        
        <Box sx={{ px: 3, py: 1.5 }}>
          <Box sx={{ 
            display: 'flex', 
            flexWrap: 'wrap', 
            gap: 2,
            alignItems: 'center'
          }}>
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <AccountTreeIcon sx={{ mr: 0.5, color: colors.highlightColor, opacity: 0.8, fontSize: 18 }} />
              <Typography variant="body2" color="text.secondary">
                <strong>Path:</strong> {chat.project?.rootPath || 'Unknown location'}
              </Typography>
            </Box>
            
            {/* Cursor状态指示器 */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box sx={{ 
                width: 8, 
                height: 8, 
                borderRadius: '50%', 
                backgroundColor: cursorStatus.isActive ? 'success.main' : 'error.main',
                mr: 0.5 
              }} />
              <Typography variant="body2" color="text.secondary">
                <strong>Cursor:</strong> {cursorStatus.isActive ? '已激活' : '未激活'}
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Box sx={{ 
                width: 8, 
                height: 8, 
                borderRadius: '50%', 
                backgroundColor: cursorStatus.isDialogOpen ? 'success.main' : 'warning.main',
                mr: 0.5 
              }} />
              <Typography variant="body2" color="text.secondary">
                <strong>AI对话框:</strong> {cursorStatus.isDialogOpen ? '已打开' : '未打开'}
              </Typography>
            </Box>
            
            {chat.workspace_id && (
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <StorageIcon sx={{ mr: 0.5, color: colors.highlightColor, opacity: 0.8, fontSize: 18 }} />
                <Typography variant="body2" color="text.secondary">
                  <strong>Workspace:</strong> {chat.workspace_id}
                </Typography>
              </Box>
            )}
            
            {chat.db_path && (
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <DataObjectIcon sx={{ mr: 0.5, color: colors.highlightColor, opacity: 0.8, fontSize: 18 }} />
                <Typography variant="body2" color="text.secondary" sx={{ wordBreak: 'break-all' }}>
                  <strong>DB:</strong> {chat.db_path.split('/').pop()}
                </Typography>
              </Box>
            )}
          </Box>
        </Box>
      </Paper>

      <Typography variant="h5" gutterBottom fontWeight="600" sx={{ mt: 4, mb: 3 }}>
        Conversation History
      </Typography>

      {messages.length === 0 ? (
        <Paper sx={{ p: 4, textAlign: 'center', borderRadius: 3 }}>
          <Typography variant="body1">
            No messages found in this conversation.
          </Typography>
        </Paper>
      ) : (
        <Box sx={{ mb: 4 }}>
          {messages.map((message, index) => (
            <Box key={index} sx={{ mb: 3.5 }}>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 1.5 }}>
                <Avatar
                  sx={{
                    bgcolor: message.role === 'user' ? colors.highlightColor : colors.secondary.main,
                    width: 32,
                    height: 32,
                    mr: 1.5,
                    boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                  }}
                >
                  {message.role === 'user' ? <PersonIcon /> : <SmartToyIcon />}
                </Avatar>
                <Typography variant="subtitle1" fontWeight="600">
                  {message.role === 'user' ? 'You' : 'Cursor Assistant'}
                </Typography>
              </Box>
              
              <Paper 
                elevation={1}
                sx={{ 
                  p: 2.5, 
                  ml: message.role === 'user' ? 0 : 5,
                  mr: message.role === 'assistant' ? 0 : 5,
                  backgroundColor:alpha(colors.highlightColor, 0.04),
                  borderLeft: '4px solid',
                  borderColor: message.role === 'user' ? colors.highlightColor : colors.secondary.main,
                  borderRadius: 2
                }}
              >
                <Box sx={{ 
                  '& pre': { 
                    maxWidth: '100%', 
                    overflowX: 'auto',
                    backgroundColor: message.role === 'user' 
                      ? alpha(colors.primary.main, 0.07) 
                      : colors.highlightColor,
                    borderRadius: 1,
                    p: 2
                  },
                  '& code': { 
                    display: 'inline-block', 
                    maxWidth: '100%', 
                    overflowX: 'auto',
                    backgroundColor: message.role === 'user' 
                      ? alpha(colors.primary.main, 0.07) 
                      : colors.highlightColor,
                    borderRadius: 0.5,
                    px: 0.8,
                    py: 0.2
                  },
                  '& img': { maxWidth: '100%' },
                  '& ul, & ol': { pl: 3 },
                  '& a': { 
                    color: message.role === 'user' ? colors.highlightColor : colors.secondary.main,
                    textDecoration: 'none',
                    '&:hover': { textDecoration: 'none' }
                  }
                }}>
                  {typeof message.content === 'string' ? (
                    <ReactMarkdown>
                      {message.content}
                    </ReactMarkdown>
                  ) : (
                    <Typography>Content unavailable</Typography>
                  )}
                </Box>
              </Paper>
            </Box>
          ))}
          {/* 滚动锚点 */}
          <div ref={messagesEndRef} />
        </Box>
      )}
      
      {/* 固定在底部的输入框 */}
      <Paper
        elevation={3}
        sx={{
          position: 'fixed',
          bottom: 0,
          left: 0,
          right: 0,
          p: 2,
          backgroundColor: 'background.paper',
          borderTop: '1px solid',
          borderColor: 'divider',
          zIndex: 1000
        }}
      >
        <Container>
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
            <TextField
              fullWidth
              multiline
              maxRows={4}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="输入消息发送到Cursor... (Shift+Enter创建新对话)"
              variant="outlined"
              size="small"
              disabled={sending}
              sx={{
                '& .MuiOutlinedInput-root': {
                  borderRadius: 2,
                }
              }}
            />
            <IconButton
              onClick={handleSendMessage}
              disabled={!inputText.trim() || sending}
              color="primary"
              sx={{
                bgcolor: colors.highlightColor,
                color: 'white',
                '&:hover': {
                  bgcolor: alpha(colors.highlightColor, 0.8),
                },
                '&:disabled': {
                  bgcolor: 'action.disabled',
                  color: 'action.disabled'
                }
              }}
              title="发送消息"
            >
              <SendIcon />
            </IconButton>
            <IconButton
              onClick={handleCreateNewChat}
              disabled={!inputText.trim() || sending}
              color="secondary"
              sx={{
                bgcolor: colors.secondary.main,
                color: 'white',
                '&:hover': {
                  bgcolor: alpha(colors.secondary.main, 0.8),
                },
                '&:disabled': {
                  bgcolor: 'action.disabled',
                  color: 'action.disabled'
                }
              }}
              title="创建新对话并发送"
            >
              <AddIcon />
            </IconButton>
          </Box>
        </Container>
      </Paper>
      
      {/* 为固定输入框留出空间 */}
      <Box sx={{ height: '80px' }} />
    </Container>
  );
};

export default ChatDetail;