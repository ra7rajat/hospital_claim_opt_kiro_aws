import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Search, Download, Eye } from 'lucide-react'
import { apiClient } from '@/lib/api'
import { cn } from '@/lib/utils'

interface AuditEntry {
  audit_id: string
  user_id: string
  action: string
  resource_type: string
  resource_id: string
  timestamp: string
  details: Record<string, any>
  ip_address: string
  before_state?: Record<string, any>
  after_state?: Record<string, any>
}

export default function AuditLogs() {
  const [searchQuery, setSearchQuery] = useState('')
  const [actionFilter, setActionFilter] = useState<string>('all')
  const [resourceFilter, setResourceFilter] = useState<string>('all')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [selectedEntry, setSelectedEntry] = useState<AuditEntry | null>(null)

  const { data: auditLogs = [], isLoading } = useQuery<AuditEntry[]>({
    queryKey: ['audit-logs', actionFilter, resourceFilter, startDate, endDate],
    queryFn: async () => {
      const params = new URLSearchParams()
      if (actionFilter !== 'all') params.append('action', actionFilter)
      if (resourceFilter !== 'all') params.append('resourceType', resourceFilter)
      if (startDate) params.append('startDate', startDate)
      if (endDate) params.append('endDate', endDate)
      
      const response = await apiClient.get<{ entries: AuditEntry[] }>(
        `/audit/search?${params}`
      )
      return response.entries
    },
  })

  const filteredLogs = auditLogs.filter((log) =>
    log.user_id.toLowerCase().includes(searchQuery.toLowerCase()) ||
    log.resource_id.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const getActionColor = (action: string) => {
    switch (action) {
      case 'CREATE':
        return 'bg-green-100 text-green-800'
      case 'UPDATE':
        return 'bg-blue-100 text-blue-800'
      case 'DELETE':
        return 'bg-red-100 text-red-800'
      case 'VIEW':
        return 'bg-gray-100 text-gray-800'
      default:
        return 'bg-purple-100 text-purple-800'
    }
  }

  const handleExportCompliance = async () => {
    try {
      await apiClient.post('/audit/compliance-report', {
        startDate: startDate || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString(),
        endDate: endDate || new Date().toISOString(),
      })
    } catch (error) {
      console.error('Error generating compliance report:', error)
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Audit Logs</h1>
          <p className="text-gray-600">Complete audit trail of all system actions</p>
        </div>
        <button
          onClick={handleExportCompliance}
          className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 flex items-center space-x-2"
        >
          <Download className="h-5 w-5" />
          <span>Compliance Report</span>
        </button>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Search
            </label>
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="User ID or Resource ID..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Action Type
            </label>
            <select
              value={actionFilter}
              onChange={(e) => setActionFilter(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            >
              <option value="all">All Actions</option>
              <option value="CREATE">Create</option>
              <option value="UPDATE">Update</option>
              <option value="DELETE">Delete</option>
              <option value="VIEW">View</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Resource Type
            </label>
            <select
              value={resourceFilter}
              onChange={(e) => setResourceFilter(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
            >
              <option value="all">All Resources</option>
              <option value="POLICY">Policy</option>
              <option value="CLAIM">Claim</option>
              <option value="PATIENT">Patient</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Date Range
            </label>
            <div className="flex space-x-2">
              <input
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="flex-1 px-2 py-2 border border-gray-300 rounded-lg text-sm"
              />
              <input
                type="date"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="flex-1 px-2 py-2 border border-gray-300 rounded-lg text-sm"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Audit Log Entries */}
      <div className="bg-white rounded-lg shadow">
        <div className="p-6">
          <h2 className="text-xl font-semibold mb-4">
            Audit Entries ({filteredLogs.length})
          </h2>
          
          {isLoading ? (
            <div className="text-center py-12 text-gray-500">Loading audit logs...</div>
          ) : filteredLogs.length === 0 ? (
            <div className="text-center py-12 text-gray-500">No audit logs found</div>
          ) : (
            <div className="space-y-2">
              {filteredLogs.map((entry) => (
                <div
                  key={entry.audit_id}
                  className="border rounded-lg p-4 hover:shadow-md transition-shadow"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3 mb-2">
                        <span className={cn('px-3 py-1 rounded-full text-xs font-medium', getActionColor(entry.action))}>
                          {entry.action}
                        </span>
                        <span className="text-sm font-medium text-gray-900">
                          {entry.resource_type}
                        </span>
                        <span className="text-sm text-gray-500">
                          {entry.resource_id}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600">
                        <div>
                          <span className="font-medium">User:</span> {entry.user_id}
                        </div>
                        <div>
                          <span className="font-medium">Time:</span>{' '}
                          {new Date(entry.timestamp).toLocaleString()}
                        </div>
                        <div>
                          <span className="font-medium">IP:</span> {entry.ip_address}
                        </div>
                        <div className="flex items-center space-x-2">
                          <button
                            onClick={() => setSelectedEntry(entry)}
                            className="text-primary hover:underline flex items-center space-x-1"
                          >
                            <Eye className="h-4 w-4" />
                            <span>View Details</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Detail Modal */}
      {selectedEntry && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-lg max-w-3xl w-full max-h-[80vh] overflow-y-auto">
            <div className="p-6 border-b">
              <div className="flex items-center justify-between">
                <h2 className="text-2xl font-bold">Audit Entry Details</h2>
                <button
                  onClick={() => setSelectedEntry(null)}
                  className="text-gray-500 hover:text-gray-700"
                >
                  ✕
                </button>
              </div>
            </div>
            <div className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-500">Action</p>
                  <p className="text-lg font-semibold">{selectedEntry.action}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Resource</p>
                  <p className="text-lg font-semibold">
                    {selectedEntry.resource_type} - {selectedEntry.resource_id}
                  </p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">User</p>
                  <p className="text-lg font-semibold">{selectedEntry.user_id}</p>
                </div>
                <div>
                  <p className="text-sm font-medium text-gray-500">Timestamp</p>
                  <p className="text-lg font-semibold">
                    {new Date(selectedEntry.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>

              <div>
                <p className="text-sm font-medium text-gray-500 mb-2">Details</p>
                <pre className="bg-gray-50 p-4 rounded-lg text-sm overflow-x-auto">
                  {JSON.stringify(selectedEntry.details, null, 2)}
                </pre>
              </div>

              {selectedEntry.before_state && (
                <div>
                  <p className="text-sm font-medium text-gray-500 mb-2">Before State</p>
                  <pre className="bg-red-50 p-4 rounded-lg text-sm overflow-x-auto">
                    {JSON.stringify(selectedEntry.before_state, null, 2)}
                  </pre>
                </div>
              )}

              {selectedEntry.after_state && (
                <div>
                  <p className="text-sm font-medium text-gray-500 mb-2">After State</p>
                  <pre className="bg-green-50 p-4 rounded-lg text-sm overflow-x-auto">
                    {JSON.stringify(selectedEntry.after_state, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
