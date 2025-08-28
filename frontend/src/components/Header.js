import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { AppBar, Toolbar, Typography, Box, Container, Button, Chip, Tooltip } from '@mui/material';
import ChatIcon from '@mui/icons-material/Chat';
import GitHubIcon from '@mui/icons-material/GitHub';
import BugReportIcon from '@mui/icons-material/BugReport';
import WifiIcon from '@mui/icons-material/Wifi';
import { colors } from '../App';

const Header = () => {
  const [serverInfo, setServerInfo] = useState(null);

  useEffect(() => {
    // 获取服务器信息
    const fetchServerInfo = async () => {
      try {
        const response = await fetch('/api/server/info');
        if (response.ok) {
          const data = await response.json();
          setServerInfo(data);
        }
      } catch (error) {
        console.error('获取服务器信息失败:', error);
      }
    };

    fetchServerInfo();
  }, []);

  return (
    <AppBar position="static" sx={{ mb: 4 }}>
      <Container>
        <Toolbar sx={{ p: { xs: 1, sm: 1.5 }, px: { xs: 1, sm: 0 } }}>
          <Box component={Link} to="/" sx={{ 
            display: 'flex', 
            alignItems: 'center', 
            textDecoration: 'none', 
            color: 'inherit',
            flexGrow: 1,
            '&:hover': {
              textDecoration: 'none'
            }
          }}>
            <ChatIcon sx={{ mr: 1.5, fontSize: 28 }} />
            <Typography variant="h5" component="div" fontWeight="700">
              Cursor View
            </Typography>
          </Box>
          
          {/* 服务器信息显示 */}
          {serverInfo && (
            <Box sx={{ display: 'flex', alignItems: 'center', mr: 2 }}>
              <Tooltip title={`局域网访问: ${serverInfo.lan_url}`}>
                <Chip
                  icon={<WifiIcon />}
                  label={`${serverInfo.local_ip}:${serverInfo.port}`}
                  size="small"
                  sx={{
                    backgroundColor: 'rgba(255,255,255,0.2)',
                    color: 'white',
                    border: '1px solid rgba(255,255,255,0.3)',
                    '&:hover': {
                      backgroundColor: 'rgba(255,255,255,0.3)',
                    }
                  }}
                />
              </Tooltip>
            </Box>
          )}
          
          <Button 
            component={Link}
            to="/cursor-debug"
            startIcon={<BugReportIcon />}
            variant="outlined"
            color="inherit"
            size="small"
            sx={{ 
              borderColor: 'rgba(255,255,255,0.5)', 
              color: 'white',
              mr: 2,
              '&:hover': { 
                borderColor: 'rgba(255,255,255,0.8)',
                backgroundColor: colors.highlightColor
              }
            }}
          >
            Cursor调试
          </Button>
          
          <Button 
            component="a"
            href="https://github.com/saharmor/cursor-view"
            target="_blank"
            rel="noopener noreferrer"
            startIcon={<GitHubIcon />}
            variant="outlined"
            color="inherit"
            size="small"
            sx={{ 
              borderColor: 'rgba(255,255,255,0.5)', 
              color: 'white',
              '&:hover': { 
                borderColor: 'rgba(255,255,255,0.8)',
                backgroundColor: colors.highlightColor
              }
            }}
          >
            GitHub
          </Button>
        </Toolbar>
      </Container>
    </AppBar>
  );
};

export default Header;