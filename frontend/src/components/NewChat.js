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
  TextField,
  IconButton,
  Tooltip,
  Alert,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import FolderIcon from '@mui/icons-material/Folder';

import PersonIcon from '@mui/icons-material/Person';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import StorageIcon from '@mui/icons-material/Storage';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import ChatIcon from '@mui/icons-material/Chat';
import SendIcon from '@mui/icons-material/Send';
import RefreshIcon from '@mui/icons-material/Refresh';
import { colors } from '../App';

const NewChat = () => {
  const { workspaceId } = useParams();

  const [error, setError] = useState(null);
  const [inputText, setInputText] = useState('');
  const [sending, setSending] = useState(false);
  const [messages, setMessages] = useState([]);
  const [workspaceInfo, setWorkspaceInfo] = useState(null);
  const messagesEndRef = useRef(null);
  
  // Cursor状态相关
  const [cursorStatus, setCursorStatus] = useState({
    isActive: false,
    isDialogOpen: false,
    lastCheck: null
  });
  const [statusCheckInterval] = useState(5000); // 5秒检查一次状态
  const statusTimerRef = useRef(null);
  
  // 对话框切换相关状态
  const [isTogglingDialog, setIsTogglingDialog] = useState(false);

  // 检查Cursor状态
  const checkCursorStatus = useCallback(async () => {
    if (!workspaceId) {
      console.log('缺少workspaceId，跳过状态检查');
      return;
    }
    
    try {
      const response = await axios.get('/api/cursor-status', {
        params: { workspace_id: workspaceId }
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
  }, [workspaceId]);

  // 启动状态检查定时器
  const startStatusTimer = useCallback(() => {
    if (!workspaceId) {
      console.log('缺少workspaceId，跳过状态检查定时器');
      return;
    }
    
    if (statusTimerRef.current) {
      clearInterval(statusTimerRef.current);
    }
    
    statusTimerRef.current = setInterval(() => {
      checkCursorStatus();
    }, statusCheckInterval);
  }, [statusCheckInterval, checkCursorStatus, workspaceId]);

  // 停止状态检查定时器
  const stopStatusTimer = () => {
    if (statusTimerRef.current) {
      clearInterval(statusTimerRef.current);
      statusTimerRef.current = null;
    }
  };

  // 切换对话框状态
  const handleToggleDialog = async () => {
    console.log('=== 开始切换对话框 ===');
    console.log('workspaceId:', workspaceId);
    
    try {
      setIsTogglingDialog(true);
      
      if (!workspaceId) {
        console.error('无法获取工作空间ID');
        alert('无法获取工作空间ID，请检查页面状态');
        return;
      }
      
      console.log('准备发送请求到 /api/cursor/dialog/toggle');
      console.log('请求数据:', { workspace_id: workspaceId });
      
      const response = await axios.post('/api/cursor/dialog/toggle', {
        workspace_id: workspaceId
      });
      
      console.log('收到响应:', response);
      
      if (response.data.success) {
        console.log('对话框状态切换成功:', response.data.message);
        
        // 更新Cursor状态
        await checkCursorStatus();
      } else {
        console.error('对话框状态切换失败:', response.data.error);
      }
    } catch (error) {
      console.error('切换对话框状态时发生错误:', error);
      console.error('错误详情:', error.response?.data || error.message);
      alert(`切换对话框失败: ${error.message}`);
    } finally {
      setIsTogglingDialog(false);
      console.log('=== 切换对话框完成 ===');
    }
  };

  // 切换Cursor状态（打开/关闭）
  const handleCursorToggle = async () => {
    console.log('=== 开始切换Cursor状态 ===');
    console.log('当前状态:', cursorStatus.isActive);
    
    try {
      if (cursorStatus.isActive) {
        // 如果Cursor已激活，尝试关闭
        console.log('尝试关闭Cursor...');
        const response = await axios.post('/api/cursor/quit');
        
        if (response.data.success) {
          console.log('Cursor关闭成功');
          await checkCursorStatus();
        } else {
          console.error('Cursor关闭失败:', response.data.error);
        }
      } else {
        // 如果Cursor未激活，尝试打开
        console.log('尝试打开Cursor...');
        const response = await axios.post('/api/cursor/open', {
          workspace_id: workspaceId
        });
        
        if (response.data.success) {
          console.log('Cursor打开成功');
          await checkCursorStatus();
        } else {
          console.error('Cursor打开失败:', response.data.error);
        }
      }
    } catch (error) {
      console.error('切换Cursor状态时发生错误:', error);
      console.error('错误详情:', error.response?.data || error.message);
      alert(`切换Cursor状态失败: ${error.message}`);
    }
  };

  // 发送消息
  const handleSendMessage = async () => {
    if (!inputText.trim() || sending) return;
    
    const userMessage = {
      role: 'user',
      content: inputText.trim(),
      timestamp: Date.now()
    };
    
    try {
      setSending(true);
      setMessages(prev => [...prev, userMessage]);
      setInputText('');
      
      // 发送消息到后端
      const response = await axios.post('/api/send-message', {
        message: userMessage.content,
        workspace_id: workspaceId
      });
      
      if (response.data.success) {
        console.log('消息发送成功');
        
        // 添加AI回复（这里可以根据实际需求调整）
        const aiMessage = {
          role: 'assistant',
          content: '消息已发送到Cursor，请查看Cursor中的回复。',
          timestamp: Date.now()
        };
        setMessages(prev => [...prev, aiMessage]);
      } else {
        console.error('消息发送失败:', response.data.error);
        setError('消息发送失败: ' + response.data.error);
      }
    } catch (error) {
      console.error('发送消息时发生错误:', error);
      setError('发送消息失败: ' + error.message);
    } finally {
      setSending(false);
    }
  };

  // 获取工作空间信息
  const fetchWorkspaceInfo = useCallback(async () => {
    if (!workspaceId) return;
    
    try {
      console.log('获取工作空间信息，workspaceId:', workspaceId);
      const response = await axios.get(`/api/workspace/${workspaceId}/info`);
      
      if (response.data.success) {
        const data = response.data;
        console.log('工作空间信息:', data);
        
        setWorkspaceInfo({
          name: data.project.name,
          rootPath: data.project.rootPath,
          workspaceId: data.workspace_id
        });
      } else {
        console.error('获取工作空间信息失败:', response.data.error);
        // 如果API失败，使用默认信息
        setWorkspaceInfo({
          name: 'Unknown Project',
          rootPath: '/unknown/path',
          workspaceId: workspaceId
        });
      }
    } catch (error) {
      console.error('获取工作空间信息失败:', error);
      // 如果请求失败，使用默认信息
      setWorkspaceInfo({
        name: 'Unknown Project',
        rootPath: '/unknown/path',
        workspaceId: workspaceId
      });
    }
  }, [workspaceId]);

  // 初始化
  useEffect(() => {
    console.log('NewChat useEffect 执行 - workspaceId:', workspaceId);
    
    if (!workspaceId) {
      setError('缺少工作空间ID');
      return;
    }
    
    fetchWorkspaceInfo();
    checkCursorStatus();
    startStatusTimer();
    
    // 清理函数
    return () => {
      stopStatusTimer();
    };
  }, [workspaceId, fetchWorkspaceInfo, checkCursorStatus, startStatusTimer]);

  // 自动滚动到对话底部
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  if (error) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography variant="h6" color="error" gutterBottom>
            页面加载失败
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

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
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
        
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          {/* Cursor状态指示器 + 打开/关闭按钮 */}
          <Tooltip title={cursorStatus.isActive ? "点击关闭Cursor" : "点击打开Cursor"}>
            <Box
              onClick={() => handleCursorToggle()}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                p: 1.5,
                borderRadius: 2,
                cursor: 'pointer',
                backgroundColor: cursorStatus.isActive ? alpha(colors.success.main, 0.1) : alpha(colors.error.main, 0.1),
                border: `1px solid ${cursorStatus.isActive ? colors.success.main : colors.error.main}`,
                transition: 'all 0.2s ease',
                '&:hover': {
                  backgroundColor: cursorStatus.isActive ? alpha(colors.success.main, 0.2) : alpha(colors.error.main, 0.2),
                  transform: 'translateY(-1px)',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
                },
                '&:active': {
                  transform: 'translateY(0)',
                }
              }}
            >
              <Box sx={{ 
                width: 10, 
                height: 10, 
                borderRadius: '50%', 
                backgroundColor: cursorStatus.isActive ? colors.success.main : colors.error.main,
                boxShadow: cursorStatus.isActive ? '0 0 8px rgba(76, 175, 80, 0.6)' : '0 0 8px rgba(244, 67, 54, 0.6)',
              }} />
              <Typography 
                variant="body2" 
                sx={{ 
                  fontWeight: 600,
                  color: cursorStatus.isActive ? colors.success.main : colors.error.main,
                  userSelect: 'none'
                }}
              >
                Cursor: {cursorStatus.isActive ? '已激活' : '未激活'}
              </Typography>
            </Box>
          </Tooltip>
          
          {/* AI对话框状态指示器 + 切换按钮 */}
          <Tooltip title="切换AI对话框 (Command+I)">
            <Box
              onClick={handleToggleDialog}
              sx={{
                display: 'flex',
                alignItems: 'center',
                gap: 1,
                p: 1.5,
                borderRadius: 2,
                cursor: isTogglingDialog ? 'not-allowed' : 'pointer',
                backgroundColor: cursorStatus.isDialogOpen ? alpha(colors.success.main, 0.1) : alpha(colors.warning.main, 0.1),
                border: `1px solid ${cursorStatus.isDialogOpen ? colors.success.main : colors.warning.main}`,
                transition: 'all 0.2s ease',
                opacity: isTogglingDialog ? 0.6 : 1,
                '&:hover': {
                  backgroundColor: isTogglingDialog ? undefined : (cursorStatus.isDialogOpen ? alpha(colors.success.main, 0.2) : alpha(colors.warning.main, 0.2)),
                  transform: isTogglingDialog ? undefined : 'translateY(-1px)',
                  boxShadow: isTogglingDialog ? undefined : '0 2px 8px rgba(0,0,0,0.2)',
                },
                '&:active': {
                  transform: isTogglingDialog ? undefined : 'translateY(0)',
                }
              }}
            >
              {isTogglingDialog ? (
                <CircularProgress size={16} sx={{ color: colors.warning.main }} />
              ) : (
                <ChatIcon sx={{ 
                  color: cursorStatus.isDialogOpen ? colors.success.main : colors.warning.main,
                  fontSize: 20
                }} />
              )}
              <Typography 
                variant="body2" 
                sx={{ 
                  fontWeight: 600,
                  color: cursorStatus.isDialogOpen ? colors.success.main : colors.warning.main,
                  userSelect: 'none'
                }}
              >
                AI对话框: {cursorStatus.isDialogOpen ? '已打开' : '未打开'}
              </Typography>
            </Box>
          </Tooltip>
          
          {/* 手动刷新状态按钮 */}
          <Tooltip title="刷新状态">
            <IconButton
              onClick={checkCursorStatus}
              size="small"
              sx={{
                color: colors.highlightColor,
                backgroundColor: alpha(colors.highlightColor, 0.1),
                border: `1px solid ${alpha(colors.highlightColor, 0.3)}`,
                '&:hover': {
                  backgroundColor: alpha(colors.highlightColor, 0.2),
                  transform: 'translateY(-1px)',
                  boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
                },
                '&:active': {
                  transform: 'translateY(0)',
                }
              }}
            >
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* 工作空间信息 */}
      {workspaceInfo && (
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
                {workspaceInfo.name}
              </Typography>
              <Chip
                icon={<StorageIcon />}
                label="新对话"
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
                  <strong>Path:</strong> {workspaceInfo.rootPath}
                </Typography>
              </Box>
              
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <StorageIcon sx={{ mr: 0.5, color: colors.highlightColor, opacity: 0.8, fontSize: 18 }} />
                <Typography variant="body2" color="text.secondary">
                  <strong>Workspace:</strong> {workspaceInfo.workspaceId}
                </Typography>
              </Box>
            </Box>
          </Box>
        </Paper>
      )}

      {/* 状态提示 */}
      {!cursorStatus.isActive && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          Cursor 未激活，请确保 Cursor 正在运行并且可以访问。
        </Alert>
      )}

      {/* 对话输入区域 */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h5" gutterBottom sx={{ mb: 3, color: colors.highlightColor }}>
          新对话
        </Typography>
        
        {/* 消息列表 */}
        {messages.length > 0 && (
          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom sx={{ mb: 2 }}>
              对话记录
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
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
                      width: 32,
                      height: 32,
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
          </Box>
        )}
        
        {/* 输入框 */}
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'flex-end' }}>
          <TextField
            fullWidth
            multiline
            rows={3}
            variant="outlined"
            placeholder="输入你的消息..."
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            onKeyPress={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            disabled={sending || !cursorStatus.isActive}
            sx={{
              '& .MuiOutlinedInput-root': {
                borderRadius: 2,
              }
            }}
          />
          <Button
            onClick={handleSendMessage}
            disabled={!inputText.trim() || sending || !cursorStatus.isActive}
            variant="contained"
            color="highlight"
            startIcon={sending ? <CircularProgress size={20} /> : <SendIcon />}
            sx={{ 
              borderRadius: 2,
              minWidth: 100,
              height: 56,
              '&:hover': {
                backgroundColor: alpha(colors.highlightColor, 0.8),
              }
            }}
          >
            {sending ? '发送中...' : '发送'}
          </Button>
        </Box>
        
        <div ref={messagesEndRef} />
      </Paper>
    </Container>
  );
};

export default NewChat;
