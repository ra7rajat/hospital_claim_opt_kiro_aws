import { useEffect, useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { apiClient } from '../lib/api'

interface SessionManagerProps {
  children: React.ReactNode
}

export default function SessionManager({ children }: SessionManagerProps) {
  const navigate = useNavigate()
  const [showWarning, setShowWarning] = useState(false)
  const [timeRemaining, setTimeRemaining] = useState(0)
  const [lastActivity, setLastActivity] = useState(Date.now())

  const SESSION_TIMEOUT = 30 * 60 * 1000 // 30 minutes
  const WARNING_THRESHOLD = 5 * 60 * 1000 // 5 minutes before timeout
  const CHECK_INTERVAL = 60 * 1000 // Check every minute

  const handleLogout = useCallback(async () => {
    try {
      await apiClient.post('/auth/logout')
    } catch (err) {
      console.error('Logout error:', err)
    } finally {
      apiClient.clearToken()
      localStorage.removeItem('authToken')
      localStorage.removeItem('user')
      navigate('/login', { state: { message: 'Your session has expired. Please log in again.' } })
    }
  }, [navigate])

  const renewSession = useCallback(async () => {
    try {
      const response = await apiClient.post<{ token: string }>('/auth/session/renew')
      apiClient.setToken(response.token)
      localStorage.setItem('authToken', response.token)
      setLastActivity(Date.now())
      setShowWarning(false)
    } catch (err) {
      console.error('Session renewal error:', err)
      handleLogout()
    }
  }, [handleLogout])

  const updateActivity = useCallback(() => {
    setLastActivity(Date.now())
    setShowWarning(false)
  }, [])

  useEffect(() => {
    // Track user activity
    const activityEvents = ['mousedown', 'keydown', 'scroll', 'touchstart']
    
    activityEvents.forEach(event => {
      window.addEventListener(event, updateActivity)
    })

    return () => {
      activityEvents.forEach(event => {
        window.removeEventListener(event, updateActivity)
      })
    }
  }, [updateActivity])

  useEffect(() => {
    // Check session status periodically
    const checkSession = () => {
      const now = Date.now()
      const timeSinceActivity = now - lastActivity
      const remaining = SESSION_TIMEOUT - timeSinceActivity

      if (remaining <= 0) {
        // Session expired
        handleLogout()
      } else if (remaining <= WARNING_THRESHOLD && !showWarning) {
        // Show warning
        setShowWarning(true)
        setTimeRemaining(Math.floor(remaining / 1000))
      } else if (remaining > WARNING_THRESHOLD && showWarning) {
        // Hide warning if user became active
        setShowWarning(false)
      }

      if (showWarning) {
        setTimeRemaining(Math.floor(remaining / 1000))
      }
    }

    const interval = setInterval(checkSession, CHECK_INTERVAL)
    checkSession() // Check immediately

    return () => clearInterval(interval)
  }, [lastActivity, showWarning, handleLogout])

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60)
    const secs = seconds % 60
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  return (
    <>
      {children}
      
      {showWarning && (
        <div className="fixed bottom-4 right-4 max-w-sm w-full bg-white rounded-lg shadow-lg border border-yellow-200 p-4 z-50">
          <div className="flex items-start">
            <div className="flex-shrink-0">
              <svg className="h-6 w-6 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div className="ml-3 flex-1">
              <h3 className="text-sm font-medium text-gray-900">
                Session Expiring Soon
              </h3>
              <p className="mt-1 text-sm text-gray-600">
                Your session will expire in {formatTime(timeRemaining)}
              </p>
              <div className="mt-3 flex space-x-3">
                <button
                  onClick={renewSession}
                  className="text-sm font-medium text-blue-600 hover:text-blue-500"
                >
                  Stay Logged In
                </button>
                <button
                  onClick={handleLogout}
                  className="text-sm font-medium text-gray-600 hover:text-gray-500"
                >
                  Log Out
                </button>
              </div>
            </div>
            <div className="ml-3 flex-shrink-0">
              <button
                onClick={() => setShowWarning(false)}
                className="inline-flex text-gray-400 hover:text-gray-500"
              >
                <span className="sr-only">Close</span>
                <svg className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  )
}
