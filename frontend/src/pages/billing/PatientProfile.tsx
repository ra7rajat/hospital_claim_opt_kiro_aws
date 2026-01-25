import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { 
  User, 
  Phone, 
  Mail, 
  Calendar, 
  Shield, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  ArrowLeft,
  Loader2 
} from 'lucide-react'
import { apiClient } from '@/lib/api'
import { cn } from '@/lib/utils'
import ClaimsList from '@/components/patient/ClaimsList'
import RiskVisualization from '@/components/patient/RiskVisualization'
import RiskTrend from '@/components/patient/RiskTrend'
import RecommendationsList from '@/components/patient/RecommendationsList'
import MultiClaimAnalytics from '@/components/patient/MultiClaimAnalytics'

interface PatientDemographics {
  name: string
  date_of_birth: string | null
  gender: string | null
  contact_email: string | null
  contact_phone: string | null
  address: {
    street?: string
    city?: string
    state?: string
    zip?: string
  }
}

interface InsuranceInfo {
  policy_number: string | null
  policy_name: string | null
  policy_id: string | null
  coverage_start: string | null
  coverage_end: string | null
  tpa_name: string | null
  sum_insured: number
}

interface Claim {
  claim_id: string
  date: string
  amount: number
  status: 'pending' | 'approved' | 'rejected' | 'processing'
  risk_score: number
  settlement_ratio: number
  procedure_codes: string[]
  diagnosis_codes: string[]
  hospital_name: string
  rejection_reason?: string
}

interface RiskFactor {
  name: string
  value: number
  weight: number
  contribution: number
}

interface AggregatedRisk {
  risk_score: number
  risk_level: 'high' | 'medium' | 'low'
  factors: RiskFactor[]
  trend: 'increasing' | 'stable' | 'decreasing'
  hospital_average: number
  comparison: 'above' | 'below'
}

interface RiskTrendPoint {
  month: string
  risk_score: number
  claim_count: number
}

interface PatientProfile {
  patient_id: string
  demographics: PatientDemographics
  insurance_info: InsuranceInfo
  claims: Claim[]
  aggregated_risk: AggregatedRisk
  risk_trend: RiskTrendPoint[]
}

