import React from 'react';
import {
  Avatar,
  Box,
  Card,
  CardActions,
  CardContent,
  Button,
  Chip,
  Divider,
  Link,
  Typography,
} from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';
import { useNavigate } from 'react-router-dom';
import { useTheme } from '@mui/material/styles';
import { Entity } from '../../types';
import EntityContactInfo from './EntityContactInfo';

interface RepresentativeCardProps {
  rep: Entity;
}

const RepresentativeCard: React.FC<RepresentativeCardProps> = ({ rep }) => {
  const theme = useTheme();
  const navigate = useNavigate();

  return (
    <Card
      elevation={3}
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        transition: 'transform 0.2s, box-shadow 0.2s',
        '&:hover': {
          transform: 'translateY(-4px)',
          boxShadow: 6,
        },
      }}
    >
      <CardContent sx={{ flexGrow: 1 }}>
        <Box display="flex" justifyContent="space-between" alignItems="flex-start" mb={2}>
          <Box display="flex" alignItems="center">
            <Avatar
              src={rep.image_url}
              sx={{
                mr: 2,
                bgcolor: theme.palette.primary.main,
                width: 48,
                height: 48,
              }}
            >
              <PersonIcon />
            </Avatar>
            <Box>
              <Link
                component="button"
                variant="h6"
                onClick={() => navigate(`/representatives/${rep.id}`)}
                sx={{
                  fontWeight: 'bold',
                  fontSize: '1.25rem',
                  fontFamily: theme.typography.h6.fontFamily,
                  textAlign: 'left',
                  textTransform: 'none',
                  color: 'text.primary',
                  textDecoration: 'none',
                  '&:hover': {
                    textDecoration: 'underline',
                    color: theme.palette.primary.main,
                  },
                }}
              >
                {rep.name}
              </Link>
              <Typography variant="subtitle2" color="textSecondary">
                {rep.title}
              </Typography>
              {rep.district_name && (
                <Chip
                  size="small"
                  label={rep.district_name}
                  color="primary"
                  variant="outlined"
                  sx={{ mt: 0.5 }}
                />
              )}
            </Box>
          </Box>
        </Box>

        <Divider sx={{ mb: 2 }} />

        <EntityContactInfo entity={rep} />
      </CardContent>
      <CardActions sx={{ justifyContent: 'flex-end', p: 2, pt: 0 }}>
        <Button
          size="small"
          variant="outlined"
          color="primary"
          onClick={() => navigate(`/representatives/${rep.id}`)}
        >
          View Representative Details
        </Button>
      </CardActions>
    </Card>
  );
};

export default RepresentativeCard;
