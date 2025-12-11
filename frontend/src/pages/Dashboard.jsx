import React, { useEffect, useState } from 'react';
import { Box, Typography, Grid, Paper, CircularProgress, Chip } from '@mui/material';
import { People, History, Dns, CheckCircle, Error as ErrorIcon } from '@mui/icons-material';
import apiClient from '../api/client';
import dayjs from 'dayjs';

const StatCard = ({ title, value, icon, color }) => (
  <Paper
    elevation={3}
    sx={{
      p: 3, display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 120,
      background: `linear-gradient(135deg, ${color} 0%, ${color}DD 100%)`, color: '#fff'
    }}
  >
    <Box>
      <Typography variant="h6" sx={{ opacity: 0.8, mb: 1 }}>{title}</Typography>
      <Typography variant="h4" fontWeight="bold">{value}</Typography>
    </Box>
    <Box sx={{ opacity: 0.3, transform: 'scale(2)' }}>{icon}</Box>
  </Paper>
);

const Dashboard = () => {
  const [stats, setStats] = useState({ userCount: 0, logCount: 0, todayCount: 0 });
  const [loading, setLoading] = useState(true);
  
  // 後端連線狀態 (預設為 false)
  const [isOnline, setIsOnline] = useState(false);

  const fetchData = async () => {
    try {
      const [usersRes, logsRes] = await Promise.all([
        apiClient.get('/users/'),
        apiClient.get('/access/logs?limit=1000')
      ]);
      const users = usersRes.data;
      const logs = logsRes.data;
      const today = dayjs().format('YYYY-MM-DD');
      const todayLogs = logs.filter(log => dayjs(log.timestamp).format('YYYY-MM-DD') === today);

      setStats({ userCount: users.length, logCount: logs.length, todayCount: todayLogs.length });
      
      setIsOnline(true);
    } catch (error) { 
      console.error("無法取得儀表板資料 (後端可能離線)", error); 
      setIsOnline(false);
    } finally { 
      setLoading(false); 
    }
  };

  useEffect(() => {
    fetchData();
    // 每 5 秒檢查一次
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Box>
      <Typography variant="h4" gutterBottom sx={{ mb: 4, fontWeight: 'bold' }}>系統儀表板</Typography>
      
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 10 }}><CircularProgress /></Box>
      ) : (
        <Grid container spacing={3}>
          <Grid item xs={12} md={4}>
            <StatCard title="學生總數" value={isOnline ? stats.userCount : '-'} icon={<People />} color="#1976d2" />
          </Grid>
          <Grid item xs={12} md={4}>
            <StatCard title="歷史刷卡次數" value={isOnline ? stats.logCount : '-'} icon={<History />} color="#2e7d32" />
          </Grid>
          <Grid item xs={12} md={4}>
            <StatCard title="今日進出次數" value={isOnline ? stats.todayCount : '-'} icon={<Dns />} color="#ed6c02" />
          </Grid>
        </Grid>
      )}

      <Box sx={{ mt: 5, display: 'flex', alignItems: 'center', gap: 1 }}>
        <Typography variant="body2" color="text.secondary">
          後端服務狀態：
        </Typography>
        
        {isOnline ? (
          <Chip 
            icon={<CheckCircle style={{ color: 'white' }} />} 
            label="已連線 (Online)" 
            color="success" 
            size="small" 
          />
        ) : (
          <Chip 
            icon={<ErrorIcon style={{ color: 'white' }} />} 
            label="連線失敗 (Offline)" 
            color="error" 
            size="small" 
          />
        )}
        
        <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
           (Port 8000)
        </Typography>
      </Box>
    </Box>
  );
};

export default Dashboard;