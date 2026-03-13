import React from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { Entity, EntityStatus, EntityStatusRecord, DashboardConfig } from '../../types';
import { getStatusColor, getStatusLabel as getStatusLabelDefault } from '@/utils/statusColors';
import { formatMetricValue } from '@/utils/dataTransformers';

interface EntityDistrictMapProps {
  entities: Entity[];
  statusRecords: EntityStatusRecord[];
  geojsonByDistrict: { [districtName: string]: GeoJSON.GeoJsonObject };
  getStatusLabel?: (status: string) => string;
  centerPoint?: [number, number];
  dashboardConfig?: DashboardConfig;
}

const EntityDistrictMap: React.FC<EntityDistrictMapProps> = ({
  entities,
  statusRecords,
  geojsonByDistrict,
  getStatusLabel = getStatusLabelDefault,
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

  const tooltipMetrics = dashboardConfig?.metrics?.filter(m => m.show_in_tooltip !== false) ?? [];

  const entityByDistrict: Record<string, Entity | undefined> = {};
  entities.forEach(entity => {
    if (entity.district_name) {
      entityByDistrict[entity.district_name] = entity;
    }
  });

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  function onEachFeature(feature: GeoJSON.Feature, layer: any) {
    const wardNumber = feature.properties?.ward;
    const districtName = wardNumber ? `Ward ${wardNumber}` : undefined;
    const entity = districtName ? entityByDistrict[districtName] : undefined;
    const status = entity ? statusMap[entity.id] : EntityStatus.NEUTRAL;

    let tooltipContent = `<strong>${districtName || 'Unknown Ward'}</strong>`;
    if (entity) {
      tooltipContent += `<br/>${entity.name} (${entity.title || ''})<br/>Status: ${getStatusLabel(status)}`;
      const record = recordMap[entity.id];
      for (const metric of tooltipMetrics) {
        const value = record?.record_metadata?.[metric.key];
        tooltipContent += `<br/>${metric.label}: ${formatMetricValue(value, metric.format ?? 'text')}`;
      }
    }
    layer.bindTooltip(tooltipContent, { sticky: true });
  }

  return (
    <MapContainer center={centerPoint} zoom={11} style={{ height: 600, width: '100%' }}>
      <TileLayer
        attribution="&copy; OpenStreetMap contributors"
        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      {Object.entries(geojsonByDistrict).map(([districtName, geojson]) => {
        const wardNumber = districtName.match(/\d+/)?.[0];
        const lookupName = wardNumber ? `Ward ${wardNumber}` : districtName;
        return (
          <GeoJSON
            key={districtName}
            data={geojson}
            style={() => ({
              color: '#333',
              weight: 1,
              fillColor: getStatusColor(
                entityByDistrict[lookupName]
                  ? statusMap[entityByDistrict[lookupName]!.id]
                  : EntityStatus.NEUTRAL
              ),
              fillOpacity: 0.7,
            })}
            onEachFeature={onEachFeature}
          />
        );
      })}
    </MapContainer>
  );
};

export default EntityDistrictMap;
