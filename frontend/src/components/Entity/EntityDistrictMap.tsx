import React from 'react';
import { MapContainer, TileLayer, GeoJSON } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { Entity, EntityStatus, EntityStatusRecord, DashboardConfig } from '../../types';
import { makeStatusColorFn, makeStatusLabelFn } from '@/utils/statusColors';
import { buildDistrictTooltip } from './districtTooltip';

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
  const getStatusColor = makeStatusColorFn(dashboardConfig?.status_colors);
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
              layer.bindTooltip(
                buildDistrictTooltip({
                  districtName,
                  entity,
                  record: entity ? recordMap[entity.id] : undefined,
                  statusLabel: getStatusLabel(status),
                  statusColor: getStatusColor(status),
                  metrics: tooltipMetrics,
                }),
                { sticky: true, className: 'district-tooltip', direction: 'top', offset: [0, -8] }
              );
            }}
          />
        );
      })}
    </MapContainer>
  );
};

export default EntityDistrictMap;
