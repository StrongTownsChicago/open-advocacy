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
import SyncIcon from '@mui/icons-material/Sync';
import AdminLayout from '../../components/common/AdminLayout';
import { importsService, ImportLocation, ImportResult } from '../../services/imports';
import { scorecardService, ScorecardRefreshResult } from '../../services/scorecard';

const DataImportPage: React.FC = () => {
  const [locations, setLocations] = useState<ImportLocation[]>([]);
  const [loading, setLoading] = useState(true);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [importingKeys, setImportingKeys] = useState<Set<string>>(new Set());
  const [results, setResults] = useState<Record<string, ImportResult | string>>({});
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [refreshResult, setRefreshResult] = useState<ScorecardRefreshResult | null>(null);
  const [refreshError, setRefreshError] = useState<string | null>(null);

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

  const handleScorecardRefresh = async () => {
    setIsRefreshing(true);
    setRefreshResult(null);
    setRefreshError(null);
    try {
      const response = await scorecardService.refreshScorecardData();
      setRefreshResult(response.data);
    } catch {
      setRefreshError('Scorecard refresh failed. Check that the eLMS and OpenStates APIs are reachable.');
    } finally {
      setIsRefreshing(false);
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

      <Typography variant="h6" sx={{ mt: 4, mb: 1 }}>
        Scorecard Vote Data
      </Typography>
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Fetch the latest vote and sponsorship data from the Chicago City Clerk eLMS API and the
        Illinois OpenStates API, and update all scorecard records.
      </Typography>

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, sm: 6, md: 4 }}>
          <Card>
            <CardContent>
              <SyncIcon color="primary" sx={{ fontSize: 36, mb: 1 }} />
              <Typography variant="h6" gutterBottom>
                Scorecard Refresh
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Updates vote and co-sponsorship status records for all scorecard projects using live
                data from the eLMS API (Chicago) and OpenStates API (Illinois).
              </Typography>

              {refreshResult && (
                <Alert severity="success" sx={{ mb: 2 }}>
                  Refresh complete: {refreshResult.updated} records updated
                  {refreshResult.errors > 0 && `, ${refreshResult.errors} errors`}
                </Alert>
              )}

              {refreshError && (
                <Alert severity="error" sx={{ mb: 2 }}>
                  {refreshError}
                </Alert>
              )}

              <Button
                variant="contained"
                onClick={handleScorecardRefresh}
                disabled={isRefreshing}
                startIcon={isRefreshing ? <CircularProgress size={18} /> : undefined}
                fullWidth
              >
                {isRefreshing ? 'Refreshing...' : 'Refresh Scorecard Data'}
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </AdminLayout>
  );
};

export default DataImportPage;
