import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Chip,
  Link as MuiLink,
  Typography,
} from '@mui/material';
import { ScorecardEntityRow, ScorecardResponse } from '../../types';
import { getStatusColor } from '../../utils/statusColors';

interface MobileCardListProps {
  rows: ScorecardEntityRow[];
  data: ScorecardResponse;
}

const MobileCardList: React.FC<MobileCardListProps> = ({ rows, data }) => (
  <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
    {rows.map(row => (
      <Card key={row.entity.id} variant="outlined">
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
            <MuiLink
              component={RouterLink}
              to={`/representatives/${row.entity.id}`}
              fontWeight={700}
              fontSize="1rem"
              underline="hover"
            >
              {row.entity.name}
            </MuiLink>
            <Typography variant="body2" color="text.secondary">
              {row.entity.district_name ?? ''}
            </Typography>
          </Box>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1 }}>
            Alignment: {row.aligned_count} / {row.total_scoreable}
          </Typography>
          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5 }}>
            {data.projects.map(project => {
              const statusEntry = row.statuses[project.id];
              if (!statusEntry) return null;
              return (
                <Box
                  key={project.id}
                  sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}
                >
                  <MuiLink
                    component={RouterLink}
                    to={`/projects/${project.id}`}
                    variant="caption"
                    underline="hover"
                    sx={{ flex: 1, mr: 1 }}
                  >
                    {project.title}
                  </MuiLink>
                  <Chip
                    label={statusEntry.label}
                    size="small"
                    sx={{
                      backgroundColor: getStatusColor(statusEntry.status),
                      color: '#fff',
                      fontWeight: 600,
                      fontSize: '0.65rem',
                    }}
                  />
                </Box>
              );
            })}
          </Box>
        </CardContent>
      </Card>
    ))}
  </Box>
);

export default MobileCardList;
