import { useState } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import { Download, FileText, Calendar, TrendingUp, BarChart3, PieChart } from 'lucide-react'
import { apiClient } from '@/lib/api'
import { cn } from '@/lib/utils'

interface Report {
  id: string
  name: string
  type: 'csr_trend' | 'rejection_analysis' | 'policy_frequency' | 'benchmark'
  period: string
  generatedAt: string
  format: 'pdf' | 'excel'
}

interface ReportData {
  csrTrend: Array<{ month: string; csr: number }>
  rejectionReasons: Array<{ reason: string; count: number; percentage: number }>
  topPolicyClauses: Array<{ clause: string; frequency: number }>
  benchmarkComparison: {
    hospitalCSR: number
    industryAverage: number
    topPerformer: number
  }
  metrics: {
    totalClaims: number
    approvedClaims: number
    rejectedClaims: number
    avgProcessingTime: number
    costSavings: number
  }
}

export default function Reports() {
  const [selectedPeriod, setSelectedPeriod] = useState<'month' | 'quarter' | 'year'>('month')
  const [selectedType] = useState<'all' | 'csr_trend' | 'rejection_analysis' | 'policy_frequency' | 'benchmark'>('all')

  const { data: reports = [] } = useQuery<Report[]>({
    queryKey: ['reports', selectedType],
    queryFn: () => {
      const params = selectedType !== 'all' ? `?type=${selectedType}` : ''
      return apiClient.get(`/reports${params}`)
    },
  })

  const { data: reportData } = useQuery<ReportData>({
    queryKey: ['report-data', selectedPeriod],
    queryFn: () => apiClient.get(`/reports/data?period=${selectedPeriod}`),
  })

  const generateMutation = useMutation({
    mutationFn: async (data: { type: string; period: string; format: 'pdf' | 'excel' }) => {
      return apiClient.post('/reports/generate', data)
    },
  })

  const downloadMutation = useMutation({
    mutationFn: async (reportId: string) => {
      return apiClient.get(`/reports/${reportId}/download`)
    },
  })

  const handleGenerate = (type: string, format: 'pdf' | 'excel') => {
    generateMutation.mutate({ type, period: selectedPeriod, format })
  }

  const handleDownload = (reportId: string) => {
    downloadMutation.mutate(reportId)
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Reports & Analytics</h1>
        <p className="text-gray-600">View claim settlement reports and analytics</p>
      </div>

      {/* Period Selector */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Calendar className="h-5 w-5 text-gray-500" />
            <span className="font-medium text-gray-700">Time Period:</span>
          </div>
          <div className="flex space-x-2">
            {['month', 'quarter', 'year'].map((period) => (
              <button
                key={period}
                onClick={() => setSelectedPeriod(period as any)}
                className={cn(
                  'px-4 py-2 rounded-lg text-sm font-medium transition-colors',
                  selectedPeriod === period
                    ? 'bg-primary text-white'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                )}
              >
                {period.charAt(0).toUpperCase() + period.slice(1)}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Key Metrics */}
      {reportData && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-600 mb-1">Total Claims</p>
            <p className="text-2xl font-bold text-gray-900">{reportData.metrics.totalClaims}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-600 mb-1">Approved</p>
            <p className="text-2xl font-bold text-green-600">{reportData.metrics.approvedClaims}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-600 mb-1">Rejected</p>
            <p className="text-2xl font-bold text-red-600">{reportData.metrics.rejectedClaims}</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-600 mb-1">Avg Processing</p>
            <p className="text-2xl font-bold text-primary">{reportData.metrics.avgProcessingTime}s</p>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <p className="text-sm text-gray-600 mb-1">Cost Savings</p>
            <p className="text-2xl font-bold text-green-600">
              ${(reportData.metrics.costSavings / 1000).toFixed(0)}K
            </p>
          </div>
        </div>
      )}

      {/* CSR Trend Chart */}
      {reportData && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold flex items-center">
              <TrendingUp className="h-5 w-5 mr-2 text-primary" />
              CSR Trend Analysis
            </h2>
            <div className="flex space-x-2">
              <button
                onClick={() => handleGenerate('csr_trend', 'pdf')}
                className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 flex items-center space-x-1"
              >
                <Download className="h-4 w-4" />
                <span>PDF</span>
              </button>
              <button
                onClick={() => handleGenerate('csr_trend', 'excel')}
                className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 flex items-center space-x-1"
              >
                <Download className="h-4 w-4" />
                <span>Excel</span>
              </button>
            </div>
          </div>
          <div className="h-64 flex items-end space-x-2">
            {reportData.csrTrend.map((data, idx) => (
              <div key={idx} className="flex-1 flex flex-col items-center">
                <div
                  className="w-full bg-primary rounded-t"
                  style={{ height: `${data.csr * 100}%` }}
                ></div>
                <p className="text-xs text-gray-600 mt-2">{data.month}</p>
                <p className="text-xs font-medium text-gray-900">{(data.csr * 100).toFixed(0)}%</p>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Rejection Analysis */}
      {reportData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold flex items-center">
                <BarChart3 className="h-5 w-5 mr-2 text-primary" />
                Top Rejection Reasons
              </h2>
              <button
                onClick={() => handleGenerate('rejection_analysis', 'pdf')}
                className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50"
              >
                <Download className="h-4 w-4" />
              </button>
            </div>
            <div className="space-y-3">
              {reportData.rejectionReasons.map((reason, idx) => (
                <div key={idx}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-sm text-gray-700">{reason.reason}</span>
                    <span className="text-sm font-medium text-gray-900">{reason.count}</span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-primary h-2 rounded-full"
                      style={{ width: `${reason.percentage}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold flex items-center">
                <PieChart className="h-5 w-5 mr-2 text-primary" />
                Policy Clause Frequency
              </h2>
              <button
                onClick={() => handleGenerate('policy_frequency', 'excel')}
                className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50"
              >
                <Download className="h-4 w-4" />
              </button>
            </div>
            <div className="space-y-2">
              {reportData.topPolicyClauses.map((clause, idx) => (
                <div key={idx} className="flex items-center justify-between p-2 hover:bg-gray-50 rounded cursor-pointer">
                  <span className="text-sm text-gray-700">{clause.clause}</span>
                  <span className="text-sm font-medium text-primary">{clause.frequency}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Benchmark Comparison */}
      {reportData && (
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Benchmark Comparison</h2>
            <button
              onClick={() => handleGenerate('benchmark', 'pdf')}
              className="px-3 py-1 text-sm border border-gray-300 rounded hover:bg-gray-50 flex items-center space-x-1"
            >
              <Download className="h-4 w-4" />
              <span>Export</span>
            </button>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 bg-blue-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">Your Hospital</p>
              <p className="text-3xl font-bold text-blue-600">
                {(reportData.benchmarkComparison.hospitalCSR * 100).toFixed(1)}%
              </p>
            </div>
            <div className="p-4 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">Industry Average</p>
              <p className="text-3xl font-bold text-gray-600">
                {(reportData.benchmarkComparison.industryAverage * 100).toFixed(1)}%
              </p>
            </div>
            <div className="p-4 bg-green-50 rounded-lg">
              <p className="text-sm text-gray-600 mb-1">Top Performer</p>
              <p className="text-3xl font-bold text-green-600">
                {(reportData.benchmarkComparison.topPerformer * 100).toFixed(1)}%
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Generated Reports */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Generated Reports</h2>
        <div className="space-y-3">
          {reports.map((report) => (
            <div
              key={report.id}
              className="flex items-center justify-between p-4 border rounded-lg hover:shadow-md transition-shadow"
            >
              <div className="flex items-center space-x-3">
                <FileText className="h-6 w-6 text-primary" />
                <div>
                  <p className="font-medium text-gray-900">{report.name}</p>
                  <p className="text-sm text-gray-500">
                    {report.period} • Generated {new Date(report.generatedAt).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <button
                onClick={() => handleDownload(report.id)}
                className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 flex items-center space-x-2"
              >
                <Download className="h-4 w-4" />
                <span>Download {report.format.toUpperCase()}</span>
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

