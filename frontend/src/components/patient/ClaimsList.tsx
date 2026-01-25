import { useState } from 'react'
import { 
  ChevronDown, 
  ChevronUp, 
  CheckCircle, 
  XCircle, 
  Clock, 
  AlertTriangle,
  TrendingUp,
  TrendingDown
} from 'lucide-react'
import { cn } from '@/lib/utils'

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

interface ClaimsListProps {
  claims: Claim[]
  sortBy: 'date' | 'amount' | 'status' | 'risk_score'
  sortOrder: 'asc' | 'desc'
  onSortChange: (field: 'date' | 'amount' | 'status' | 'risk_score', order: 'asc' | 'desc') => void
}

export default function ClaimsList({ claims, sortBy, sortOrder, onSortChange }: ClaimsListProps) {
  const [expandedClaim, setExpandedClaim] = useState<string | null>(null)

  const handleSort = (field: 'date' | 'amount' | 'status' | 'risk_score') => {
    if (sortBy === field) {
      // Toggle order
      onSortChange(field, sortOrder === 'asc' ? 'desc' : 'asc')
    } else {
      // New field, default to desc
      onSortChange(field, 'desc')
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className="h-5 w-5 text-green-500" />
      case 'rejected':
        return <XCircle className="h-5 w-5 text-red-500" />
      case 'processing':
        return <Clock className="h-5 w-5 text-blue-500" />
      case 'pending':
        return <AlertTriangle className="h-5 w-5 text-yellow-500" />
      default:
        return <Clock className="h-5 w-5 text-gray-500" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'approved':
        return 'text-green-600 bg-green-50'
      case 'rejected':
        return 'text-red-600 bg-red-50'
      case 'processing':
        return 'text-blue-600 bg-blue-50'
      case 'pending':
        return 'text-yellow-600 bg-yellow-50'
      default:
        return 'text-gray-600 bg-gray-50'
    }
  }

  const getRiskColor = (score: number) => {
    if (score >= 70) return 'text-red-600 bg-red-50'
    if (score >= 40) return 'text-yellow-600 bg-yellow-50'
    return 'text-green-600 bg-green-50'
  }

  const SortIcon = ({ field }: { field: string }) => {
    if (sortBy !== field) return null
    return sortOrder === 'asc' ? 
      <ChevronUp className="h-4 w-4 inline ml-1" /> : 
      <ChevronDown className="h-4 w-4 inline ml-1" />
  }

  // Sort claims
  const sortedClaims = [...claims].sort((a, b) => {
    let comparison = 0
    switch (sortBy) {
      case 'date':
        comparison = a.date.localeCompare(b.date)
        break
      case 'amount':
        comparison = a.amount - b.amount
        break
      case 'status':
        comparison = a.status.localeCompare(b.status)
        break
      case 'risk_score':
        comparison = a.risk_score - b.risk_score
        break
    }
    return sortOrder === 'asc' ? comparison : -comparison
  })

  if (claims.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No claims found for this patient
      </div>
    )
  }

  return (
    <div className="space-y-3">
      {/* Sort Controls */}
      <div className="flex items-center space-x-4 text-sm">
        <span className="text-gray-600">Sort by:</span>
        <button
          onClick={() => handleSort('date')}
          className={cn(
            'px-3 py-1 rounded-lg transition-colors',
            sortBy === 'date' ? 'bg-primary text-white' : 'bg-gray-100 hover:bg-gray-200'
          )}
        >
          Date <SortIcon field="date" />
        </button>
        <button
          onClick={() => handleSort('amount')}
          className={cn(
            'px-3 py-1 rounded-lg transition-colors',
            sortBy === 'amount' ? 'bg-primary text-white' : 'bg-gray-100 hover:bg-gray-200'
          )}
        >
          Amount <SortIcon field="amount" />
        </button>
        <button
          onClick={() => handleSort('status')}
          className={cn(
            'px-3 py-1 rounded-lg transition-colors',
            sortBy === 'status' ? 'bg-primary text-white' : 'bg-gray-100 hover:bg-gray-200'
          )}
        >
          Status <SortIcon field="status" />
        </button>
        <button
          onClick={() => handleSort('risk_score')}
          className={cn(
            'px-3 py-1 rounded-lg transition-colors',
            sortBy === 'risk_score' ? 'bg-primary text-white' : 'bg-gray-100 hover:bg-gray-200'
          )}
        >
          Risk Score <SortIcon field="risk_score" />
        </button>
      </div>

      {/* Claims Table */}
      <div className="space-y-2">
        {sortedClaims.map((claim) => (
          <div
            key={claim.claim_id}
            className="border border-gray-200 rounded-lg overflow-hidden hover:shadow-md transition-shadow"
          >
            {/* Claim Summary */}
            <div
              className="p-4 cursor-pointer hover:bg-gray-50"
              onClick={() => setExpandedClaim(expandedClaim === claim.claim_id ? null : claim.claim_id)}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4 flex-1">
                  {getStatusIcon(claim.status)}
                  <div>
                    <p className="font-medium">Claim #{claim.claim_id}</p>
                    <p className="text-sm text-gray-600">{claim.date}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-6">
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Amount</p>
                    <p className="font-semibold">${claim.amount.toLocaleString()}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Risk Score</p>
                    <p className={cn('font-semibold px-2 py-1 rounded', getRiskColor(claim.risk_score))}>
                      {claim.risk_score}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Status</p>
                    <p className={cn('font-semibold px-2 py-1 rounded capitalize', getStatusColor(claim.status))}>
                      {claim.status}
                    </p>
                  </div>
                  {expandedClaim === claim.claim_id ? 
                    <ChevronUp className="h-5 w-5 text-gray-400" /> : 
                    <ChevronDown className="h-5 w-5 text-gray-400" />
                  }
                </div>
              </div>
            </div>

            {/* Expanded Details */}
            {expandedClaim === claim.claim_id && (
              <div className="border-t border-gray-200 bg-gray-50 p-4 space-y-3">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Hospital</p>
                    <p className="font-medium">{claim.hospital_name || 'N/A'}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Settlement Ratio</p>
                    <div className="flex items-center space-x-2">
                      <p className="font-medium">{(claim.settlement_ratio * 100).toFixed(1)}%</p>
                      {claim.settlement_ratio >= 0.8 ? (
                        <TrendingUp className="h-4 w-4 text-green-500" />
                      ) : (
                        <TrendingDown className="h-4 w-4 text-red-500" />
                      )}
                    </div>
                  </div>
                </div>

                {claim.procedure_codes.length > 0 && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Procedure Codes</p>
                    <div className="flex flex-wrap gap-2">
                      {claim.procedure_codes.map((code, idx) => (
                        <span key={idx} className="px-2 py-1 bg-blue-100 text-blue-700 text-xs rounded">
                          {code}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {claim.diagnosis_codes.length > 0 && (
                  <div>
                    <p className="text-sm text-gray-600 mb-1">Diagnosis Codes</p>
                    <div className="flex flex-wrap gap-2">
                      {claim.diagnosis_codes.map((code, idx) => (
                        <span key={idx} className="px-2 py-1 bg-purple-100 text-purple-700 text-xs rounded">
                          {code}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {claim.rejection_reason && (
                  <div className="bg-red-50 border border-red-200 rounded p-3">
                    <p className="text-sm text-gray-600 mb-1">Rejection Reason</p>
                    <p className="text-sm text-red-800">{claim.rejection_reason}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
