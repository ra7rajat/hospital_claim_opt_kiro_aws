import { createBrowserRouter, Navigate } from 'react-router-dom'
import Layout from './components/Layout'
import Login from './pages/Login'
import MFAChallenge from './components/MFAChallenge'
import PasswordReset from './components/PasswordReset'
import PasswordResetConfirm from './components/PasswordResetConfirm'
import AdminDashboard from './pages/admin/Dashboard'
import PolicyManagement from './pages/admin/PolicyManagement'
import Reports from './pages/admin/Reports'
import AuditLogs from './pages/admin/AuditLogs'
import Settings from './pages/admin/Settings'
import EligibilityCheck from './pages/doctor/EligibilityCheck'
import BillAudit from './pages/billing/BillAudit'
import PatientProfile from './pages/billing/PatientProfile'

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <Login />,
  },
  {
    path: '/mfa-challenge',
    element: <MFAChallenge />,
  },
  {
    path: '/password-reset',
    element: <PasswordReset />,
  },
  {
    path: '/password-reset/confirm',
    element: <PasswordResetConfirm />,
  },
  {
    path: '/',
    element: <Layout />,
    children: [
      {
        index: true,
        element: <Navigate to="/admin/dashboard" replace />,
      },
      {
        path: 'admin',
        children: [
          {
            path: 'dashboard',
            element: <AdminDashboard />,
          },
          {
            path: 'policies',
            element: <PolicyManagement />,
          },
          {
            path: 'reports',
            element: <Reports />,
          },
          {
            path: 'audit-logs',
            element: <AuditLogs />,
          },
          {
            path: 'settings',
            element: <Settings />,
          },
        ],
      },
      {
        path: 'doctor',
        children: [
          {
            path: 'eligibility',
            element: <EligibilityCheck />,
          },
        ],
      },
      {
        path: 'billing',
        children: [
          {
            path: 'audit',
            element: <BillAudit />,
          },
          {
            path: 'patient/:patientId',
            element: <PatientProfile />,
          },
        ],
      },
    ],
  },
])
