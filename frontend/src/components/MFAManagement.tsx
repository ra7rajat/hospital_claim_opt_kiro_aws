import { useState, useEffect } from 'react'
import { apiClient } from '../lib/api'
import MFASetup from './MFASetup'

interface MFAStatus {
  enabled: boolean
  enrolledAt?: string
}

export default function MFAManagement() {
  const [mfaStatus, setMfaStatus] = useState<MFAStatus | null>(null)
  const [showSetup, setShowSetup] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    loadMFAStatus()
  }, [])

  const loadMFAStatus = async () => {
    setIsLoading(true)
    try {
      const status = await apiClient.get<MFAStatus>('/auth/mfa/status')
      setMfaStatus(status)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load MFA status')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDisableMFA = async () => {
    if (!confirm('Are you sure you want to disable two-factor authentication? This will make your account less secure.')) {
      return
    }

    setIsLoading(true)
    setError('')

    try {
      await apiClient.post('/auth/mfa/disable')
      await loadMFAStatus()
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to disable MFA')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSetupComplete = async () => {
    setShowSetup(false)
    await loadMFAStatus()
  }

  if (isLoading && !mfaStatus) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="text-gray-600">Loading...</div>
      </div>
    )
  }

  if (showSetup) {
    return (
      <MFASetup
        onComplete={handleSetupComplete}
        onCancel={() => setShowSetup(false)}
      />
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900">Two-Factor Authentication</h3>
        <p className="mt-1 text-sm text-gray-600">
          Add an extra layer of security to your account
        </p>
      </div>

      {error && (
        <div className="rounded-md bg-red-50 p-4">
          <div className="text-sm text-red-800">{error}</div>
        </div>
      )}

      <div className="bg-white shadow sm:rounded-lg">
        <div className="px-4 py-5 sm:p-6">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h4 className="text-base font-medium text-gray-900">
                {mfaStatus?.enabled ? 'MFA Enabled' : 'MFA Disabled'}
              </h4>
              <p className="mt-1 text-sm text-gray-600">
                {mfaStatus?.enabled
                  ? `Two-factor authentication is active. Enrolled on ${new Date(mfaStatus.enrolledAt || '').toLocaleDateString()}`
                  : 'Protect your account with two-factor authentication'}
              </p>
            </div>
            <div className="ml-4">
              {mfaStatus?.enabled ? (
                <button
                  onClick={handleDisableMFA}
                  disabled={isLoading}
                  className="px-4 py-2 border border-red-300 rounded-md text-sm font-medium text-red-700 hover:bg-red-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Disabling...' : 'Disable'}
                </button>
              ) : (
                <button
                  onClick={() => setShowSetup(true)}
                  disabled={isLoading}
                  className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Enable MFA
                </button>
              )}
            </div>
          </div>
        </div>
      </div>

      {mfaStatus?.enabled && (
        <div className="bg-blue-50 border border-blue-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-blue-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <p className="text-sm text-blue-700">
                Your account is protected with two-factor authentication. You'll need your authenticator app or backup codes to sign in.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
