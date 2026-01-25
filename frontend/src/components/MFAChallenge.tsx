import { useState, type FormEvent } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import { apiClient } from '../lib/api'
import { UserRole } from '../types/auth'

interface MFAVerifyResponse {
  token: string
  user: {
    id: string
    email: string
    name: string
    role: UserRole
    hospitalId: string
  }
}

export default function MFAChallenge() {
  const navigate = useNavigate()
  const location = useLocation()
  const { mfaToken, email } = location.state || {}

  const [code, setCode] = useState('')
  const [useBackupCode, setUseBackupCode] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  if (!mfaToken) {
    navigate('/login')
    return null
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    try {
      const response = await apiClient.post<MFAVerifyResponse>('/auth/mfa/verify', {
        mfaToken,
        code,
        isBackupCode: useBackupCode,
      })

      // Store token
      apiClient.setToken(response.token)
      localStorage.setItem('authToken', response.token)
      localStorage.setItem('user', JSON.stringify(response.user))

      // Role-based redirection
      switch (response.user.role) {
        case UserRole.ADMIN:
        case UserRole.TPA_MANAGER:
          navigate('/admin/dashboard')
          break
        case UserRole.DOCTOR:
          navigate('/doctor/eligibility')
          break
        case UserRole.BILLING_SPECIALIST:
          navigate('/billing/audit')
          break
        default:
          navigate('/admin/dashboard')
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Invalid code. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="max-w-md w-full space-y-8 p-8 bg-white rounded-lg shadow">
        <div>
          <h2 className="text-3xl font-bold text-center text-gray-900">
            Two-Factor Authentication
          </h2>
          <p className="mt-2 text-center text-gray-600">
            Enter the code from your authenticator app
          </p>
          {email && (
            <p className="mt-1 text-center text-sm text-gray-500">{email}</p>
          )}
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <div className="flex">
                <div className="ml-3">
                  <h3 className="text-sm font-medium text-red-800">{error}</h3>
                </div>
              </div>
            </div>
          )}

          <div>
            <label htmlFor="code" className="block text-sm font-medium text-gray-700">
              {useBackupCode ? 'Backup Code' : 'Authentication Code'}
            </label>
            <input
              id="code"
              name="code"
              type="text"
              required
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\s/g, ''))}
              className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 text-center text-2xl tracking-widest"
              placeholder={useBackupCode ? '••••••••' : '••••••'}
              maxLength={useBackupCode ? 8 : 6}
            />
          </div>

          <div className="flex items-center justify-center">
            <button
              type="button"
              onClick={() => setUseBackupCode(!useBackupCode)}
              className="text-sm text-blue-600 hover:text-blue-500"
            >
              {useBackupCode ? 'Use authenticator code' : 'Use backup code'}
            </button>
          </div>

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? 'Verifying...' : 'Verify'}
            </button>
          </div>

          <div className="text-center">
            <button
              type="button"
              onClick={() => navigate('/login')}
              className="text-sm text-gray-600 hover:text-gray-500"
            >
              Back to login
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
