import { useState, useEffect } from 'react'
import { CheckCircle, XCircle, Loader2, AlertCircle } from 'lucide-react'
import { apiClient } from '@/lib/api'
import { cn } from '@/lib/utils'

interface BatchProgressProps {
  batchId: string
  onComplete: () => void
}

interface BatchStatus {
  batchId: string
  status: string
  totalRecords: number
  processedRecords: number
  successCount: number
  failureCount: number
  progress: number
  createdAt: string
  updatedAt: string
  completedAt?: string
}

export default function BatchProgress({ batchId, onComplete }: BatchProgressProps) {
  const [status, setStatus] = useState<BatchStatus | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [polling, setPolling] = useState(true)

  useEffect(() => {
    fetchStatus()
    
    // Poll every 2 seconds
    const interval = setInterval(() => {
      if (polling) {
        fetchStatus()
      }
    }, 2000)

    return () => clearInterval(interval)
  }, [batchId, polling])

  const fetchStatus = async () => {
    try {
      const response = await apiClient.get<BatchStatus>(
        `/eligibility/batch/status?batchId=${batchId}`
      )
      setStatus(response)

      // Stop polling if completed or failed
      if (response.status === 'COMPLETED' || response.status === 'FAILED') {
        setPolling(false)
        if (response.status === 'COMPLETED') {
          onComplete()
        }
      }
    } catch (err) {
      setError('Failed to fetch batch status')
      setPolling(false)
    }
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex items-start space-x-2">
          <XCircle className="h-5 w-5 text-red-600 mt-0.5" />
          <div>
            <p className="font-medium text-red-900">Error</p>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        </div>
      </div>
    )
  }

  if (!status) {
    return (
      <div className="flex items-center justify-center py-12">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  const getStatusIcon = () => {
    switch (status.status) {
      case 'COMPLETED':
        return <CheckCircle className="h-8 w-8 text-green-600" />
      case 'FAILED':
      case 'VALIDATION_FAILED':
        return <XCircle className="h-8 w-8 text-red-600" />
      case 'PROCESSING':
        return <Loader2 className="h-8 w-8 animate-spin text-primary" />
      default:
        return <AlertCircle className="h-8 w-8 text-yellow-600" />
    }
  }

  const getStatusText = () => {
    switch (status.status) {
      case 'COMPLETED':
        return 'Processing Complete'
      case 'FAILED':
        return 'Processing Failed'
      case 'VALIDATION_FAILED':
        return 'Validation Failed'
      case 'PROCESSING':
        return 'Processing...'
      default:
        return status.status
    }
  }

  const getStatusColor = () => {
    switch (status.status) {
      case 'COMPLETED':
        return 'text-green-900'
      case 'FAILED':
      case 'VALIDATION_FAILED':
        return 'text-red-900'
      case 'PROCESSING':
        return 'text-primary'
      default:
        return 'text-gray-900'
    }
  }

  return (
    <div className="space-y-6">
      {/* Status Header */}
      <div className="flex items-center space-x-4">
        {getStatusIcon()}
        <div>
          <h3 className={cn('text-xl font-bold', getStatusColor())}>
            {getStatusText()}
          </h3>
          <p className="text-sm text-gray-600">
            Batch ID: {batchId}
          </p>
        </div>
      </div>

      {/* Progress Bar */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium text-gray-700">
            Progress
          </span>
          <span className="text-sm font-medium text-gray-900">
            {status.progress.toFixed(0)}%
          </span>
        </div>
        <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
          <div
            className={cn(
              'h-full transition-all duration-500 rounded-full',
              status.status === 'COMPLETED'
                ? 'bg-green-600'
                : status.status === 'FAILED' || status.status === 'VALIDATION_FAILED'
                ? 'bg-red-600'
                : 'bg-primary'
            )}
            style={{ width: `${status.progress}%` }}
          />
        </div>
      </div>

      {/* Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600 mb-1">Total Records</p>
          <p className="text-2xl font-bold text-gray-900">
            {status.totalRecords}
          </p>
        </div>
        <div className="p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600 mb-1">Processed</p>
          <p className="text-2xl font-bold text-primary">
            {status.processedRecords}
          </p>
        </div>
        <div className="p-4 bg-green-50 rounded-lg">
          <p className="text-sm text-green-700 mb-1">Successful</p>
          <p className="text-2xl font-bold text-green-600">
            {status.successCount}
          </p>
        </div>
        <div className="p-4 bg-red-50 rounded-lg">
          <p className="text-sm text-red-700 mb-1">Failed</p>
          <p className="text-2xl font-bold text-red-600">
            {status.failureCount}
          </p>
        </div>
      </div>

      {/* Processing Message */}
      {status.status === 'PROCESSING' && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start space-x-2">
            <Loader2 className="h-5 w-5 text-blue-600 mt-0.5 animate-spin" />
            <div>
              <p className="font-medium text-blue-900">Processing in Progress</p>
              <p className="text-sm text-blue-700 mt-1">
                Please wait while we check eligibility for all patients. This may take a few moments.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Completion Message */}
      {status.status === 'COMPLETED' && (
        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-start space-x-2">
            <CheckCircle className="h-5 w-5 text-green-600 mt-0.5" />
            <div>
              <p className="font-medium text-green-900">Processing Complete</p>
              <p className="text-sm text-green-700 mt-1">
                All records have been processed successfully. View the results below.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Failure Message */}
      {(status.status === 'FAILED' || status.status === 'VALIDATION_FAILED') && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <div className="flex items-start space-x-2">
            <XCircle className="h-5 w-5 text-red-600 mt-0.5" />
            <div>
              <p className="font-medium text-red-900">Processing Failed</p>
              <p className="text-sm text-red-700 mt-1">
                There was an error processing your batch. Please check the file and try again.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Timestamps */}
      <div className="text-xs text-gray-500 space-y-1">
        <p>Started: {new Date(status.createdAt).toLocaleString()}</p>
        <p>Last Updated: {new Date(status.updatedAt).toLocaleString()}</p>
        {status.completedAt && (
          <p>Completed: {new Date(status.completedAt).toLocaleString()}</p>
        )}
      </div>
    </div>
  )
}
