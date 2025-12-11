import React, { useEffect, useState, useMemo } from 'react';
import { 
  Box, Button, Typography, Dialog, DialogTitle, DialogContent, DialogContentText,
  DialogActions, TextField, Chip, Stack, Snackbar, Alert, IconButton, Switch, FormControlLabel, Paper
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { zhTW } from '@mui/x-data-grid/locales';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import RefreshIcon from '@mui/icons-material/Refresh';
import ContentCopyIcon from '@mui/icons-material/ContentCopy';
import apiClient from '../api/client';

const DeviceManagement = () => {
  const [devices, setDevices] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const [open, setOpen] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [currentId, setCurrentId] = useState(null);
  const [formData, setFormData] = useState({ device_name: '', location: '', is_active: true });
  
  const [errors, setErrors] = useState({});

  const [tokenDialog, setTokenDialog] = useState({ open: false, token: '', deviceName: '' });
  const [confirmDialog, setConfirmDialog] = useState({ 
    open: false, type: '', targetId: null, targetName: '' 
  });
  const [msg, setMsg] = useState({ open: false, txt: '', type: 'success' });

  const fetchDevices = async () => {
    if (devices.length === 0) setLoading(true);
    try { 
      const res = await apiClient.get('/devices/'); 
      setDevices(res.data); 
    } catch (e) { console.error(e); } finally { setLoading(false); }
  };

  useEffect(() => { fetchDevices(); }, []);

  const validate = () => {
    let tempErrors = {};
    if (!formData.device_name.trim()) tempErrors.device_name = "設備名稱為必填欄位";
    if (!formData.location.trim()) tempErrors.location = "安裝位置為必填欄位";
    setErrors(tempErrors);
    return Object.keys(tempErrors).length === 0;
  };

  const handleOpenAdd = () => {
    setIsEditMode(false);
    setFormData({ device_name: '', location: '', is_active: true });
    setErrors({});
    setOpen(true);
  };

  const handleOpenEdit = (row) => {
    setIsEditMode(true);
    setCurrentId(row.id);
    setFormData({ device_name: row.device_name, location: row.location, is_active: row.is_active });
    setErrors({});
    setOpen(true);
  };

  const handleClickDelete = (id, name) => {
    setConfirmDialog({ open: true, type: 'DELETE', targetId: id, targetName: name });
  };

  const handleClickReset = (id, name) => {
    setConfirmDialog({ open: true, type: 'RESET', targetId: id, targetName: name });
  };

  const handleConfirmAction = async () => {
    const { type, targetId, targetName } = confirmDialog;
    try {
      if (type === 'DELETE') {
        await apiClient.delete(`/devices/${targetId}`);
        setMsg({ open: true, txt: '刪除成功', type: 'success' });
      } else if (type === 'RESET') {
        const res = await apiClient.post(`/devices/${targetId}/reset-token`);
        setTokenDialog({ open: true, token: res.data.token, deviceName: targetName });
        setMsg({ open: true, txt: 'Token 重設成功', type: 'success' });
      }
      fetchDevices();
    } catch (e) {
      setMsg({ open: true, txt: '操作失敗', type: 'error' });
    } finally {
      setConfirmDialog({ ...confirmDialog, open: false });
    }
  };

  const handleSubmit = async () => {
    if (!validate()) return;

    try {
      if (isEditMode) {
        await apiClient.put(`/devices/${currentId}`, formData);
        setMsg({ open: true, txt: '更新成功', type: 'success' });
      } else {
        const res = await apiClient.post('/devices/', formData);
        setTokenDialog({ open: true, token: res.data.token, deviceName: res.data.device_name });
        setMsg({ open: true, txt: '新增成功', type: 'success' });
      }
      setOpen(false);
      fetchDevices();
    } catch (e) {
      setMsg({ open: true, txt: '操作失敗 (名稱可能重複)', type: 'error' });
    }
  };

  const copyToken = () => {
    navigator.clipboard.writeText(tokenDialog.token);
    setMsg({ open: true, txt: '已複製到剪貼簿', type: 'success' });
  };

  const columns = useMemo(() => [
    { field: 'device_name', headerName: '設備名稱', width: 150 },
    { field: 'location', headerName: '位置', width: 150 },
    { 
      field: 'token_status', headerName: 'Token', width: 150, sortable: false,
      renderCell: () => <Typography variant="caption" color="text.secondary">●●●●●● (已隱藏)</Typography>
    },
    { 
      field: 'is_active', headerName: '狀態', width: 100, 
      renderCell: (p) => <Chip label={p.value?"啟用":"停用"} color={p.value?"success":"default"} size="small"/> 
    },
    {
      field: 'actions', headerName: '操作', width: 180, sortable: false,
      renderCell: (p) => (
        <>
          <IconButton color="primary" onClick={() => handleOpenEdit(p.row)} title="編輯資訊"><EditIcon /></IconButton>
          <IconButton color="warning" onClick={() => handleClickReset(p.row.id, p.row.device_name)} title="重設 Token"><RefreshIcon /></IconButton>
          <IconButton color="error" onClick={() => handleClickDelete(p.row.id, p.row.device_name)} title="刪除設備"><DeleteIcon /></IconButton>
        </>
      ),
    },
  ], []);

  return (
    <Box sx={{ height: 600, width: '100%' }}>
      <Stack direction="row" justifyContent="space-between" mb={2}>
        <Typography variant="h5">設備管理</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleOpenAdd}>
          新增設備
        </Button>
      </Stack>
      
      <DataGrid 
        rows={devices} columns={columns} loading={loading} disableRowSelectionOnClick 
        sortingOrder={['asc', 'desc']}
        localeText={zhTW.components.MuiDataGrid.defaultProps.localeText}
      />
      
      {/* 新增/編輯 Dialog */}
      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>{isEditMode ? '編輯設備資訊' : '新增設備'}</DialogTitle>
        <DialogContent>
          <TextField 
            margin="dense" label="設備名稱 (ID)" fullWidth required
            value={formData.device_name} 
            onChange={e => setFormData({...formData, device_name: e.target.value})} 
            helperText={errors.device_name || "ESP32 程式碼中的 DEVICE_ID"}
            error={!!errors.device_name}
          />
          <TextField 
            margin="dense" label="安裝位置" fullWidth required
            value={formData.location} 
            onChange={e => setFormData({...formData, location: e.target.value})} 
            helperText={errors.location}
            error={!!errors.location}
          />
          <FormControlLabel control={<Switch checked={formData.is_active} onChange={e => setFormData({...formData, is_active: e.target.checked})} />} label="啟用設備" sx={{ mt: 2 }} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>取消</Button>
          <Button variant="contained" onClick={handleSubmit}>{isEditMode?'更新':'建立'}</Button>
        </DialogActions>
      </Dialog>

      {/* 確認刪除/重設 Dialog */}
      <Dialog open={confirmDialog.open} onClose={() => setConfirmDialog({...confirmDialog, open: false})}>
        <DialogTitle>
          {confirmDialog.type === 'DELETE' ? '確認刪除' : '確認重設 Token'}
        </DialogTitle>
        <DialogContent>
          <DialogContentText>
            {confirmDialog.type === 'DELETE' 
              ? `確定要刪除設備 [${confirmDialog.targetName}] 嗎？此操作無法復原。`
              : `確定要重設 [${confirmDialog.targetName}] 的 Token 嗎？舊的 Token 將立即失效。`
            }
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfirmDialog({...confirmDialog, open: false})}>取消</Button>
          <Button onClick={handleConfirmAction} color={confirmDialog.type==='DELETE'?'error':'warning'} variant="contained" autoFocus>
            確認
          </Button>
        </DialogActions>
      </Dialog>

      {/* Token 顯示 Dialog */}
      <Dialog open={tokenDialog.open} onClose={() => {}}> 
        <DialogTitle sx={{ bgcolor: '#e3f2fd' }}>⚠️ 請保存您的 Token</DialogTitle>
        <DialogContent sx={{ mt: 2, minWidth: 400 }}>
          <DialogContentText sx={{ mb: 2 }}>
            設備 <strong>{tokenDialog.deviceName}</strong> 的驗證 Token 已產生。<br/>
            基於安全考量，<strong>此 Token 只會顯示這一次</strong>。
          </DialogContentText>
          <Paper variant="outlined" sx={{ p: 2, display: 'flex', alignItems: 'center', bgcolor: '#f5f5f5' }}>
            <Typography variant="body1" sx={{ fontFamily: 'monospace', flexGrow: 1, wordBreak: 'break-all' }}>
              {tokenDialog.token}
            </Typography>
            <IconButton onClick={copyToken} color="primary"><ContentCopyIcon /></IconButton>
          </Paper>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTokenDialog({ ...tokenDialog, open: false })} variant="contained" color="primary">我已複製，關閉視窗</Button>
        </DialogActions>
      </Dialog>
      
      <Snackbar open={msg.open} autoHideDuration={3000} onClose={() => setMsg({...msg, open: false})}><Alert severity={msg.type}>{msg.txt}</Alert></Snackbar>
    </Box>
  );
};

export default DeviceManagement;