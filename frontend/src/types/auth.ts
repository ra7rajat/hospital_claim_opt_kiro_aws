export const UserRole = {
  ADMIN: 'admin',
  DOCTOR: 'doctor',
  BILLING_SPECIALIST: 'billing_specialist',
  TPA_MANAGER: 'tpa_manager',
} as const

export type UserRole = typeof UserRole[keyof typeof UserRole]

export interface User {
  id: string
  email: string
  name: string
  role: UserRole
  hospitalId: string
}

export interface AuthState {
  user: User | null
  isAuthenticated: boolean
  isLoading: boolean
}
