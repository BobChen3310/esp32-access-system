import React from 'react';
import { Box, Typography, Button, Container } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ErrorOutlineIcon from '@mui/icons-material/ErrorOutline';

const NotFound = () => {
  const navigate = useNavigate();

  return (
    <Container maxWidth="md">
      <Box
        sx={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '60vh',
          textAlign: 'center',
        }}
      >
        <ErrorOutlineIcon sx={{ fontSize: 100, color: 'text.secondary', mb: 2 }} />
        
        <Typography variant="h2" component="h1" gutterBottom fontWeight="bold">
          404
        </Typography>
        
        <Typography variant="h5" component="h2" color="text.secondary" gutterBottom>
          找不到頁面
        </Typography>
        
        <Typography variant="body1" color="text.secondary" paragraph sx={{ mb: 4 }}>
          您嘗試訪問的網址可能已更名、移除或暫時無法使用。
        </Typography>

        <Button 
          variant="contained" 
          size="large" 
          onClick={() => navigate('/')}
        >
          回到儀表板
        </Button>
      </Box>
    </Container>
  );
};

export default NotFound;
