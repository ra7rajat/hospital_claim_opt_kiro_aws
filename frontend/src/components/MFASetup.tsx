import { useState, useEffect } from 'react'
import { apiClient } from '../lib/api'

interface MFASetupData {
  secret: string
  qrCode: string
  backupCodes: string[]
}

interface MFASetupProps {
  onComplete?: () => void
  onCancel?: () => void
}

export default function MFASetup({ onComplete, onCancel }: MFASetupProps) {
  const [setupData, setSetupData] = useState<MFASetupData | null>(null)
  const [verificationCode, setVerificationCode] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [step, setStep] = useState<'setup' | 'verify' | 'backup'>('setup')
  const [backupCodesDownloaded, setBackupCodesDownloaded] = useState(false)

  useEffect(() => {
    loadSetupData()
  }, [])

  const loadSetupData = async () => {
    setIsLoading(true)
    try {
      const data = await apiClient.post<MFASetupData>('/auth/mfa/setup')
      setSetupData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load MFA setup')
    } finally {
      setIsLoading(false)
    }
  }

  const handleVerify = async () => {
    if (!setupData) return

    setError('')
    setIsLoading(true)

    try {
      await apiClient.post('/auth/mfa/enable', {
        secret: setupData.secret,
        code: verificationCode,
      })
      setStep('backup')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid code. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleDownloadBackupCodes = () => {
    if (!setupData) return

    const content = `MFA Backup Codes\n\nKeep these codes in a safe place. Each code can only be used once.\n\n${setupData.backupCodes.join('\n')}`
    const blob = new Blob([content], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'mfa-backup-codes.txt'
    a.click()
    URL.revokeObjectURL(url)
    setBackupCodesDownloaded(true)
  }

  const handleComplete = () => {
    if (onComplete) {
      onComplete()
    }
  }

  if (isLoading && !setupData) {
    return (
      <div className="flex justify-center items-center p-8">
        <div className="text-gray-600">Loading MFA setup...</div>
      </div>
    )
  }

  if (!setupData) {
    return (
      <div className="p-8">
        <div className="text-red-600">{error || 'Failed to load MFA setup'}</div>
      </div>
    )
  }

  return (
    <div className="max-w-2xl mx-auto p-6">
      {step === 'setup' && (
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Set Up Two-Factor Authentication</h3>
            <p className="mt-1 text-sm text-gray-600">
              Scan the QR code with your authenticator app (Google Authenticator, Authy, etc.)
            </p>
          </div>

          <div className="flex justify-center">
            <img src={setupData.qrCode} alt="MFA QR Code" className="border rounded-lg p-4" />
          </div>

          <div>
            <p className="text-sm text-gray-600 mb-2">Or enter this code manually:</p>
            <div className="bg-gray-100 p-3 rounded font-mono text-sm break-all">
              {setupData.secret}
            </div>
          </div>

          <div className="flex justify-end space-x-3">
            {onCancel && (
              <button
                onClick={onCancel}
                className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
              >
                Cancel
              </button>
            )}
            <button
              onClick={() => setStep('verify')}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700"
            >
              Next
            </button>
          </div>
        </div>
      )}

      {step === 'verify' && (
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Verify Your Setup</h3>
            <p className="mt-1 text-sm text-gray-600">
              Enter the 6-digit code from your authenticator app to verify the setup
            </p>
          </div>

          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="text-sm text-red-800">{error}</div>
            </div>
          )}

          <div>
            <label htmlFor="verification-code" className="block text-sm font-medium text-gray-700">
              Verification Code
            </label>
            <input
              id="verification-code"
              type="text"
              value={verificationCode}
              onChange={(e) => setVerificationCode(e.target.value.replace(/\s/g, ''))}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-center text-2xl tracking-widest"
              placeholder="••••••"
              maxLength={6}
            />
          </div>

          <div className="flex justify-end space-x-3">
            <button
              onClick={() => setStep('setup')}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Back
            </button>
            <button
              onClick={handleVerify}
              disabled={isLoading || verificationCode.length !== 6}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Verifying...' : 'Verify'}
            </button>
          </div>
        </div>
      )}

      {step === 'backup' && (
        <div className="space-y-6">
          <div>
            <h3 className="text-lg font-medium text-gray-900">Save Your Backup Codes</h3>
            <p className="mt-1 text-sm text-gray-600">
              Keep these codes in a safe place. You can use them to access your account if you lose your device.
            </p>
          </div>

          <div className="bg-yellow-50 border border-yellow-200 rounded-md p-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
              </div>
              <div className="ml-3">
                <p className="text-sm text-yellow-700">
                  Each code can only be used once. Download and store them securely.
                </p>
              </div>
            </div>
          </div>

          <div className="bg-gray-100 p-4 rounded-md">
            <div className="grid grid-cols-2 gap-2 font-mono text-sm">
              {setupData.backupCodes.map((code, index) => (
                <div key={index} className="bg-white p-2 rounded text-center">
                  {code}
                </div>
              ))}
            </div>
          </div>

          <div className="flex justify-end space-x-3">
            <button
              onClick={handleDownloadBackupCodes}
              className="px-4 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50"
            >
              Download Codes
            </button>
            <button
              onClick={handleComplete}
              disabled={!backupCodesDownloaded}
              className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Complete Setup
            </button>
          </div>

          {!backupCodesDownloaded && (
            <p className="text-sm text-gray-500 text-center">
              Please download your backup codes before completing setup
            </p>
          )}
        </div>
      )}
    </div>
  )
}
