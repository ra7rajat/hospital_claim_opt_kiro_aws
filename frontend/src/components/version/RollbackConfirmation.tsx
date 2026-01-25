import { useState } from 'react'
import { AlertTriangle, X, RotateCcw } from 'lucide-react'
import { useMutation } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'

interface RollbackConfirmationProps {
  policyId: string
  targetVersion: number
  onClose: () => void
  onSuccess: () => void
}

export default function RollbackConfirmation({
  policyId,
  targetVersion,
  onClose,
  onSuccess,
}: RollbackConfirmationProps) {
  const [reason, setReason] = useState('')
  const [confirmed, setConfirmed] = useState(false)

  const rollbackMutation = useMutation({
    mutationFn: async () => {
      return apiClient.post(`/policies/${policyId}/rollback`, {
        target_version: targetVersion,
        reason: reason,
      })
    },
    onSuccess: () => {
      onSuccess()
    },
  })

  const handleRollback = () => {
    if (!confirmed || !reason.trim()) {
      return
    }
    rollbackMutation.mutate()
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-3">
            <div className="p-2 bg-red-100 rounded-full">
              <AlertTriangle className="h-6 w-6 text-red-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">Confirm Policy Rollback</h2>
              <p className="text-sm text-gray-600 mt-1">
                This action will create a new version based on version {targetVersion}
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
            disabled={rollbackMutation.isPending}
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-4">
          {/* Warning Banner */}
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-start space-x-3">
              <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
              <div className="flex-1">
                <h3 className="font-semibold text-red-900 mb-1">Important Information</h3>
                <ul className="text-sm text-red-800 space-y-1">
                  <li>• This will create a new version (not delete existing versions)</li>
                  <li>• All active claims will use the rolled-back policy rules</li>
                  <li>• Affected users will be notified of the change</li>
                  <li>• This action will be logged in the audit trail</li>
                  <li>• You can rollback again if needed</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Rollback Details */}
          <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
            <h3 className="font-semibold text-gray-900 mb-3">Rollback Details</h3>
            <div className="space-y-2 text-sm">
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Target Version:</span>
                <span className="font-medium text-gray-900">Version {targetVersion}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Action:</span>
                <span className="font-medium text-gray-900">Create new version from v{targetVersion}</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-gray-600">Timestamp:</span>
                <span className="font-medium text-gray-900">{new Date().toLocaleString()}</span>
              </div>
            </div>
          </div>

          {/* Reason Input */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Reason for Rollback <span className="text-red-600">*</span>
            </label>
            <textarea
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Please provide a detailed reason for this rollback (e.g., 'Incorrect coverage rules causing claim rejections')"
              className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent resize-none"
              rows={4}
              disabled={rollbackMutation.isPending}
            />
            <p className="mt-1 text-xs text-gray-500">
              This reason will be included in the audit log and notification emails
            </p>
          </div>

          {/* Confirmation Checkbox */}
          <div className="flex items-start space-x-3 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
            <input
              type="checkbox"
              id="confirm-rollback"
              checked={confirmed}
              onChange={(e) => setConfirmed(e.target.checked)}
              className="mt-1 h-4 w-4 text-primary focus:ring-primary border-gray-300 rounded"
              disabled={rollbackMutation.isPending}
            />
            <label htmlFor="confirm-rollback" className="text-sm text-gray-700 cursor-pointer">
              I understand that this will create a new policy version based on version {targetVersion}, and
              all active claims will immediately use the rolled-back policy rules. I have reviewed the
              impact analysis and am authorized to perform this action.
            </label>
          </div>

          {/* Error Message */}
          {rollbackMutation.isError && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="flex items-start space-x-3">
                <AlertTriangle className="h-5 w-5 text-red-600 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-semibold text-red-900 mb-1">Rollback Failed</h3>
                  <p className="text-sm text-red-800">
                    {rollbackMutation.error instanceof Error
                      ? rollbackMutation.error.message
                      : 'An error occurred while performing the rollback. Please try again.'}
                  </p>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t bg-gray-50 flex items-center justify-between">
          <button
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors"
            disabled={rollbackMutation.isPending}
          >
            Cancel
          </button>
          <button
            onClick={handleRollback}
            disabled={!confirmed || !reason.trim() || rollbackMutation.isPending}
            className="flex items-center space-x-2 px-6 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {rollbackMutation.isPending ? (
              <>
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Rolling back...</span>
              </>
            ) : (
              <>
                <RotateCcw className="h-4 w-4" />
                <span>Confirm Rollback</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  )
}
