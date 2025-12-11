import React, { useState } from 'react';
import { 
  Box, Drawer, AppBar, Toolbar, List, Typography, ListItem, 
  ListItemButton, ListItemIcon, ListItemText, CssBaseline, 
  IconButton, Menu, MenuItem, Dialog, DialogTitle, DialogContent, 
  DialogActions, TextField, Button, Snackbar, Alert, Divider
} from '@mui/material';
import { 
  Dashboard, People, History, SettingsRemote, 
  AccountCircle, LockReset, Logout
} from '@mui/icons-material';
import { useNavigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../auth/AuthContext';
import apiClient from '../api/client';

const drawerWidth = 240;

const MainLayout = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { logout, user } = useAuth();

  const [anchorEl, setAnchorEl] = useState(null);
  const [pwdOpen, setPwdOpen] = useState(false);
  const [pwdData, setPwdData] = useState({ old_password: '', new_password: '', confirm_password: '' });
  const [msg, setMsg] = useState({ open: false, txt: '', type: 'success' });

  const handleMenuOpen = (event) => setAnchorEl(event.currentTarget);
  const handleMenuClose = () => setAnchorEl(null);

  const handleLogout = () => {
    handleMenuClose();
    logout();
    navigate('/login');
  };

  const handleOpenPwdDialog = () => {
    handleMenuClose();
    setPwdData({ old_password: '', new_password: '', confirm_password: '' });
    setPwdOpen(true);
  };

  const handleChangePassword = async () => {
    // 檢查必填
    if (!pwdData.old_password || !pwdData.new_password) {
      setMsg({ open: true, txt: '請填寫所有欄位', type: 'error' });
      return;
    }
    
    // 檢查新舊密碼是否相同
    if (pwdData.old_password === pwdData.new_password) {
      setMsg({ open: true, txt: '新密碼不可與舊密碼相同', type: 'error' });
      return;
    }

    // 檢查確認密碼
    if (pwdData.new_password !== pwdData.confirm_password) {
      setMsg({ open: true, txt: '新密碼與確認密碼不符', type: 'error' });
      return;
    }

    try {
      await apiClient.post('/auth/change-password', {
        old_password: pwdData.old_password,
        new_password: pwdData.new_password
      });
      setMsg({ open: true, txt: '密碼修改成功，請重新登入', type: 'success' });
      setPwdOpen(false);
      setTimeout(() => {
        logout();
        navigate('/login');
      }, 1500);
    } catch (e) {
      const errorMsg = e.response?.data?.detail || '修改失敗';
      setMsg({ open: true, txt: errorMsg, type: 'error' });
    }
  };

  const menuItems = [
    { text: '儀表板', icon: <Dashboard />, path: '/' },
    { text: '學生管理', icon: <People />, path: '/users' },
    { text: '設備管理', icon: <SettingsRemote />, path: '/devices' },
    { text: '刷卡紀錄', icon: <History />, path: '/logs' },
  ];

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar sx={{ justifyContent: 'space-between' }}>
          <Typography variant="h6" noWrap component="div">
            ESP32 門禁管理系統
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            {user && (
              <Typography variant="body1" sx={{ mr: 2, display: { xs: 'none', sm: 'block' } }}>
                歡迎, <strong>{user}</strong>
              </Typography>
            )}

            <IconButton
              size="large"
              aria-label="account of current user"
              aria-controls="menu-appbar"
              aria-haspopup="true"
              onClick={handleMenuOpen}
              color="inherit"
            >
              <AccountCircle />
            </IconButton>
            <Menu
              id="menu-appbar"
              anchorEl={anchorEl}
              anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
              keepMounted
              transformOrigin={{ vertical: 'top', horizontal: 'right' }}
              open={Boolean(anchorEl)}
              onClose={handleMenuClose}
            >
              <MenuItem onClick={handleOpenPwdDialog}>
                <ListItemIcon><LockReset fontSize="small" /></ListItemIcon>
                修改密碼
              </MenuItem>
              <Divider />
              <MenuItem onClick={handleLogout}>
                <ListItemIcon><Logout fontSize="small" /></ListItemIcon>
                登出
              </MenuItem>
            </Menu>
          </Box>
        </Toolbar>
      </AppBar>

      <Drawer
        variant="permanent"
        sx={{
          width: drawerWidth, flexShrink: 0,
          [`& .MuiDrawer-paper`]: { width: drawerWidth, boxSizing: 'border-box' },
        }}
      >
        <Toolbar /> 
        <Box sx={{ overflow: 'auto' }}>
          <List>
            {menuItems.map((item) => (
              <ListItem key={item.text} disablePadding>
                <ListItemButton 
                  selected={location.pathname === item.path}
                  onClick={() => navigate(item.path)}
                >
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.text} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, p: 3 }}>
        <Toolbar />
        <Outlet />
      </Box>

      {/* 修改密碼 Dialog */}
      <Dialog open={pwdOpen} onClose={() => setPwdOpen(false)}>
        <DialogTitle>修改密碼</DialogTitle>
        <DialogContent sx={{ minWidth: 350 }}>
          <TextField
            margin="dense" label="舊密碼" type="password" fullWidth
            value={pwdData.old_password}
            onChange={(e) => setPwdData({...pwdData, old_password: e.target.value})}
          />
          <TextField
            margin="dense" label="新密碼" type="password" fullWidth
            value={pwdData.new_password}
            onChange={(e) => setPwdData({...pwdData, new_password: e.target.value})}
          />
          <TextField
            margin="dense" label="確認新密碼" type="password" fullWidth
            value={pwdData.confirm_password}
            onChange={(e) => setPwdData({...pwdData, confirm_password: e.target.value})}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPwdOpen(false)}>取消</Button>
          <Button onClick={handleChangePassword} variant="contained">確認修改</Button>
        </DialogActions>
      </Dialog>

      <Snackbar open={msg.open} autoHideDuration={3000} onClose={() => setMsg({...msg, open: false})}>
        <Alert severity={msg.type}>{msg.txt}</Alert>
      </Snackbar>
    </Box>
  );
};

export default MainLayout;