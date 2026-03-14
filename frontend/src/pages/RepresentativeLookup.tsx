import React from 'react';
import {
  Container,
  Typography,
  TextField,
  Button,
  Grid,
  Box,
  CircularProgress,
  Alert,
  Paper,
  Chip,
  Snackbar,
  useTheme,
  Fade,
  IconButton,
  Tooltip,
} from '@mui/material';
import MuiAlert from '@mui/material/Alert';
import SearchIcon from '@mui/icons-material/Search';
import InfoIcon from '@mui/icons-material/Info';
import Dialog from '@mui/material/Dialog';
import DialogTitle from '@mui/material/DialogTitle';
import DialogActions from '@mui/material/DialogActions';
import { Entity } from '../types';
import { useNavigate } from 'react-router-dom';
import { useRepresentativeLookup } from '../hooks/useRepresentativeLookup';
import RepresentativeCard from '../components/Entity/RepresentativeCard';

const RepresentativeLookup: React.FC = () => {
  const theme = useTheme();
  const navigate = useNavigate();

  const {
    address,
    representatives,
    districts,
    searched,
    loading,
    error,
    showToast,
    toastMessage,
    showBackModal,
    handleAddressChange,
    handleSubmit,
    clearSearch,
    handleCloseToast,
    setShowBackModal,
  } = useRepresentativeLookup();

  const renderRepresentativeCards = (reps: Entity[]) => {
    if (reps.length === 0) {
      return (
        <Box sx={{ textAlign: 'center', py: 4 }}>
          <Typography variant="body1">No representatives found.</Typography>
        </Box>
      );
    }

    return (
      <Grid container spacing={3}>
        {reps.map(rep => (
          <Grid size={{ xs: 12, md: 6 }} key={rep.id}>
            <RepresentativeCard rep={rep} />
          </Grid>
        ))}
      </Grid>
    );
  };

  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <Paper
        elevation={2}
        sx={{
          p: 3,
          mb: 4,
          borderRadius: 2,
          backgroundColor: theme.palette.background.paper,
        }}
      >
        <Typography variant="h4" component="h1" gutterBottom fontWeight="bold" color="primary">
          Find Your Representatives
        </Typography>

        <Typography variant="body1" paragraph color="textSecondary">
          Enter your address to find representatives who serve your area. The list of your
          representatives will be stored in your browser for easy access to representative
          positions.
        </Typography>

        <form onSubmit={handleSubmit} style={{ width: '100%' }}>
          <Grid container spacing={2} alignItems="stretch" sx={{ width: '100%' }}>
            <Grid size={{ xs: 12, md: 8 }} sx={{ width: '100%' }}>
              <TextField
                fullWidth
                label="Street Address"
                variant="outlined"
                value={address}
                onChange={handleAddressChange}
                placeholder="123 Main St, City, IL 60601"
                required
                disabled={loading}
                sx={{
                  width: '100%',
                  '& .MuiOutlinedInput-root': {
                    borderRadius: 2,
                    height: '100%',
                  },
                }}
              />
            </Grid>
            <Grid size={{ xs: 12, md: 4 }}>
              <Button
                type="submit"
                variant="contained"
                color="primary"
                fullWidth
                sx={{
                  height: '100%',
                  borderRadius: 2,
                  py: 1.5,
                }}
                disabled={loading}
                startIcon={
                  loading ? <CircularProgress size={20} color="inherit" /> : <SearchIcon />
                }
              >
                {loading ? 'Searching...' : 'Find Representatives'}
              </Button>
            </Grid>
          </Grid>
        </form>
      </Paper>

      {error && (
        <Alert severity="error" sx={{ mb: 4 }}>
          {error}
        </Alert>
      )}

      {searched && !loading && (
        <Fade in={searched}>
          <Box>
            <Box
              sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}
            >
              <Typography variant="h5" component="h2">
                Your Representatives
              </Typography>
              <Box>
                <Tooltip title="Representatives for your area">
                  <IconButton size="small" color="primary" sx={{ mr: 1 }}>
                    <InfoIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Button variant="text" color="primary" onClick={clearSearch} size="small">
                  Clear Results
                </Button>
              </Box>
            </Box>

            {representatives.length > 0 && districts.length > 0 && (
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle1" gutterBottom>
                  Districts:
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {districts.map((district, index) => (
                    <Chip
                      key={index}
                      label={district}
                      color="secondary"
                      variant="outlined"
                      size="small"
                    />
                  ))}
                </Box>
              </Box>
            )}

            {renderRepresentativeCards(representatives)}
          </Box>
        </Fade>
      )}

      <Snackbar
        open={showToast}
        autoHideDuration={6000}
        onClose={handleCloseToast}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <MuiAlert elevation={6} variant="filled" onClose={handleCloseToast} severity="success">
          {toastMessage}
        </MuiAlert>
      </Snackbar>

      <Dialog open={showBackModal} onClose={() => setShowBackModal(false)}>
        <DialogTitle>Done viewing your representatives?</DialogTitle>
        <DialogActions>
          <Button
            onClick={() => {
              setShowBackModal(false);
              navigate(-1);
            }}
            color="primary"
          >
            Go Back
          </Button>
          <Button onClick={() => setShowBackModal(false)} color="secondary">
            Stay
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default RepresentativeLookup;
