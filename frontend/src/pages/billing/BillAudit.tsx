import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Upload, FileText, CheckCircle, XCircle, AlertTriangle, TrendingUp, Lightbulb, Loader2 } from 'lucide-react'
import { apiClient } from '@/lib/api'
import { cn } from '@/lib/utils'

interface LineItemResult {
  itemId: string
  description: string
  amount: number
  status: 'approved' | 'rejected' | 'review'
  reason?: string
  policyClause?: string
  suggestion?: string
}

interface AuditResult {
  lineItemResults: LineItemResult[]
  overallRiskScore: 'High' | 'Medium' | 'Low'
  predictedSettlementRatio: number
  optimizationSuggestions: string[]
  totalAmount: number
  approvedAmount: number
}

export default function BillAudit() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [patientId, setPatientId] = useState('')

  const auditMutation = useMutation({
    mutationFn: async (data: { file: File; patientId: string }) => {
      const formData = new FormData()
      formData.append('file', data.file)
      formData.append('patientId', data.patientId)
      return apiClient.post<AuditResult>('/audit/bill', formData)
    },
  })

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0])
    }
  }

  const handleAudit = () => {
    if (selectedFile && patientId) {
      auditMutation.mutate({ file: selectedFile, patientId })
    }
  }

  const result = auditMutation.data

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'rejected':
        return <XCircle className="h-5 w-5 text-red-500" />
      case 'review':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />
    }
  }

  const getRiskColor = (risk: string) => {
    switch (risk) {
      case 'High':
        return 'text-red-600 bg-red-50'
      case 'Medium':
        return 'text-yellow-600 bg-yellow-50'
      case 'Low':
        return 'text-green-600 bg-green-50'
    }
  }

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Bill Audit</h1>
        <p className="text-gray-600">Upload and audit medical bills before submission</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6 space-y-4">
        <h2 className="text-xl font-semibold">Upload Bill</h2>
        
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Patient ID *
          </label>
          <input
            type="text"
            value={patientId}
            onChange={(e) => setPatientId(e.target.value)}
            placeholder="Enter patient ID"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Medical Bill (PDF) *
          </label>
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
            <Upload className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-sm text-gray-600">
              <label className="text-primary cursor-pointer hover:underline">
                Choose file
                <input
                  type="file"
                  className="hidden"
                  accept=".pdf"
                  onChange={handleFileChange}
                />
              </label>
            </p>
            {selectedFile && (
              <p className="mt-2 text-sm text-gray-900 font-medium">{selectedFile.name}</p>
            )}
          </div>
        </div>

        <button
          onClick={handleAudit}
          disabled={!selectedFile || !patientId || auditMutation.isPending}
          className="w-full py-3 bg-primary text-white rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center space-x-2"
        >
          {auditMutation.isPending ? (
            <>
              <Loader2 className="h-5 w-5 animate-spin" />
              <span>Auditing...</span>
            </>
          ) : (
            <>
              <FileText className="h-5 w-5" />
              <span>Start Audit</span>
            </>
          )}
        </button>
      </div>

      {result && (
        <>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-sm text-gray-600 mb-1">Risk Score</p>
              <p className={cn('text-2xl font-bold px-3 py-1 rounded inline-block', getRiskColor(result.overallRiskScore))}>
                {result.overallRiskScore}
              </p>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-sm text-gray-600 mb-1">Predicted Settlement Ratio</p>
              <div className="flex items-baseline space-x-2">
                <p className="text-2xl font-bold text-primary">{(result.predictedSettlementRatio * 100).toFixed(1)}%</p>
                <TrendingUp className="h-5 w-5 text-green-500" />
              </div>
            </div>
            <div className="bg-white rounded-lg shadow p-6">
              <p className="text-sm text-gray-600 mb-1">Approved Amount</p>
              <p className="text-2xl font-bold text-gray-900">
                ${result.approvedAmount.toFixed(2)}
                <span className="text-sm text-gray-500 ml-2">/ ${result.totalAmount.toFixed(2)}</span>
              </p>
            </div>
          </div>

          {result.optimizationSuggestions.length > 0 && (
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <div className="flex items-start space-x-3">
                <Lightbulb className="h-6 w-6 text-blue-600 mt-1" />
                <div className="flex-1">
                  <h3 className="font-semibold text-blue-900 mb-2">Optimization Suggestions</h3>
                  <ul className="space-y-2">
                    {result.optimizationSuggestions.map((suggestion, idx) => (
                      <li key={idx} className="text-sm text-blue-800 flex items-start">
                        <span className="mr-2">•</span>
                        <span>{suggestion}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </div>
          )}

          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Line Item Analysis</h2>
            <div className="space-y-3">
              {result.lineItemResults.map((item) => (
                <div
                  key={item.itemId}
                  className={cn(
                    'border-l-4 p-4 rounded-r-lg',
                    item.status === 'approved' && 'border-green-500 bg-green-50',
                    item.status === 'rejected' && 'border-red-500 bg-red-50',
                    item.status === 'review' && 'border-yellow-500 bg-yellow-50'
                  )}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-2 mb-1">
                        {getStatusIcon(item.status)}
                        <span className="font-medium">{item.description}</span>
                      </div>
                      <p className="text-sm text-gray-600 mb-2">${item.amount.toFixed(2)}</p>
                      {item.reason && (
                        <p className="text-sm text-gray-700 mb-1">
                          <span className="font-medium">Reason:</span> {item.reason}
                        </p>
                      )}
                      {item.policyClause && (
                        <p className="text-sm text-gray-600 mb-1">
                          <span className="font-medium">Policy:</span> {item.policyClause}
                        </p>
                      )}
                      {item.suggestion && (
                        <p className="text-sm text-blue-700 mt-2">
                          <span className="font-medium">💡 Suggestion:</span> {item.suggestion}
                        </p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </>
      )}
    </div>
  )
}

