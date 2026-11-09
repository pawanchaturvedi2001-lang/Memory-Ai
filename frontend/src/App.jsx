import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';

import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import { Projects } from './pages/Projects';
import { ProjectDetails } from './pages/ProjectDetails';
import { DocumentUpload } from './pages/DocumentUpload';
import { KnowledgeExtraction } from './pages/KnowledgeExtraction';
import { KnowledgeGapDetector } from './pages/KnowledgeGapDetector';
import { ApprovalManagement } from './pages/ApprovalManagement';
import { HandoverReports } from './pages/HandoverReports';
import { UserManagement } from './pages/UserManagement';

const ProtectedRoute = ({ children }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  return children;
};

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected Routes */}
          <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
          <Route path="/projects" element={<ProtectedRoute><Projects /></ProtectedRoute>} />
          <Route path="/projects/:id" element={<ProtectedRoute><ProjectDetails /></ProtectedRoute>} />
          <Route path="/upload" element={<ProtectedRoute><DocumentUpload /></ProtectedRoute>} />
          <Route path="/knowledge" element={<ProtectedRoute><KnowledgeExtraction /></ProtectedRoute>} />
          <Route path="/gaps" element={<ProtectedRoute><KnowledgeGapDetector /></ProtectedRoute>} />
          <Route path="/approvals" element={<ProtectedRoute><ApprovalManagement /></ProtectedRoute>} />
          <Route path="/reports" element={<ProtectedRoute><HandoverReports /></ProtectedRoute>} />
          <Route path="/users" element={<ProtectedRoute><UserManagement /></ProtectedRoute>} />

          {/* Fallback Redirect */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
