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
  IconButton,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import FolderIcon from '@mui/icons-material/Folder';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import PersonIcon from '@mui/icons-material/Person';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import StorageIcon from '@mui/icons-material/Storage';
import AccountTreeIcon from '@mui/icons-material/AccountTree';

import FileDownloadIcon from '@mui/icons-material/FileDownload';
import WarningIcon from '@mui/icons-material/Warning';
import RefreshIcon from '@mui/icons-material/Refresh';
import { colors } from '../App';

const ChatHistory = () => {
  const { sessionId } = useParams();
  const [chat, setChat] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [exportModalOpen, setExportModalOpen] = useState(false);
  const [formatDialogOpen, setFormatDialogOpen] = useState(false);
  const [exportFormat, setExportFormat] = useState('html');
  const [dontShowExportWarning, setDontShowExportWarning] = useState(false);
  const messagesEndRef = useRef(null);
  
  // 定时刷新相关状态
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshInterval, setRefreshInterval] = useState(30000); // 默认30秒
  const [lastChatHash, setLastChatHash] = useState(null);
  const [lastChangeTime, setLastChangeTime] = useState(null);
  const refreshTimerRef = useRef(null);

  // 计算聊天内容的哈希值，用于检测变化
  const calculateChatHash = (chatData) => {
    if (!chatData || !chatData.messages) return null;
    const messagesStr = JSON.stringify(chatData.messages);
    const encoder = new TextEncoder();
    const data = encoder.encode(messagesStr);
    let hash = 0;
    for (let i = 0; i < data.length; i++) {
      hash = ((hash << 5) - hash + data[i]) & 0xffffffff;
    }
    return hash.toString(16);
  };

  // 获取聊天数据
  const fetchChat = useCallback(async () => {
    console.log('fetchChat 被调用 - sessionId:', sessionId);
    
    if (!sessionId || sessionId === 'undefined' || sessionId === 'null') {
      console.log('sessionId无效，跳过fetchChat');
      return;
    }

    console.log('开始获取聊天数据，sessionId:', sessionId);
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
      console.error('fetchChat 错误:', err);
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
      if (!loading) { // 加载时不刷新
        setIsRefreshing(true);
        fetchChat().finally(() => {
          setIsRefreshing(false);
        });
      }
    }, refreshInterval);
  }, [refreshInterval, fetchChat, loading]);

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

  // 处理导出格式选择
  const handleFormatDialogClose = (confirmed) => {
    setFormatDialogOpen(false);
    if (confirmed) {
      setExportModalOpen(true);
    }
  };

  // 处理导出警告关闭
  const handleExportWarningClose = (confirmed) => {
    setExportModalOpen(false);
    if (confirmed) {
      handleExport();
    }
  };

  // 处理导出
  const handleExport = () => {
    if (!chat) return;
    
    const exportUrl = `/api/chat/${sessionId}/export?format=${exportFormat}`;
    const link = document.createElement('a');
    link.href = exportUrl;
    link.download = `cursor-chat-${sessionId.slice(0, 8)}.${exportFormat}`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    // 如果用户选择不再显示警告，设置cookie
    if (dontShowExportWarning) {
      document.cookie = 'dontShowExportWarning=true; max-age=31536000; path=/';
    }
  };

  // 初始化数据获取和定时刷新
  useEffect(() => {
    console.log('ChatHistory useEffect 执行 - sessionId:', sessionId);
    
    if (!sessionId || sessionId === 'undefined') {
      console.log('sessionId无效，跳过数据获取');
      setLoading(false);
      return;
    }

    console.log('开始初始化数据获取和定时刷新，sessionId:', sessionId);
    fetchChat();
    startRefreshTimer();
    
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
    };
  }, [sessionId, fetchChat, startRefreshTimer]);

  // 当刷新间隔改变时，重启定时器
  useEffect(() => {
    if (refreshInterval) {
      stopRefreshTimer();
      startRefreshTimer();
    }
  }, [refreshInterval, startRefreshTimer]);

  // 监听lastChangeTime变化，设置10秒后降低刷新频率的定时器
  useEffect(() => {
    if (lastChangeTime && refreshInterval < 30000) {
      const timer = setTimeout(() => {
        setRefreshInterval(30000); // 10秒后恢复到30秒刷新
      }, 10000);
      
      return () => clearTimeout(timer);
    }
  }, [lastChangeTime, refreshInterval]);

  // 自动滚动到对话底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chat?.messages]);

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
          <CircularProgress />
        </Box>
      </Container>
    );
  }

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="h6" color="error" gutterBottom>
            加载失败
          </Typography>
          <Typography color="text.secondary" gutterBottom>
            {error}
          </Typography>
          <Button
            component={Link}
            to="/"
            variant="contained"
            sx={{ mt: 2 }}
          >
            返回首页
          </Button>
        </Paper>
      </Container>
    );
  }

  if (!chat) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="h6" color="text.secondary" gutterBottom>
            未找到对话
          </Typography>
          <Button
            component={Link}
            to="/"
            variant="contained"
            sx={{ mt: 2 }}
          >
            返回首页
          </Button>
        </Paper>
      </Container>
    );
  }

  const { messages, project, date } = chat;
  const projectName = project?.name || 'Unknown Project';
  const dateDisplay = date ? new Date(date * 1000).toLocaleDateString() : 'Unknown Date';

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* 导出格式选择对话框 */}
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
            onClick={() => setFormatDialogOpen(true)}
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
                width: '8px',
                height: '8px'
              },
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
            
            {chat.workspace_id && (
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <StorageIcon sx={{ mr: 0.5, color: colors.highlightColor, opacity: 0.8, fontSize: 18 }} />
                <Typography variant="body2" color="text.secondary">
                  <strong>Workspace:</strong> {chat.workspace_id}
                </Typography>
              </Box>
            )}
          </Box>
        </Box>
      </Paper>

      {/* 对话内容 */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ mb: 3, color: colors.highlightColor }}>
          对话内容
        </Typography>
        
        {messages && messages.length > 0 ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
            {messages.map((message, index) => (
              <Box
                key={index}
                sx={{
                  display: 'flex',
                  gap: 2,
                  p: 2,
                  borderRadius: 2,
                  backgroundColor: message.role === 'user' ? alpha(colors.highlightColor, 0.1) : 'grey.50',
                  border: `1px solid ${message.role === 'user' ? alpha(colors.highlightColor, 0.3) : 'grey.200'}`,
                }}
              >
                <Avatar
                  sx={{
                    bgcolor: message.role === 'user' ? colors.highlightColor : 'grey.500',
                    width: 40,
                    height: 40,
                  }}
                >
                  {message.role === 'user' ? <PersonIcon /> : <SmartToyIcon />}
                </Avatar>
                
                <Box sx={{ flex: 1 }}>
                  <Typography variant="subtitle2" gutterBottom sx={{ fontWeight: 600 }}>
                    {message.role === 'user' ? 'You' : 'AI Assistant'}
                  </Typography>
                  
                  <Box sx={{ 
                    '& p': { mb: 1 },
                    '& pre': { 
                      backgroundColor: 'grey.100', 
                      p: 2, 
                      borderRadius: 1, 
                      overflow: 'auto',
                      fontSize: '0.875rem'
                    },
                    '& code': { 
                      backgroundColor: 'grey.100', 
                      p: 0.5, 
                      borderRadius: 0.5,
                      fontSize: '0.875rem'
                    }
                  }}>
                    <ReactMarkdown>{message.content}</ReactMarkdown>
                  </Box>
                </Box>
              </Box>
            ))}
          </Box>
        ) : (
          <Typography color="text.secondary" textAlign="center" sx={{ py: 4 }}>
            暂无对话内容
          </Typography>
        )}
        
        <div ref={messagesEndRef} />
      </Paper>
    </Container>
  );
};

export default ChatHistory;
