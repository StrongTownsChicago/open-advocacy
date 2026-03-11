import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  CircularProgress,
  Alert,
} from '@mui/material';
import CloudDownloadIcon from '@mui/icons-material/CloudDownload';
import AdminLayout from '../../components/common/AdminLayout';
import { importsService, ImportLocation, ImportResult } from '../../services/imports';

const DataImportPage: React.FC = () => {
  const [locations, setLocations] = useState<ImportLocation[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [importingKeys, setImportingKeys] = useState<Set<string>>(new Set());
  const [results, setResults] = useState<Record<string, ImportResult | string>>({});

  useEffect(() => {
    const fetchLocations = async () => {
      try {
        const response = await importsService.getLocations();
        setLocations(response.data);
      } catch {
        setFetchError('Failed to load available import locations');
      } finally {
        setLoading(false);
      }
    };
    fetchLocations();
  }, []);

  const handleImport = async (locationKey: string) => {
    setImportingKeys(prev => new Set(prev).add(locationKey));
    setResults(prev => {
      const updated = { ...prev };
      delete updated[locationKey];
      return updated;
    });

    try {
      const response = await importsService.triggerImport(locationKey);
      setResults(prev => ({ ...prev, [locationKey]: response.data }));
    } catch {
      setResults(prev => ({
        ...prev,
        [locationKey]: `Import failed for ${locationKey}`,
      }));
    } finally {
      setImportingKeys(prev => {
        const updated = new Set(prev);
        updated.delete(locationKey);
        return updated;
      });
    }
  };

  if (loading) {
    return (
      <AdminLayout title="Data Imports">
        <CircularProgress />
      </AdminLayout>
    );
  }

  if (fetchError) {
    return (
      <AdminLayout title="Data Imports">
        <Alert severity="error">{fetchError}</Alert>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout title="Data Imports">
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Import representative and geographic data from external sources.
      </Typography>

      <Grid container spacing={3}>
        {locations.map(location => {
          const isImporting = importingKeys.has(location.key);
          const result = results[location.key];
          const isError = typeof result === 'string';

          return (
            <Grid size={{ xs: 12, sm: 6, md: 4 }} key={location.key}>
              <Card>
                <CardContent>
                  <CloudDownloadIcon color="primary" sx={{ fontSize: 36, mb: 1 }} />
                  <Typography variant="h6" gutterBottom>
                    {location.name}
                  </Typography>
                  {location.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {location.description}
                    </Typography>
                  )}

                  {result && !isError && typeof result === 'object' && (
                    <Alert severity="success" sx={{ mb: 2 }}>
                      Import complete: {result.steps_completed} steps succeeded
                      {result.steps_failed > 0 && `, ${result.steps_failed} failed`}
                    </Alert>
                  )}

                  {isError && (
                    <Alert severity="error" sx={{ mb: 2 }}>
                      {result}
                    </Alert>
                  )}

                  <Button
                    variant="contained"
                    onClick={() => handleImport(location.key)}
                    disabled={isImporting}
                    startIcon={isImporting ? <CircularProgress size={18} /> : undefined}
                    fullWidth
                  >
                    {isImporting ? 'Importing...' : 'Import'}
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      {locations.length === 0 && (
        <Typography color="text.secondary">No import locations available.</Typography>
      )}
    </AdminLayout>
  );
};

export default DataImportPage;
