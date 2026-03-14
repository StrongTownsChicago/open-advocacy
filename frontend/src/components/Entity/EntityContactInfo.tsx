import React from 'react';
import { Box, Link, Typography } from '@mui/material';
import EmailIcon from '@mui/icons-material/Email';
import PhoneIcon from '@mui/icons-material/Phone';
import PublicIcon from '@mui/icons-material/Public';
import LocationOnIcon from '@mui/icons-material/LocationOn';
import { Entity } from '../../types';

interface EntityContactInfoProps {
  entity: Entity;
}

const EntityContactInfo: React.FC<EntityContactInfoProps> = ({ entity }) => {
  if (!entity.email && !entity.phone && !entity.website && !entity.address) {
    return null;
  }

  return (
    <Box display="flex" flexDirection="column" gap={1}>
      {entity.email && (
        <Box display="flex" alignItems="center" gap={1}>
          <EmailIcon fontSize="small" color="action" />
          <Link href={`mailto:${entity.email}`}>{entity.email}</Link>
        </Box>
      )}

      {entity.phone && (
        <Box display="flex" alignItems="center" gap={1}>
          <PhoneIcon fontSize="small" color="action" />
          <Link href={`tel:${entity.phone}`}>{entity.phone}</Link>
        </Box>
      )}

      {entity.website && (
        <Box display="flex" alignItems="center" gap={1}>
          <PublicIcon fontSize="small" color="action" />
          <Link href={entity.website} target="_blank" rel="noopener">
            Website
          </Link>
        </Box>
      )}

      {entity.address && (
        <Box display="flex" alignItems="flex-start" gap={1}>
          <LocationOnIcon fontSize="small" color="action" sx={{ mt: 0.3 }} />
          <Typography variant="body2">{entity.address}</Typography>
        </Box>
      )}
    </Box>
  );
};

export default EntityContactInfo;
