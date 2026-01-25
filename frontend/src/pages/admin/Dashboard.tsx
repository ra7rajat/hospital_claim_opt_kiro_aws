import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Filter, Bell, TrendingUp, TrendingDown, AlertCircle, Users, FileText, DollarSign } from 'lucide-react'
import { apiClient } from '@/lib/api'
import { cn } from '@/lib/utils'

interface Patient {
  id: string
  name: string
  claimCount: number
  totalAmount: number
  riskLevel: 'High' | 'Medium' | 'Low'
  status: 'pending' | 'in_review' | 'approved' | 'rejected'
  lastUpdated: string
}

interface DashboardMetrics {
  averageCSR: number
  csrTrend: number
  totalClaims: number
  claimsTrend: number
  avgProcessingTime: number
  processingTimeTrend: number
  totalValue: number
}

interface Alert {
  id: string
  type: 'high_risk' | 'pending_action' | 'deadline'
  message: string
  patientId: string
  timestamp: string
}

export default function AdminDashboard() {
  const [searchQuery, setSearchQuery] = useState('')
  const [riskFilter, setRiskFilter] = useState<'all' | 'High' | 'Medium' | 'Low'>('all')
  const [statusFilter, setStatusFilter] = useState<'all' | 'pending' | 'in_review' | 'approved' | 'rejected'>('all')

  const { data: metrics } = useQuery<DashboardMetrics>({
    queryKey: ['dashboard-metrics'],
    queryFn: () => apiClient.get('/dashboard/metrics'),
    refetchInterval: 30000, // Refresh every 30 seconds
  })

  const { data: patients = [] } = useQuery<Patient[]>({
    queryKey: ['patients', riskFilter, statusFilter],
    queryFn: () => {
      const params = new URLSearchParams()
      if (riskFilter !== 'all') params.append('risk', riskFilter)
      if (statusFilter !== 'all') params.append('status', statusFilter)
      return apiClient.get(`/dashboard/patients?${params}`)
    },
  })

  const { data: alerts = [] } = useQuery<Alert[]>({
    queryKey: ['alerts'],
    queryFn: () => apiClient.get('/dashboard/alerts'),
    refetchInterval: 30000,
  })

  const filteredPatients = patients.filter((patient) =>
    patient.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'High':
        return 'bg-red-100 text-red-800'
      case 'Medium':
        return 'bg-yellow-100 text-yellow-800'
      case 'Low':
        return 'bg-green-100 text-green-800'
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-gray-100 text-gray-800'
      case 'in_review':
        return 'bg-blue-100 text-blue-800'
      case 'approved':
        return 'bg-green-100 text-green-800'
      case 'rejected':
        return 'bg-red-100 text-red-800'
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">TPA Command Center</h1>
          <p className="text-gray-600">Manage claims and monitor performance</p>
        </div>
        <div className="relative">
          <button className="p-2 rounded-lg hover:bg-gray-100 relative">
            <Bell className="h-6 w-6 text-gray-600" />
            {alerts.length > 0 && (
              <span className="absolute top-1 right-1 h-3 w-3 bg-red-500 rounded-full"></span>
            )}
          </button>
        </div>
      </div>

      {/* Metrics Cards */}
      {metrics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-600">Average CSR</p>
              <TrendingUp className="h-5 w-5 text-primary" />
            </div>
            <p className="text-3xl font-bold text-gray-900">{(metrics.averageCSR * 100).toFixed(1)}%</p>
            <div className="flex items-center mt-2 text-sm">
              {metrics.csrTrend >= 0 ? (
                <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
              )}
              <span className={metrics.csrTrend >= 0 ? 'text-green-600' : 'text-red-600'}>
                {Math.abs(metrics.csrTrend).toFixed(1)}% from last month
              </span>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-600">Total Claims</p>
              <FileText className="h-5 w-5 text-primary" />
            </div>
            <p className="text-3xl font-bold text-gray-900">{metrics.totalClaims}</p>
            <div className="flex items-center mt-2 text-sm">
              {metrics.claimsTrend >= 0 ? (
                <TrendingUp className="h-4 w-4 text-green-500 mr-1" />
              ) : (
                <TrendingDown className="h-4 w-4 text-red-500 mr-1" />
              )}
              <span className={metrics.claimsTrend >= 0 ? 'text-green-600' : 'text-red-600'}>
                {Math.abs(metrics.claimsTrend).toFixed(0)} from last month
              </span>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-600">Avg Processing Time</p>
              <Users className="h-5 w-5 text-primary" />
            </div>
            <p className="text-3xl font-bold text-gray-900">{metrics.avgProcessingTime}s</p>
            <div className="flex items-center mt-2 text-sm">
              {metrics.processingTimeTrend <= 0 ? (
                <TrendingDown className="h-4 w-4 text-green-500 mr-1" />
              ) : (
                <TrendingUp className="h-4 w-4 text-red-500 mr-1" />
              )}
              <span className={metrics.processingTimeTrend <= 0 ? 'text-green-600' : 'text-red-600'}>
                {Math.abs(metrics.processingTimeTrend).toFixed(1)}s from last month
              </span>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-2">
              <p className="text-sm text-gray-600">Total Value</p>
              <DollarSign className="h-5 w-5 text-primary" />
            </div>
            <p className="text-3xl font-bold text-gray-900">
              ${(metrics.totalValue / 1000000).toFixed(1)}M
            </p>
            <p className="text-sm text-gray-500 mt-2">Claims value this month</p>
          </div>
        </div>
      )}

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start space-x-3">
            <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
            <div className="flex-1">
              <h3 className="font-semibold text-yellow-900 mb-2">Active Alerts ({alerts.length})</h3>
              <div className="space-y-2">
                {alerts.slice(0, 3).map((alert) => (
                  <div key={alert.id} className="text-sm text-yellow-800">
                    {alert.message}
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Filters and Search */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search patients..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <div className="flex items-center space-x-2">
              <Filter className="h-5 w-5 text-gray-500" />
              <span className="text-sm font-medium text-gray-700">Risk:</span>
              {['all', 'High', 'Medium', 'Low'].map((risk) => (
                <button
                  key={risk}
                  onClick={() => setRiskFilter(risk as any)}
                  className={cn(
                    'px-3 py-1 rounded-lg text-sm font-medium transition-colors',
                    riskFilter === risk
                      ? 'bg-primary text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  )}
                >
                  {risk}
                </button>
              ))}
            </div>

            <div className="flex items-center space-x-2">
              <span className="text-sm font-medium text-gray-700">Status:</span>
              {['all', 'pending', 'in_review', 'approved', 'rejected'].map((status) => (
                <button
                  key={status}
                  onClick={() => setStatusFilter(status as any)}
                  className={cn(
                    'px-3 py-1 rounded-lg text-sm font-medium transition-colors',
                    statusFilter === status
                      ? 'bg-primary text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  )}
                >
                  {status.replace('_', ' ')}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Patient List */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4">Active Patients</h2>
          <div className="space-y-3">
            {filteredPatients.map((patient) => (
              <div
                key={patient.id}
                className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
              >
                <div className="flex items-center justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium text-gray-900">{patient.name}</h3>
                    <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                      <span>{patient.claimCount} claims</span>
                      <span>•</span>
                      <span>${patient.totalAmount.toFixed(2)}</span>
                      <span>•</span>
                      <span>{new Date(patient.lastUpdated).toLocaleDateString()}</span>
                    </div>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span className={cn('px-3 py-1 rounded-full text-xs font-medium', getRiskColor(patient.riskLevel))}>
                      {patient.riskLevel} Risk
                    </span>
                    <span className={cn('px-3 py-1 rounded-full text-xs font-medium', getStatusColor(patient.status))}>
                      {patient.status.replace('_', ' ')}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}

