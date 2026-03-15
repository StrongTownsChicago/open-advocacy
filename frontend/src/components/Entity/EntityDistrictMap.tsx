import React from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { Entity, EntityStatus, EntityStatusRecord, DashboardConfig } from '../../types';
import { getStatusColor, makeStatusLabelFn } from '@/utils/statusColors';
import { formatMetricValue } from '@/utils/dataTransformers';

interface EntityDistrictMapProps {
  entities: Entity[];
  statusRecords: EntityStatusRecord[];
  geojsonByDistrict: { [districtName: string]: GeoJSON.GeoJsonObject };
  centerPoint?: [number, number];
  dashboardConfig?: DashboardConfig;
}

const EntityDistrictMap: React.FC<EntityDistrictMapProps> = ({
  entities,
  statusRecords,
  geojsonByDistrict,
  centerPoint = [41.8781, -87.6298],
  dashboardConfig,
}) => {
  const statusMap = statusRecords.reduce(
    (acc, record) => {
      acc[record.entity_id] = record.status;
      return acc;
    },
    {} as Record<string, EntityStatus>
  );

  const recordMap = statusRecords.reduce(
    (acc, record) => {
      acc[record.entity_id] = record;
      return acc;
    },
    {} as Record<string, EntityStatusRecord>
  );

  const getStatusLabel = makeStatusLabelFn(dashboardConfig?.status_labels);
  const tooltipMetrics = dashboardConfig?.metrics?.filter(m => m.show_in_tooltip !== false) ?? [];

  const entityByDistrict: Record<string, Entity | undefined> = {};
  entities.forEach(entity => {
    if (entity.district_name) {
      entityByDistrict[entity.district_name] = entity;
    }
  });

  return (
    <MapContainer center={centerPoint} zoom={11} style={{ height: 600, width: '100%' }}>
      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {Object.entries(geojsonByDistrict).map(([districtName, geojson]) => {
        const entity = entityByDistrict[districtName];
        const status = entity ? statusMap[entity.id] : EntityStatus.NEUTRAL;
        return (
          <GeoJSON
            key={districtName}
            data={geojson}
            style={() => ({
              color: '#333',
              weight: 1,
              fillColor: getStatusColor(status),
              fillOpacity: 0.7,
            })}
            // eslint-disable-next-line @typescript-eslint/no-explicit-any
            onEachFeature={(_feature: GeoJSON.Feature, layer: any) => {
              let tooltipContent = `<strong>${districtName}</strong>`;
              if (entity) {
                tooltipContent += `<br/>${entity.name} (${entity.title || ''})<br/>Status: ${getStatusLabel(status)}`;
                const record = recordMap[entity.id];
                for (const metric of tooltipMetrics) {
                  const value = record?.record_metadata?.[metric.key];
                  tooltipContent += `<br/>${metric.label}: ${formatMetricValue(value, metric.format ?? 'text')}`;
                }
              }
              layer.bindTooltip(tooltipContent, { sticky: true });
            }}
          />
        );
      })}
    </MapContainer>
  );
};

export default EntityDistrictMap;
