import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { ThemeProvider } from './theme/ThemeProvider';
import { AuthProvider } from './contexts/AuthContext';
import { UserRepresentativesProvider } from './contexts/UserRepresentativesContext';
import Header from './components/common/Header';

import HomePage from './pages/HomePage';
import ProjectDetail from './pages/ProjectDetail';
import ProjectFormPage from './pages/ProjectFormPage';
import ProjectList from './pages/ProjectList';
import RepresentativeLookup from './pages/RepresentativeLookup';
import EntityDetail from './pages/EntityDetail';
import LoginPage from './pages/LoginPage';
import UnauthorizedPage from './pages/UnauthorizedPage';
import ProjectDashboard from './pages/ProjectDashboard';
import Scorecard from './pages/Scorecard/index';
import ScorecardIndex from './pages/ScorecardIndex';

// Admin Pages
import UserManagement from './pages/admin/UserManagementPage';
import RegisterPage from './pages/admin/RegisterPage';
import AdminDashboard from './pages/admin/AdminDashboard';
import DataImportPage from './pages/admin/DataImportPage';

import ProtectedRoute from './components/auth/ProtectedRoute';

const DASHBOARD_PATH_PREFIXES = ['/dashboard/', '/scorecard/'];

const ConditionalHeader: React.FC = () => {
  const location = useLocation();
  const isDashboard = DASHBOARD_PATH_PREFIXES.some(prefix =>
    location.pathname.startsWith(prefix)
  );
  return isDashboard ? null : <Header />;
};

const App: React.FC = () => {
  return (
    <Router>
      <ThemeProvider>
        <AuthProvider>
          <UserRepresentativesProvider>
            <ConditionalHeader />
            <main>
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/projects" element={<ProjectList />} />
                <Route path="/projects/create" element={<ProjectFormPage />} />
                <Route path="/projects/:id/edit" element={<ProjectFormPage />} />
                <Route path="/projects/:id" element={<ProjectDetail />} />
                <Route path="/representatives" element={<RepresentativeLookup />} />
                <Route path="/representatives/:id" element={<EntityDetail />} />
                <Route path="/dashboard/:slug" element={<ProjectDashboard />} />
                <Route path="/scorecard" element={<ScorecardIndex />} />
                <Route path="/scorecard/abundant-housing-illinois" element={<Navigate to="/scorecard/abundant-housing-illinois-chicago-city-council" replace />} />
                <Route path="/scorecard/:groupSlug" element={<Scorecard />} />
                <Route
                  path="/adu-opt-in-dashboard"
                  element={<Navigate to="/dashboard/adu-opt-in-dashboard" replace />}
                />
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
                      <AdminDashboard />
                    </ProtectedRoute>
                  }
                />

                <Route
                  path="/admin/users"
                  element={
                    <ProtectedRoute requiredRoles={['super_admin', 'group_admin']}>
                      <UserManagement />
                    </ProtectedRoute>
                  }
                />

                <Route
                  path="/admin/imports"
                  element={
                    <ProtectedRoute requiredRoles={['super_admin']}>
                      <DataImportPage />
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
