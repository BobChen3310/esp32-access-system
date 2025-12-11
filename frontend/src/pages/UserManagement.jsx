import React, { useEffect, useState, useMemo } from 'react';
import { 
  Box, Button, Typography, Dialog, DialogTitle, DialogContent, 
  DialogActions, TextField, Chip, Stack, Snackbar, Alert, IconButton, Switch, FormControlLabel,
  Select, MenuItem, InputLabel, FormControl, OutlinedInput, Checkbox, ListItemText
} from '@mui/material';
import { DataGrid } from '@mui/x-data-grid';
import { zhTW } from '@mui/x-data-grid/locales';
import AddIcon from '@mui/icons-material/Add';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import apiClient from '../api/client';

const UserManagement = () => {
  const [users, setUsers] = useState([]);
  const [allDevices, setAllDevices] = useState([]);
  const [loading, setLoading] = useState(false);
  
  const [open, setOpen] = useState(false);
  const [isEditMode, setIsEditMode] = useState(false);
  const [currentId, setCurrentId] = useState(null);

  const [formData, setFormData] = useState({ 
    student_id: '', name: '', email: '', card_uid: '', 
    is_active: true, accessible_device_ids: [] 
  });

  const [errors, setErrors] = useState({});
  const [msg, setMsg] = useState({ open: false, txt: '', type: 'success' });

  const fetchData = async () => {
    if (users.length === 0) setLoading(true);
    try {
      const [usersRes, devicesRes] = await Promise.all([
        apiClient.get('/users/'),
        apiClient.get('/devices/')
      ]);
      setUsers(usersRes.data);
      setAllDevices(devicesRes.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, []);

  const validate = () => {
    let tempErrors = {};
    if (!formData.student_id.trim()) tempErrors.student_id = "學號為必填欄位";
    if (!formData.name.trim()) tempErrors.name = "姓名為必填欄位";
    setErrors(tempErrors);
    return Object.keys(tempErrors).length === 0;
  };

  const handleOpenAdd = () => {
    setIsEditMode(false);
    setFormData({ 
      student_id: '', name: '', email: '', card_uid: '', 
      is_active: true, accessible_device_ids: [] 
    });
    setErrors({});
    setOpen(true);
  };

  const handleOpenEdit = (row) => {
    setIsEditMode(true);
    setCurrentId(row.id);
    setFormData({ 
      student_id: row.student_id, 
      name: row.name, 
      email: row.email || '',
      card_uid: row.card_uid || '', 
      is_active: row.is_active,
      accessible_device_ids: row.accessible_device_ids || [] 
    });
    setErrors({});
    setOpen(true);
  };

  const handleDelete = async (id) => {
    if (!window.confirm("確定要刪除此學生嗎？")) return;
    try {
      await apiClient.delete(`/users/${id}`);
      setMsg({ open: true, txt: '刪除成功', type: 'success' });
      fetchData();
    } catch (e) {
      setMsg({ open: true, txt: '刪除失敗', type: 'error' });
    }
  };

  const handleSubmit = async () => {
    if (!validate()) return;
    try {
      if (isEditMode) {
        await apiClient.put(`/users/${currentId}`, formData);
      } else {
        await apiClient.post('/users/', formData);
      }
      setMsg({ open: true, txt: isEditMode ? '更新成功' : '新增成功', type: 'success' });
      setOpen(false);
      fetchData();
    } catch (e) {
      const errorDetail = e.response?.data?.detail || '操作失敗';
      setMsg({ open: true, txt: `操作失敗: ${errorDetail}`, type: 'error' });
    }
  };

  const handleDeviceChange = (event) => {
    const { value } = event.target;
    setFormData({
      ...formData,
      accessible_device_ids: typeof value === 'string' ? value.split(',') : value,
    });
  };

  const columns = useMemo(() => [
    { field: 'student_id', headerName: '學號', width: 130 },
    { field: 'name', headerName: '姓名', width: 130 },
    { field: 'email', headerName: 'Email', width: 200 },
    { 
      field: 'accessible_device_names', 
      headerName: '可通行設備', 
      width: 250,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', gap: 0.5, alignItems: 'center', height: '100%', overflowX: 'auto' }}>
          {params.value && params.value.length > 0 ? (
            params.value.map((dName, idx) => (
              <Chip key={idx} label={dName} size="small" variant="outlined" />
            ))
          ) : (
            <Typography variant="caption" color="text.secondary">(無權限)</Typography>
          )}
        </Box>
      )
    },
    { 
      field: 'card_uid', 
      headerName: '卡號', 
      width: 180,
      renderCell: (params) => (
        <Box sx={{ display: 'flex', alignItems: 'center', height: '100%' }}>
          {params.value ? (
            <Typography variant="body2" component="span" sx={{ fontFamily: 'monospace' }}>
              {params.value}
            </Typography>
          ) : (
            <Typography variant="caption" color="text.secondary">
              (未綁定)
            </Typography>
          )}
        </Box>
      )
    },
    { 
      field: 'is_active', 
      headerName: '狀態', 
      width: 90, 
      renderCell: (params) => (
        <Chip 
          label={params.value ? "啟用" : "停用"} 
          color={params.value ? "success" : "default"} 
          size="small" 
        />
      ) 
    },
    {
      field: 'actions', 
      headerName: '操作', 
      width: 120, 
      sortable: false,
      renderCell: (params) => (
        <>
          <IconButton color="primary" onClick={() => handleOpenEdit(params.row)}>
            <EditIcon />
          </IconButton>
          <IconButton color="error" onClick={() => handleDelete(params.row.id)}>
            <DeleteIcon />
          </IconButton>
        </>
      ),
    },
  ], []); // 空依賴陣列，確保 columns 永遠不變

  return (
    <Box sx={{ height: 600, width: '100%' }}>
      <Stack direction="row" justifyContent="space-between" mb={2}>
        <Typography variant="h5">學生管理</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={handleOpenAdd}>
          新增學生
        </Button>
      </Stack>
      
      <DataGrid 
        rows={users} 
        columns={columns} 
        loading={loading}
        disableRowSelectionOnClick
        sortingOrder={['asc', 'desc']}
        localeText={zhTW.components.MuiDataGrid.defaultProps.localeText}
      />
      
      <Dialog open={open} onClose={() => setOpen(false)}>
        <DialogTitle>{isEditMode ? '編輯學生資料' : '新增學生'}</DialogTitle>
        <DialogContent sx={{ minWidth: 400 }}>
          <TextField 
            margin="dense" label="學號" fullWidth required
            value={formData.student_id} 
            onChange={e => setFormData({...formData, student_id: e.target.value})}
            error={!!errors.student_id}
            helperText={errors.student_id}
          />
          <TextField 
            margin="dense" label="姓名" fullWidth required
            value={formData.name} 
            onChange={e => setFormData({...formData, name: e.target.value})}
            error={!!errors.name}
            helperText={errors.name}
          />
          <TextField 
            margin="dense" label="Email" fullWidth 
            value={formData.email} 
            onChange={e => setFormData({...formData, email: e.target.value})} 
            placeholder="example@school.edu.tw"
          />
          <TextField 
            margin="dense" label="卡號 (UID)" fullWidth 
            value={formData.card_uid} 
            onChange={e => setFormData({...formData, card_uid: e.target.value})} 
            helperText="若無卡片可留空"
          />
          
          <FormControl fullWidth margin="dense">
            <InputLabel id="device-multiple-checkbox-label">可通行設備權限</InputLabel>
            <Select
              labelId="device-multiple-checkbox-label"
              multiple
              value={formData.accessible_device_ids}
              onChange={handleDeviceChange}
              input={<OutlinedInput label="可通行設備權限" />}
              renderValue={(selected) => (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {selected.map((value) => {
                    const device = allDevices.find(d => d.id === value);
                    return <Chip key={value} label={device ? device.device_name : value} size="small" />;
                  })}
                </Box>
              )}
            >
              {allDevices.map((device) => (
                <MenuItem key={device.id} value={device.id}>
                  <Checkbox checked={formData.accessible_device_ids.indexOf(device.id) > -1} />
                  <ListItemText primary={device.device_name} secondary={device.location} />
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          {isEditMode && (
            <FormControlLabel 
              control={
                <Switch 
                  checked={formData.is_active} 
                  onChange={e => setFormData({...formData, is_active: e.target.checked})} 
                />
              } 
              label="啟用帳號" 
              sx={{ mt: 2 }} 
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpen(false)}>取消</Button>
          <Button variant="contained" onClick={handleSubmit}>
            {isEditMode ? '更新' : '建立'}
          </Button>
        </DialogActions>
      </Dialog>
      
      <Snackbar open={msg.open} autoHideDuration={3000} onClose={() => setMsg({...msg, open: false})}>
        <Alert severity={msg.type}>{msg.txt}</Alert>
      </Snackbar>
    </Box>
  );
};

export default UserManagement;