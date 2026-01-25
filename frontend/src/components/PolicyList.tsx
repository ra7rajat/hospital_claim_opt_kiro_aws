import { FileText, Clock, CheckCircle, AlertCircle, History } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Policy {
  id: string
  name: string
  status: 'processing' | 'completed' | 'failed'
  uploadedAt: string
  version: number
  extractionConfidence?: number
}

interface PolicyListProps {
  policies: Policy[]
  onPolicyClick: (policy: Policy) => void
  onVersionHistory: (policyId: string) => void
}

export default function PolicyList({ policies, onPolicyClick, onVersionHistory }: PolicyListProps) {
  const getStatusIcon = (status: Policy['status']) => {
    switch (status) {
      case 'processing':
        return <Clock className="h-5 w-5 text-yellow-500 animate-pulse" />
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'failed':
        return <AlertCircle className="h-5 w-5 text-red-500" />
    }
  }

  const getStatusText = (status: Policy['status']) => {
    switch (status) {
      case 'processing':
        return 'Processing'
      case 'completed':
        return 'Completed'
      case 'failed':
        return 'Failed'
    }
  }

  return (
    <div className="space-y-3">
      {policies.map((policy) => (
        <div
          key={policy.id}
          className="border rounded-lg p-4 hover:shadow-md transition-shadow cursor-pointer"
          onClick={() => onPolicyClick(policy)}
        >
          <div className="flex items-start justify-between">
            <div className="flex items-start space-x-3 flex-1">
              <FileText className="h-6 w-6 text-primary mt-1" />
              <div className="flex-1">
                <h3 className="font-medium text-gray-900">{policy.name}</h3>
                <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                  <span>Version {policy.version}</span>
                  <span>•</span>
                  <span>{new Date(policy.uploadedAt).toLocaleDateString()}</span>
                  {policy.extractionConfidence && (
                    <>
                      <span>•</span>
                      <span>
                        Confidence: {(policy.extractionConfidence * 100).toFixed(0)}%
                      </span>
                    </>
                  )}
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <div className={cn('flex items-center space-x-2 px-3 py-1 rounded-full text-sm', {
                'bg-yellow-50': policy.status === 'processing',
                'bg-green-50': policy.status === 'completed',
                'bg-red-50': policy.status === 'failed',
              })}>
                {getStatusIcon(policy.status)}
                <span>{getStatusText(policy.status)}</span>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  onVersionHistory(policy.id)
                }}
                className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded"
                title="View version history"
              >
                <History className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
