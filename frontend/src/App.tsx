import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from './theme/ThemeProvider';
import { AuthProvider } from './contexts/AuthContext';
import { UserRepresentativesProvider } from './contexts/UserRepresentativesContext';


import HomePage from './pages/HomePage';
import ProjectDetail from './pages/ProjectDetail';
import ProjectFormPage from './pages/ProjectFormPage';
import ProjectList from './pages/ProjectList';
import RepresentativeLookup from './pages/RepresentativeLookup';
import EntityDetail from './pages/EntityDetail';
import LoginPage from './pages/LoginPage';
import UnauthorizedPage from './pages/UnauthorizedPage';

// Custom Project Pages
import AduOptInDashboard from './pages/CustomProjects/AduOptInDashboard';

// Admin Pages
import UserManagement from './pages/admin/UserManagementPage';
import RegisterPage from './pages/admin/RegisterPage';

import ProtectedRoute from './components/auth/ProtectedRoute';

const App: React.FC = () => {
  return (
    <Router>
      <ThemeProvider>
        <AuthProvider>
          <UserRepresentativesProvider>
            {/* TODO: Conditionally display header depending on state */}
            {/* <Header /> */}
            <main>
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/projects" element={<ProjectList />} />
                <Route path="/projects/create" element={<ProjectFormPage />} />
                <Route path="/projects/:id/edit" element={<ProjectFormPage />} />
                <Route path="/projects/:id" element={<ProjectDetail />} />
                <Route path="/representatives" element={<RepresentativeLookup />} />
                <Route path="/representatives/:id" element={<EntityDetail />} />
                <Route path="/adu-opt-in-dashboard" element={<AduOptInDashboard />} />
                <Route path="/login" element={<LoginPage />} />
                <Route path="/unauthorized" element={<UnauthorizedPage />} />

                <Route
                  path="/projects/create"
                  element={
                    <ProtectedRoute requiredRoles={['super_admin', 'group_admin', 'editor']}>
                      <ProjectFormPage />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="/projects/:id/edit"
                  element={
                    <ProtectedRoute requiredRoles={['super_admin', 'group_admin', 'editor']}>
                      <ProjectFormPage />
                    </ProtectedRoute>
                  }
                />

                <Route
                  path="/register"
                  element={
                    <ProtectedRoute requiredRoles={['super_admin', 'group_admin']}>
                      <RegisterPage />
                    </ProtectedRoute>
                  }
                />

                <Route
                  path="/admin"
                  element={
                    <ProtectedRoute requiredRoles={['super_admin', 'group_admin']}>
                      <UserManagement />
                    </ProtectedRoute>
                  }
                />
              </Routes>
            </main>
          </UserRepresentativesProvider>
        </AuthProvider>
      </ThemeProvider>
    </Router>
  );
};

export default App;
