import { useState, useEffect } from 'react'
import { CheckCircle, XCircle, AlertCircle, Download, Filter, Search, FileText } from 'lucide-react'
import { apiClient } from '@/lib/api'
import { cn } from '@/lib/utils'

interface BatchResultsProps {
  batchId: string
}

interface BatchResult {
  rowNumber: number
  patientId: string
  status: string
  covered: boolean
  coveragePercentage: number
  preAuthRequired: boolean
  copay: number
  deductible: number
  outOfPocketMax: number
  error?: string
  timestamp: string
}

interface BatchSummary {
  total: number
  covered: number
  notCovered: number
  errors: number
  preAuthRequired: number
  coverageRate: number
  errorRate: number
  avgCoveragePercentage: number
  totalCopay: number
  totalDeductible: number
}

interface BatchResultsData {
  batchId: string
  summary: BatchSummary
  results: BatchResult[]
  totalResults: number
}

export default function BatchResults({ batchId }: BatchResultsProps) {
  const [data, setData] = useState<BatchResultsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [searchQuery, setSearchQuery] = useState('')
  const [expandedRow, setExpandedRow] = useState<number | null>(null)

  useEffect(() => {
    fetchResults()
  }, [batchId, statusFilter])

  const fetchResults = async () => {
    try {
      setLoading(true)
      const url = statusFilter
        ? `/eligibility/batch/results?batchId=${batchId}&status=${statusFilter}`
        : `/eligibility/batch/results?batchId=${batchId}`
      
      const response = await apiClient.get<BatchResultsData>(url)
      setData(response)
      setLoading(false)
    } catch (err) {
      setError('Failed to fetch batch results')
      setLoading(false)
    }
  }

  const handleExportCSV = async () => {
    try {
      const response = await apiClient.post<{ url: string }>(
        '/eligibility/batch/export',
        {
          batchId,
          format: 'csv',
          statusFilter
        }
      )
      window.open(response.url, '_blank')
    } catch (err) {
      alert('Failed to export results')
    }
  }

  const handleExportPDF = async () => {
    try {
      const response = await apiClient.post<{ url: string }>(
        '/eligibility/batch/export',
        {
          batchId,
          format: 'pdf',
          statusFilter
        }
      )
      window.open(response.url, '_blank')
    } catch (err) {
      alert('Failed to export results')
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COVERED':
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case 'NOT_COVERED':
        return <XCircle className="h-5 w-5 text-red-600" />
      case 'ERROR':
        return <AlertCircle className="h-5 w-5 text-red-600" />
      default:
        return <AlertCircle className="h-5 w-5 text-gray-600" />
    }
  }

  const getStatusBadge = (status: string) => {
    const baseClasses = 'px-2 py-1 text-xs font-medium rounded-full'
    switch (status) {
      case 'COVERED':
        return <span className={cn(baseClasses, 'bg-green-100 text-green-800')}>Covered</span>
      case 'NOT_COVERED':
        return <span className={cn(baseClasses, 'bg-red-100 text-red-800')}>Not Covered</span>
      case 'ERROR':
        return <span className={cn(baseClasses, 'bg-red-100 text-red-800')}>Error</span>
      default:
        return <span className={cn(baseClasses, 'bg-gray-100 text-gray-800')}>{status}</span>
    }
  }

  const filteredResults = data?.results.filter(result => {
    if (!searchQuery) return true
    return result.patientId.toLowerCase().includes(searchQuery.toLowerCase())
  }) || []

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (error || !data) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error || 'No results found'}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Summary Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <div className="p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600 mb-1">Total</p>
          <p className="text-2xl font-bold text-gray-900">{data.summary.total}</p>
        </div>
        <div className="p-4 bg-green-50 rounded-lg">
          <p className="text-sm text-green-700 mb-1">Covered</p>
          <p className="text-2xl font-bold text-green-600">{data.summary.covered}</p>
          <p className="text-xs text-green-600 mt-1">{data.summary.coverageRate}%</p>
        </div>
        <div className="p-4 bg-red-50 rounded-lg">
          <p className="text-sm text-red-700 mb-1">Not Covered</p>
          <p className="text-2xl font-bold text-red-600">{data.summary.notCovered}</p>
        </div>
        <div className="p-4 bg-yellow-50 rounded-lg">
          <p className="text-sm text-yellow-700 mb-1">Pre-Auth</p>
          <p className="text-2xl font-bold text-yellow-600">{data.summary.preAuthRequired}</p>
        </div>
        <div className="p-4 bg-red-50 rounded-lg">
          <p className="text-sm text-red-700 mb-1">Errors</p>
          <p className="text-2xl font-bold text-red-600">{data.summary.errors}</p>
          <p className="text-xs text-red-600 mt-1">{data.summary.errorRate}%</p>
        </div>
      </div>

      {/* Financial Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="p-4 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-700 mb-1">Avg Coverage</p>
          <p className="text-2xl font-bold text-blue-600">
            {data.summary.avgCoveragePercentage.toFixed(1)}%
          </p>
        </div>
        <div className="p-4 bg-purple-50 rounded-lg">
          <p className="text-sm text-purple-700 mb-1">Total Copay</p>
          <p className="text-2xl font-bold text-purple-600">
            ${data.summary.totalCopay.toFixed(2)}
          </p>
        </div>
        <div className="p-4 bg-indigo-50 rounded-lg">
          <p className="text-sm text-indigo-700 mb-1">Total Deductible</p>
          <p className="text-2xl font-bold text-indigo-600">
            ${data.summary.totalDeductible.toFixed(2)}
          </p>
        </div>
      </div>

      {/* Filters and Actions */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div className="flex items-center space-x-4">
          {/* Status Filter */}
          <div className="flex items-center space-x-2">
            <Filter className="h-5 w-5 text-gray-500" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            >
              <option value="">All Status</option>
              <option value="COVERED">Covered</option>
              <option value="NOT_COVERED">Not Covered</option>
              <option value="ERROR">Errors</option>
            </select>
          </div>

          {/* Search */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search patient ID..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            />
          </div>
        </div>

        {/* Export Buttons */}
        <div className="flex items-center space-x-2">
          <button
            onClick={handleExportCSV}
            className="flex items-center space-x-2 px-4 py-2 text-sm bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            <Download className="h-4 w-4" />
            <span>Export CSV</span>
          </button>
          <button
            onClick={handleExportPDF}
            className="flex items-center space-x-2 px-4 py-2 text-sm bg-white border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
          >
            <FileText className="h-4 w-4" />
            <span>Export PDF</span>
          </button>
        </div>
      </div>

      {/* Results Table */}
      <div className="border border-gray-200 rounded-lg overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50 border-b border-gray-200">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Row
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Patient ID
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Coverage
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Pre-Auth
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Copay
                </th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredResults.map((result) => (
                <>
                  <tr
                    key={result.rowNumber}
                    className="hover:bg-gray-50 cursor-pointer"
                    onClick={() => setExpandedRow(
                      expandedRow === result.rowNumber ? null : result.rowNumber
                    )}
                  >
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {result.rowNumber}
                    </td>
                    <td className="px-4 py-3 text-sm font-medium text-gray-900">
                      {result.patientId}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <div className="flex items-center space-x-2">
                        {getStatusIcon(result.status)}
                        {getStatusBadge(result.status)}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {result.status !== 'ERROR' ? `${result.coveragePercentage}%` : '-'}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {result.preAuthRequired ? (
                        <span className="px-2 py-1 text-xs font-medium bg-yellow-100 text-yellow-800 rounded-full">
                          Required
                        </span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-900">
                      {result.status !== 'ERROR' ? `$${result.copay.toFixed(2)}` : '-'}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      <button className="text-primary hover:text-primary/80">
                        {expandedRow === result.rowNumber ? 'Hide' : 'Details'}
                      </button>
                    </td>
                  </tr>
                  {expandedRow === result.rowNumber && (
                    <tr>
                      <td colSpan={7} className="px-4 py-4 bg-gray-50">
                        <div className="space-y-2">
                          <h4 className="font-medium text-gray-900">Detailed Information</h4>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                              <p className="text-gray-600">Coverage Percentage</p>
                              <p className="font-medium">{result.coveragePercentage}%</p>
                            </div>
                            <div>
                              <p className="text-gray-600">Copay</p>
                              <p className="font-medium">${result.copay.toFixed(2)}</p>
                            </div>
                            <div>
                              <p className="text-gray-600">Deductible</p>
                              <p className="font-medium">${result.deductible.toFixed(2)}</p>
                            </div>
                            <div>
                              <p className="text-gray-600">Out-of-Pocket Max</p>
                              <p className="font-medium">${result.outOfPocketMax.toFixed(2)}</p>
                            </div>
                          </div>
                          {result.error && (
                            <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded">
                              <p className="text-sm text-red-800">{result.error}</p>
                            </div>
                          )}
                          <p className="text-xs text-gray-500 mt-2">
                            Processed: {new Date(result.timestamp).toLocaleString()}
                          </p>
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>

        {filteredResults.length === 0 && (
          <div className="text-center py-12">
            <p className="text-gray-500">No results found</p>
          </div>
        )}
      </div>

      {/* Results Count */}
      <div className="text-sm text-gray-600">
        Showing {filteredResults.length} of {data.totalResults} results
      </div>
    </div>
  )
}
