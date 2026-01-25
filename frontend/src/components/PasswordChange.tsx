import { useState, type FormEvent, useEffect } from 'react'
import { apiClient } from '../lib/api'

interface PasswordStrength {
  score: number
  feedback: string[]
}

export default function PasswordChange() {
  const [currentPassword, setCurrentPassword] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [passwordStrength, setPasswordStrength] = useState<PasswordStrength>({ score: 0, feedback: [] })

  useEffect(() => {
    if (newPassword) {
      calculatePasswordStrength(newPassword)
    } else {
      setPasswordStrength({ score: 0, feedback: [] })
    }
  }, [newPassword])

  const calculatePasswordStrength = (pwd: string) => {
    const feedback: string[] = []
    let score = 0

    if (pwd.length >= 8) score++
    else feedback.push('At least 8 characters')

    if (/[a-z]/.test(pwd)) score++
    else feedback.push('One lowercase letter')

    if (/[A-Z]/.test(pwd)) score++
    else feedback.push('One uppercase letter')

    if (/\d/.test(pwd)) score++
    else feedback.push('One number')

    if (/[^a-zA-Z0-9]/.test(pwd)) score++
    else feedback.push('One special character')

    setPasswordStrength({ score, feedback })
  }

  const getStrengthColor = () => {
    if (passwordStrength.score <= 2) return 'bg-red-500'
    if (passwordStrength.score <= 3) return 'bg-yellow-500'
    if (passwordStrength.score <= 4) return 'bg-blue-500'
    return 'bg-green-500'
  }

  const getStrengthText = () => {
    if (passwordStrength.score <= 2) return 'Weak'
    if (passwordStrength.score <= 3) return 'Fair'
    if (passwordStrength.score <= 4) return 'Good'
    return 'Strong'
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess(false)

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    if (passwordStrength.score < 5) {
      setError('Password does not meet requirements')
      return
    }

    setIsLoading(true)

    try {
      await apiClient.post('/auth/password/change', {
        currentPassword,
        newPassword,
      })

      setSuccess(true)
      setCurrentPassword('')
      setNewPassword('')
      setConfirmPassword('')

      setTimeout(() => setSuccess(false), 5000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to change password')
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900">Change Password</h3>
        <p className="mt-1 text-sm text-gray-600">
          Update your password to keep your account secure
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {error && (
          <div className="rounded-md bg-red-50 p-4">
            <div className="text-sm text-red-800">{error}</div>
          </div>
        )}

        {success && (
          <div className="rounded-md bg-green-50 p-4">
            <div className="text-sm text-green-800">Password changed successfully!</div>
          </div>
        )}

        <div>
          <label htmlFor="current-password" className="block text-sm font-medium text-gray-700">
            Current Password
          </label>
          <input
            id="current-password"
            name="current-password"
            type="password"
            autoComplete="current-password"
            required
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div>
          <label htmlFor="new-password" className="block text-sm font-medium text-gray-700">
            New Password
          </label>
          <input
            id="new-password"
            name="new-password"
            type="password"
            autoComplete="new-password"
            required
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
          {newPassword && (
            <div className="mt-2">
              <div className="flex items-center justify-between mb-1">
                <span className="text-xs text-gray-600">Password strength:</span>
                <span className={`text-xs font-medium ${passwordStrength.score >= 5 ? 'text-green-600' : 'text-gray-600'}`}>
                  {getStrengthText()}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className={`h-2 rounded-full transition-all ${getStrengthColor()}`}
                  style={{ width: `${(passwordStrength.score / 5) * 100}%` }}
                />
              </div>
              {passwordStrength.feedback.length > 0 && (
                <ul className="mt-2 text-xs text-gray-600 list-disc list-inside">
                  {passwordStrength.feedback.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>

        <div>
          <label htmlFor="confirm-password" className="block text-sm font-medium text-gray-700">
            Confirm New Password
          </label>
          <input
            id="confirm-password"
            name="confirm-password"
            type="password"
            autoComplete="new-password"
            required
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
          />
        </div>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={isLoading || passwordStrength.score < 5}
            className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Changing...' : 'Change Password'}
          </button>
        </div>
      </form>
    </div>
  )
}
