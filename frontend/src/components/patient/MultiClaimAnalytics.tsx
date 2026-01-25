import { useMemo } from 'react'
import { 
  DollarSign, 
  TrendingUp, 
  TrendingDown, 
  AlertTriangle,
  Activity,
  PieChart
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

interface MultiClaimAnalyticsProps {
  claims: Claim[]
}

export default function MultiClaimAnalytics({ claims }: MultiClaimAnalyticsProps) {
  const analytics = useMemo(() => {
    if (claims.length === 0) {
      return {
        totalAmount: 0,
        averageSettlementRatio: 0,
        approvalRate: 0,
        rejectionReasons: [],
        procedureDistribution: [],
        monthlyTrend: []
      }
    }

    // Calculate total claim amount
    const totalAmount = claims.reduce((sum, claim) => sum + claim.amount, 0)

    // Calculate average settlement ratio
    const settledClaims = claims.filter(c => c.settlement_ratio > 0)
    const averageSettlementRatio = settledClaims.length > 0
      ? settledClaims.reduce((sum, c) => sum + c.settlement_ratio, 0) / settledClaims.length
      : 0

    // Calculate approval rate
    const approvedCount = claims.filter(c => c.status === 'approved').length
    const approvalRate = (approvedCount / claims.length) * 100

    // Analyze rejection reasons
    const rejectionReasons: { [key: string]: number } = {}
    claims.forEach(claim => {
      if (claim.status === 'rejected' && claim.rejection_reason) {
        rejectionReasons[claim.rejection_reason] = (rejectionReasons[claim.rejection_reason] || 0) + 1
      }
    })

    const topRejectionReasons = Object.entries(rejectionReasons)
      .map(([reason, count]) => ({
        reason,
        count,
        percentage: (count / claims.length) * 100
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5)

    // Analyze procedure distribution
    const procedureCounts: { [key: string]: number } = {}
    claims.forEach(claim => {
      claim.procedure_codes.forEach(code => {
        procedureCounts[code] = (procedureCounts[code] || 0) + 1
      })
    })

    const topProcedures = Object.entries(procedureCounts)
      .map(([code, count]) => ({
        code,
        count,
        percentage: (count / claims.length) * 100
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 5)

    // Calculate monthly trend
    const monthlyData: { [key: string]: { amount: number; count: number } } = {}
    claims.forEach(claim => {
      const month = claim.date.substring(0, 7) // YYYY-MM
      if (!monthlyData[month]) {
        monthlyData[month] = { amount: 0, count: 0 }
      }
      monthlyData[month].amount += claim.amount
      monthlyData[month].count += 1
    })

    const monthlyTrend = Object.entries(monthlyData)
      .map(([month, data]) => ({
        month,
        amount: data.amount,
        count: data.count,
        averageAmount: data.amount / data.count
      }))
      .sort((a, b) => a.month.localeCompare(b.month))

    return {
      totalAmount,
      averageSettlementRatio,
      approvalRate,
      rejectionReasons: topRejectionReasons,
      procedureDistribution: topProcedures,
      monthlyTrend
    }
  }, [claims])

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount)
  }

  const formatMonth = (month: string) => {
    const [year, monthNum] = month.split('-')
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    return `${monthNames[parseInt(monthNum) - 1]} ${year}`
  }

  if (claims.length === 0) {
    return null
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 space-y-6">
      <h2 className="text-xl font-semibold flex items-center">
        <Activity className="h-5 w-5 mr-2" />
        Multi-Claim Analytics
      </h2>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-blue-600 font-medium">Total Claim Amount</p>
            <DollarSign className="h-5 w-5 text-blue-600" />
          </div>
          <p className="text-2xl font-bold text-blue-900">
            {formatCurrency(analytics.totalAmount)}
          </p>
          <p className="text-xs text-blue-600 mt-1">
            Across {claims.length} claims
          </p>
        </div>

        <div className="bg-green-50 border border-green-200 rounded-lg p-4">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-green-600 font-medium">Avg Settlement Ratio</p>
            <TrendingUp className="h-5 w-5 text-green-600" />
          </div>
          <p className="text-2xl font-bold text-green-900">
            {(analytics.averageSettlementRatio * 100).toFixed(1)}%
          </p>
          <p className={cn(
            'text-xs mt-1',
            analytics.averageSettlementRatio >= 0.8 ? 'text-green-600' : 'text-yellow-600'
          )}>
            {analytics.averageSettlementRatio >= 0.8 ? 'Excellent' : 'Needs improvement'}
          </p>
        </div>

        <div className={cn(
          'border rounded-lg p-4',
          analytics.approvalRate >= 80 ? 'bg-green-50 border-green-200' :
          analytics.approvalRate >= 60 ? 'bg-yellow-50 border-yellow-200' :
          'bg-red-50 border-red-200'
        )}>
          <div className="flex items-center justify-between mb-2">
            <p className={cn(
              'text-sm font-medium',
              analytics.approvalRate >= 80 ? 'text-green-600' :
              analytics.approvalRate >= 60 ? 'text-yellow-600' :
              'text-red-600'
            )}>
              Approval Rate
            </p>
            {analytics.approvalRate >= 80 ? 
              <TrendingUp className="h-5 w-5 text-green-600" /> :
              <TrendingDown className="h-5 w-5 text-red-600" />
            }
          </div>
          <p className={cn(
            'text-2xl font-bold',
            analytics.approvalRate >= 80 ? 'text-green-900' :
            analytics.approvalRate >= 60 ? 'text-yellow-900' :
            'text-red-900'
          )}>
            {analytics.approvalRate.toFixed(1)}%
          </p>
          <p className="text-xs mt-1 text-gray-600">
            {claims.filter(c => c.status === 'approved').length} of {claims.length} approved
          </p>
        </div>
      </div>

      {/* Common Rejection Reasons */}
      {analytics.rejectionReasons.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-3 flex items-center">
            <AlertTriangle className="h-5 w-5 mr-2 text-red-500" />
            Common Rejection Reasons
          </h3>
          <div className="space-y-2">
            {analytics.rejectionReasons.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex-1">
                  <p className="text-sm font-medium text-red-900">{item.reason}</p>
                  <div className="mt-1 bg-red-200 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-red-500 h-full"
                      style={{ width: `${item.percentage}%` }}
                    />
                  </div>
                </div>
                <div className="ml-4 text-right">
                  <p className="text-sm font-bold text-red-900">{item.count}</p>
                  <p className="text-xs text-red-600">{item.percentage.toFixed(1)}%</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Policy Utilization Patterns */}
      {analytics.procedureDistribution.length > 0 && (
        <div>
          <h3 className="text-lg font-semibold mb-3 flex items-center">
            <PieChart className="h-5 w-5 mr-2 text-purple-500" />
            Most Utilized Procedures
          </h3>
          <div className="space-y-2">
            {analytics.procedureDistribution.map((item, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-purple-50 border border-purple-200 rounded-lg">
                <div className="flex-1">
                  <p className="text-sm font-medium text-purple-900">Procedure Code: {item.code}</p>
                  <div className="mt-1 bg-purple-200 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-purple-500 h-full"
                      style={{ width: `${item.percentage}%` }}
                    />
                  </div>
                </div>
                <div className="ml-4 text-right">
                  <p className="text-sm font-bold text-purple-900">{item.count}</p>
                  <p className="text-xs text-purple-600">{item.percentage.toFixed(1)}%</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Historical Performance Trend */}
      {analytics.monthlyTrend.length > 1 && (
        <div>
          <h3 className="text-lg font-semibold mb-3">Historical Performance</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-4 py-2 text-left font-medium text-gray-700">Month</th>
                  <th className="px-4 py-2 text-right font-medium text-gray-700">Claims</th>
                  <th className="px-4 py-2 text-right font-medium text-gray-700">Total Amount</th>
                  <th className="px-4 py-2 text-right font-medium text-gray-700">Avg Amount</th>
                </tr>
              </thead>
              <tbody>
                {analytics.monthlyTrend.map((item, idx) => (
                  <tr key={idx} className="border-b hover:bg-gray-50">
                    <td className="px-4 py-2 font-medium">{formatMonth(item.month)}</td>
                    <td className="px-4 py-2 text-right">{item.count}</td>
                    <td className="px-4 py-2 text-right">{formatCurrency(item.amount)}</td>
                    <td className="px-4 py-2 text-right">{formatCurrency(item.averageAmount)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
