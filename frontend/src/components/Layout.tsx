import { Outlet, Link, useLocation, useNavigate } from 'react-router-dom'
import { Home, FileText, ClipboardCheck, BarChart3, Shield, LogOut } from 'lucide-react'
import SessionManager from './SessionManager'
import { apiClient } from '../lib/api'

export default function Layout() {
  const location = useLocation()
  const navigate = useNavigate()
  
  const isActive = (path: string) => location.pathname.startsWith(path)
  
  const handleLogout = async () => {
    try {
      await apiClient.post('/auth/logout')
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      apiClient.clearToken()
      localStorage.removeItem('authToken')
      localStorage.removeItem('user')
      navigate('/login')
    }
  }
  
  return (
    <SessionManager>
      <div className="min-h-screen bg-gray-50">
        <nav className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex">
                <div className="flex-shrink-0 flex items-center">
                  <h1 className="text-xl font-bold text-primary">
                    Hospital Claim Optimizer
                  </h1>
                </div>
                <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                  <Link
                    to="/admin/dashboard"
                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                      isActive('/admin/dashboard')
                        ? 'border-primary text-gray-900'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    }`}
                  >
                    <Home className="w-4 h-4 mr-2" />
                    Dashboard
                  </Link>
                  <Link
                    to="/admin/policies"
                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                      isActive('/admin/policies')
                        ? 'border-primary text-gray-900'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    }`}
                  >
                    <FileText className="w-4 h-4 mr-2" />
                    Policies
                  </Link>
                  <Link
                    to="/billing/audit"
                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                      isActive('/billing/audit')
                        ? 'border-primary text-gray-900'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    }`}
                  >
                    <ClipboardCheck className="w-4 h-4 mr-2" />
                    Bill Audit
                  </Link>
                  <Link
                    to="/admin/reports"
                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                      isActive('/admin/reports')
                        ? 'border-primary text-gray-900'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    }`}
                  >
                    <BarChart3 className="w-4 h-4 mr-2" />
                    Reports
                  </Link>
                  <Link
                    to="/admin/audit-logs"
                    className={`inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium ${
                      isActive('/admin/audit-logs')
                        ? 'border-primary text-gray-900'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    }`}
                  >
                    <Shield className="w-4 h-4 mr-2" />
                    Audit Logs
                  </Link>
                </div>
              </div>
              <div className="flex items-center">
                <button 
                  onClick={handleLogout}
                  className="inline-flex items-center px-3 py-2 border border-transparent text-sm font-medium rounded-md text-gray-500 hover:text-gray-700"
                >
                  <LogOut className="w-4 h-4 mr-2" />
                  Logout
                </button>
              </div>
            </div>
          </div>
        </nav>
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </SessionManager>
  )
}