export default function PatientProfile() {
  const { patientId } = useParams<{ patientId: string }>()
  const navigate = useNavigate()
  const [sortBy, setSortBy] = useState<'date' | 'amount' | 'status' | 'risk_score'>('date')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')

  const { data: profile, isLoading, error } = useQuery({
    queryKey: ['patient-profile', patientId],
    queryFn: async () => {
      const response = await apiClient.get<PatientProfile>(`/patient/${patientId}/profile`)
      return response
    },
    enabled: !!patientId,
  })

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    )
  }

  if (error || !profile) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6 text-center">
          <p className="text-red-800">Failed to load patient profile</p>
          <button
            onClick={() => navigate(-1)}
            className="mt-4 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700"
          >
            Go Back
          </button>
        </div>
      </div>
    )
  }

  const { demographics, insurance_info, claims, aggregated_risk, risk_trend } = profile

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'increasing':
        return <TrendingUp className="h-5 w-5 text-red-500" />
      case 'decreasing':
        return <TrendingDown className="h-5 w-5 text-green-500" />
      default:
        return <Minus className="h-5 w-5 text-gray-500" />
    }
  }

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'medium':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'low':
        return 'text-green-600 bg-green-50 border-green-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <button
            onClick={() => navigate(-1)}
            className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <h1 className="text-3xl font-bold">{demographics.name}</h1>
            <p className="text-gray-600">Patient ID: {patientId}</p>
          </div>
        </div>
        <div className={cn('px-4 py-2 rounded-lg border-2 font-semibold', getRiskColor(aggregated_risk.risk_level))}>
          {aggregated_risk.risk_level.toUpperCase()} RISK
        </div>
      </div>

      {/* Demographics and Insurance Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Demographics Card */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <User className="h-5 w-5 mr-2" />
            Demographics
          </h2>
          <div className="space-y-3">
            {demographics.date_of_birth && (
              <div className="flex items-center text-sm">
                <Calendar className="h-4 w-4 mr-2 text-gray-400" />
                <span className="text-gray-600">Date of Birth:</span>
                <span className="ml-2 font-medium">{demographics.date_of_birth}</span>
              </div>
            )}
            {demographics.gender && (
              <div className="flex items-center text-sm">
                <User className="h-4 w-4 mr-2 text-gray-400" />
                <span className="text-gray-600">Gender:</span>
                <span className="ml-2 font-medium">{demographics.gender}</span>
              </div>
            )}
            {demographics.contact_email && (
              <div className="flex items-center text-sm">
                <Mail className="h-4 w-4 mr-2 text-gray-400" />
                <span className="text-gray-600">Email:</span>
                <span className="ml-2 font-medium">{demographics.contact_email}</span>
              </div>
            )}
            {demographics.contact_phone && (
              <div className="flex items-center text-sm">
                <Phone className="h-4 w-4 mr-2 text-gray-400" />
                <span className="text-gray-600">Phone:</span>
                <span className="ml-2 font-medium">{demographics.contact_phone}</span>
              </div>
            )}
            {demographics.address && Object.keys(demographics.address).length > 0 && (
              <div className="text-sm">
                <span className="text-gray-600">Address:</span>
                <p className="ml-6 font-medium">
                  {demographics.address.street && <>{demographics.address.street}<br /></>}
                  {demographics.address.city && demographics.address.state && 
                    `${demographics.address.city}, ${demographics.address.state} ${demographics.address.zip || ''}`
                  }
                </p>
              </div>
            )}
          </div>
        </div>

        {/* Insurance Info Card */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4 flex items-center">
            <Shield className="h-5 w-5 mr-2" />
            Insurance Information
          </h2>
          <div className="space-y-3">
            {insurance_info.policy_name && (
              <div className="text-sm">
                <span className="text-gray-600">Policy Name:</span>
                <span className="ml-2 font-medium">{insurance_info.policy_name}</span>
              </div>
            )}
            {insurance_info.policy_number && (
              <div className="text-sm">
                <span className="text-gray-600">Policy Number:</span>
                <span className="ml-2 font-medium">{insurance_info.policy_number}</span>
              </div>
            )}
            {insurance_info.tpa_name && (
              <div className="text-sm">
                <span className="text-gray-600">TPA:</span>
                <span className="ml-2 font-medium">{insurance_info.tpa_name}</span>
              </div>
            )}
            {insurance_info.sum_insured > 0 && (
              <div className="text-sm">
                <span className="text-gray-600">Sum Insured:</span>
                <span className="ml-2 font-medium">${insurance_info.sum_insured.toLocaleString()}</span>
              </div>
            )}
            {insurance_info.coverage_start && insurance_info.coverage_end && (
              <div className="text-sm">
                <span className="text-gray-600">Coverage Period:</span>
                <span className="ml-2 font-medium">
                  {insurance_info.coverage_start} to {insurance_info.coverage_end}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Risk Score Card */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Aggregated Risk Score</h2>
          <div className="flex items-center space-x-2">
            {getTrendIcon(aggregated_risk.trend)}
            <span className="text-sm text-gray-600 capitalize">{aggregated_risk.trend}</span>
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="text-center">
            <p className="text-sm text-gray-600 mb-1">Risk Score</p>
            <p className={cn('text-4xl font-bold', 
              aggregated_risk.risk_level === 'high' ? 'text-red-600' :
              aggregated_risk.risk_level === 'medium' ? 'text-yellow-600' :
              'text-green-600'
            )}>
              {aggregated_risk.risk_score}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600 mb-1">Hospital Average</p>
            <p className="text-4xl font-bold text-gray-600">{aggregated_risk.hospital_average}</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600 mb-1">Comparison</p>
            <p className={cn('text-2xl font-bold', 
              aggregated_risk.comparison === 'above' ? 'text-red-600' : 'text-green-600'
            )}>
              {aggregated_risk.comparison === 'above' ? 'Above' : 'Below'} Average
            </p>
          </div>
        </div>
        <RiskVisualization factors={aggregated_risk.factors} />
      </div>

      {/* Risk Trend Chart */}
      {risk_trend.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Risk Trend Over Time</h2>
          <RiskTrend data={risk_trend} />
        </div>
      )}

      {/* Multi-Claim Analytics */}
      <MultiClaimAnalytics claims={claims} />

      {/* Risk Mitigation Recommendations */}
      <RecommendationsList 
        patientId={patientId!} 
        riskFactors={aggregated_risk.factors}
        riskLevel={aggregated_risk.risk_level}
      />

      {/* Claims List */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">All Claims ({claims.length})</h2>
        <ClaimsList 
          claims={claims} 
          sortBy={sortBy}
          sortOrder={sortOrder}
          onSortChange={(field, order) => {
            setSortBy(field)
            setSortOrder(order)
          }}
        />
      </div>
    </div>
  )
}
