import React, { useState, useEffect } from 'react';
import {
  Paper,
  Box,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  CircularProgress,
  Alert,
  Select,
  MenuItem,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  SelectChangeEvent,
} from '@mui/material';
import { useAuth } from '../../contexts/AuthContext';
import { userService } from '../../services/user';
import { UserProfile } from '../../types';
import AdminLayout from '../../components/common/AdminLayout';

const UserManagement: React.FC = () => {
  const { user } = useAuth();
  const [users, setUsers] = useState<UserProfile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Password change dialog state
  const [passwordDialogOpen, setPasswordDialogOpen] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [selectedUserName, setSelectedUserName] = useState<string>('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordError, setPasswordError] = useState<string | null>(null);

  // Fetch users in the current admin's group
  useEffect(() => {
    if (user?.group_id) {
      fetchUsers(user.group_id);
    }
  }, [user]);

  const fetchUsers = async (groupId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await userService.getUsersInGroup(groupId);
      setUsers(data);
    } catch (err: unknown) {
      console.error('Error fetching users:', err);
      setError('Failed to load users. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleRoleChange = async (userId: string, newRole: string) => {
    setError(null);
    setSuccess(null);
    try {
      await userService.updateUserRole({ user_id: userId, new_role: newRole });

      // Update local state
      setUsers(prevUsers => prevUsers.map(u => (u.id === userId ? { ...u, role: newRole } : u)));

      setSuccess('User role updated successfully');
    } catch (err: unknown) {
      console.error('Error updating role:', err);
      setError('Failed to update user role');
    }
  };

  const openPasswordDialog = (userId: string, userName: string) => {
    setSelectedUserId(userId);
    setSelectedUserName(userName);
    setNewPassword('');
    setConfirmPassword('');
    setPasswordError(null);
    setPasswordDialogOpen(true);
  };

  const closePasswordDialog = () => {
    setPasswordDialogOpen(false);
    setSelectedUserId(null);
  };

  const validatePasswords = (): boolean => {
    if (newPassword.length < 8) {
      setPasswordError('Password must be at least 8 characters');
      return false;
    }

    if (newPassword !== confirmPassword) {
      setPasswordError('Passwords do not match');
      return false;
    }

    return true;
  };

  const handlePasswordChange = async () => {
    if (!validatePasswords() || !selectedUserId) return;

    setPasswordError(null);
    try {
      await userService.updateUserPassword({
        user_id: selectedUserId,
        new_password: newPassword,
      });

      closePasswordDialog();
      setSuccess('Password updated successfully');
    } catch (err: unknown) {
      console.error('Error updating password:', err);
      setPasswordError('Failed to update password');
    }
  };

  // Helper to check if current user can modify this user
  const canModifyUser = (targetUser: UserProfile): boolean => {
    if (!user) return false;

    // Super admins can modify anyone except other super admins
    if (user.role === 'super_admin') {
      return targetUser.role !== 'super_admin' || targetUser.id === user.id;
    }

    // Group admins can only modify non-admin users in their group
    if (user.role === 'group_admin') {
      return (
        targetUser.group_id === user.group_id &&
        targetUser.role !== 'super_admin' &&
        targetUser.id !== user.id // Can't modify self
      );
    }

    return false;
  };

  if (loading) {
    return (
      <AdminLayout title="User Management">
        <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
          <CircularProgress />
        </Box>
      </AdminLayout>
    );
  }

  return (
    <AdminLayout title="User Management">
      <Box sx={{ mt: 4, mb: 4 }}>
        {error && (
          <Alert severity="error" sx={{ mt: 2, mb: 2 }}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mt: 2, mb: 2 }}>
            {success}
          </Alert>
        )}

        <Paper elevation={3} sx={{ mt: 3, p: 3 }}>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Role</TableCell>
                  <TableCell>Last Login</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.map(userItem => (
                  <TableRow key={userItem.id}>
                    <TableCell>{userItem.name}</TableCell>
                    <TableCell>{userItem.email}</TableCell>
                    <TableCell>
                      {canModifyUser(userItem) ? (
                        <FormControl size="small" fullWidth>
                          <Select
                            value={userItem.role}
                            onChange={(e: SelectChangeEvent) =>
                              handleRoleChange(userItem.id, e.target.value)
                            }
                          >
                            <MenuItem value="editor">Editor</MenuItem>
                            <MenuItem value="group_admin">Group Admin</MenuItem>
                            {/* Only super_admin can assign super_admin role */}
                            {user?.role === 'super_admin' && (
                              <MenuItem value="super_admin">Super Admin</MenuItem>
                            )}
                          </Select>
                        </FormControl>
                      ) : (
                        userItem.role
                      )}
                    </TableCell>
                    <TableCell>
                      {userItem.last_login
                        ? new Date(userItem.last_login).toLocaleString()
                        : 'Never'}
                    </TableCell>
                    <TableCell>
                      {canModifyUser(userItem) && (
                        <Button
                          variant="outlined"
                          size="small"
                          onClick={() => openPasswordDialog(userItem.id, userItem.name)}
                        >
                          Change Password
                        </Button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      </Box>

      {/* Password Change Dialog */}
      <Dialog open={passwordDialogOpen} onClose={closePasswordDialog}>
        <DialogTitle>Change Password for {selectedUserName}</DialogTitle>
        <DialogContent>
          {passwordError && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {passwordError}
            </Alert>
          )}
          <TextField
            margin="dense"
            label="New Password"
            type="password"
            fullWidth
            value={newPassword}
            onChange={e => setNewPassword(e.target.value)}
          />
          <TextField
            margin="dense"
            label="Confirm Password"
            type="password"
            fullWidth
            value={confirmPassword}
            onChange={e => setConfirmPassword(e.target.value)}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={closePasswordDialog}>Cancel</Button>
          <Button onClick={handlePasswordChange} color="primary">
            Update Password
          </Button>
        </DialogActions>
      </Dialog>
    </AdminLayout>
  );
};

export default UserManagement;
