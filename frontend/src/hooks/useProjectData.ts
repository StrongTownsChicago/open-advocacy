import { useState, useEffect } from 'react';
import { Project, Entity, EntityStatusRecord } from '../types';
import { projectService } from '../services/projects';
import { statusService } from '../services/status';
import { entityService } from '../services/entities';
import { jurisdictionService } from '../services/jurisdictions';
import { transformEntityFromApi } from '../utils/dataTransformers';

interface UseProjectDataReturn {
  project: Project | null;
  entities: Entity[];
  statusRecords: EntityStatusRecord[];
  geojsonByDistrict: { [districtId: string]: GeoJSON.GeoJsonObject };
  loading: boolean;
  loadingEntities: boolean;
  error: string | null;
  refreshStatusRecords: () => Promise<void>;
}

export const useProjectData = (id: string | undefined): UseProjectDataReturn => {
  const [project, setProject] = useState<Project | null>(null);
  const [entities, setEntities] = useState<Entity[]>([]);
  const [loadingEntities, setLoadingEntities] = useState(false);
  const [statusRecords, setStatusRecords] = useState<EntityStatusRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [geojsonByDistrict, setGeojsonByDistrict] = useState<{
    [districtId: string]: GeoJSON.GeoJsonObject;
  }>({});

  useEffect(() => {
    const fetchData = async () => {
      if (!id) return;

      setLoading(true);
      setError(null);

      try {
        // Fetch project
        const projectResponse = await projectService.getProject(id);
        setProject(projectResponse.data);

        // Fetch status records for this project
        const statusResponse = await statusService.getStatusRecords(id);
        setStatusRecords(statusResponse.data);
      } catch (err) {
        console.error('Error fetching project data:', err);
        setError('Failed to load project details');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [id]);

  useEffect(() => {
    const fetchEntities = async () => {
      if (!project || !project.jurisdiction_id) return;

      setLoadingEntities(true);
      try {
        const response = await entityService.getEntitiesByJurisdictions(project.jurisdiction_id);
        const transformedEntities = response.data.map(transformEntityFromApi);
        setEntities(transformedEntities);
      } catch (err) {
        console.error('Failed to fetch entities:', err);
      } finally {
        setLoadingEntities(false);
      }
    };

    fetchEntities();
  }, [project]);

  useEffect(() => {
    const fetchGeoJSON = async () => {
      if (!project?.jurisdiction_id) return;
      try {
        const data = await jurisdictionService.getDistrictGeoJSON(project.jurisdiction_id);
        setGeojsonByDistrict(data);
      } catch (err) {
        console.error('Failed to fetch district geojson:', err);
      }
    };
    fetchGeoJSON();
  }, [project]);

  const refreshStatusRecords = async () => {
    if (!id) return;

    try {
      // Fetch raw status records
      const statusResponse = await statusService.getStatusRecords(id);
      setStatusRecords(statusResponse.data);

      // Also refresh the project to get updated status distribution
      const projectResponse = await projectService.getProject(id);
      setProject(projectResponse.data);
    } catch (err) {
      console.error('Error refreshing project data:', err);
    }
  };

  return {
    project,
    entities,
    statusRecords,
    geojsonByDistrict,
    loading,
    loadingEntities,
    error,
    refreshStatusRecords,
  };
};
