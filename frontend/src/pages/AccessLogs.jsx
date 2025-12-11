import React, { useEffect, useState, useMemo } from 'react';
import { Box, Typography, Chip, Button, Stack } from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { zhTW } from '@mui/x-data-grid/locales';
import DownloadIcon from '@mui/icons-material/Download';
import apiClient from '../api/client';
import dayjs from 'dayjs';

const AccessLogs = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  const fetchLogs = async () => {
    if (logs.length === 0) setLoading(true);
    try {
      const res = await apiClient.get('/access/logs');
      setLogs(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
    const interval = setInterval(fetchLogs, 5000); 
    return () => clearInterval(interval);
  }, []);

  const handleExport = async () => {
    try {
      const response = await apiClient.get('/access/export', {
        responseType: 'blob',
      });

      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      
      const dateStr = dayjs().format('YYYYMMDD_HHmm');
      link.setAttribute('download', `access_logs_${dateStr}.csv`);
      
      document.body.appendChild(link);
      link.click();
      
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error("匯出失敗", error);
      alert("匯出失敗，請稍後再試");
    }
  };

  const columns = useMemo(() => [
    { 
      field: 'timestamp', 
      headerName: '時間', 
      width: 200, 
      valueFormatter: (value) => {
        if (!value) return '';
        return dayjs(value).format('YYYY-MM-DD HH:mm:ss');
      }
    },
    { field: 'user_name', headerName: '姓名', width: 150 },
    { 
      field: 'card_uid', 
      headerName: '卡號 (UID)', 
      width: 150,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', height: '100%' }}>
          {params.value ? (
            <Typography variant="body2" sx={{ fontFamily: 'monospace' }}>
              {params.value}
            </Typography>
          ) : params.row.method === 'TELEGRAM' ? (
            <Typography variant="caption" color="primary" sx={{ fontStyle: 'italic' }}>
              (遠端操作)
            </Typography>
          ) : (
            <Typography variant="caption" color="text.secondary">-</Typography>
          )}
        </Box>
      )
    },
    { field: 'method', headerName: '方式', width: 100 },
    { 
      field: 'status', 
      headerName: '結果', 
      width: 120, 
      renderCell: (params) => (
        <Chip 
          label={params.value} 
          color={params.value === 'SUCCESS' ? 'success' : 'error'} 
          size="small" 
        />
      ) 
    },
    { field: 'details', headerName: '詳細訊息', width: 300 },
  ], []);

  return (
    <Box sx={{ height: 600, width: '100%' }}>
      <Stack direction="row" justifyContent="space-between" mb={2}>
        <Typography variant="h5">刷卡紀錄</Typography>
        <Button 
          variant="outlined" 
          startIcon={<DownloadIcon />} 
          onClick={handleExport}
        >
          匯出 CSV
        </Button>
      </Stack>

      <DataGrid 
        rows={logs} 
        columns={columns} 
        loading={loading}
        disableRowSelectionOnClick 
        sortingOrder={['desc', 'asc']}
        initialState={{ 
          sorting: { sortModel: [{ field: 'timestamp', sort: 'desc' }] } 
        }} 
        localeText={zhTW.components.MuiDataGrid.defaultProps.localeText}
      />
    </Box>
  );
};

export default AccessLogs;