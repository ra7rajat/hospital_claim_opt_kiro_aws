import { AlertTriangle, TrendingUp, TrendingDown, Users, Activity, Download } from 'lucide-react'

interface ImpactAnalysisResult {
  affected_claims: number
  estimated_settlement_change: number
  patients_to_notify: string[]
  confidence: 'high' | 'medium' | 'low'
  risk_level: 'high' | 'medium' | 'low'
}

interface ImpactAnalysisProps {
  impact: ImpactAnalysisResult
}

export default function ImpactAnalysis({ impact }: ImpactAnalysisProps) {
  const getRiskColor = (level: string) => {
    switch (level) {
      case 'high':
        return 'text-red-700 bg-red-50 border-red-200'
      case 'medium':
        return 'text-yellow-700 bg-yellow-50 border-yellow-200'
      case 'low':
        return 'text-green-700 bg-green-50 border-green-200'
      default:
        return 'text-gray-700 bg-gray-50 border-gray-200'
    }
  }

  const getConfidenceColor = (level: string) => {
    switch (level) {
      case 'high':
        return 'text-green-700 bg-green-100'
      case 'medium':
        return 'text-yellow-700 bg-yellow-100'
      case 'low':
        return 'text-red-700 bg-red-100'
      default:
        return 'text-gray-700 bg-gray-100'
    }
  }

  const handleExportReport = () => {
    // Create a simple text report
    const report = `
Policy Version Impact Analysis Report
=====================================

Impact Summary:
- Affected Claims: ${impact.affected_claims}
- Estimated Settlement Change: ${impact.estimated_settlement_change > 0 ? '+' : ''}${impact.estimated_settlement_change.toFixed(2)}%
- Patients to Notify: ${impact.patients_to_notify.length}
- Risk Level: ${impact.risk_level.toUpperCase()}
- Confidence: ${impact.confidence.toUpperCase()}

Patients Requiring Notification:
${impact.patients_to_notify.map((id, i) => `${i + 1}. ${id}`).join('\n')}

Generated: ${new Date().toLocaleString()}
    `.trim()

    // Create and download the file
    const blob = new Blob([report], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `impact-analysis-${Date.now()}.txt`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
  }

  return (
    <div className={`rounded-lg p-6 border ${getRiskColor(impact.risk_level)}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <Activity className="h-6 w-6" />
          <h3 className="text-lg font-semibold">Impact Analysis</h3>
        </div>
        <button
          onClick={handleExportReport}
          className="flex items-center space-x-2 px-3 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-sm"
        >
          <Download className="h-4 w-4" />
          <span>Export Report</span>
        </button>
      </div>

      {/* Risk Level Banner */}
      <div className={`mb-4 p-3 rounded-lg border flex items-center space-x-3 ${getRiskColor(impact.risk_level)}`}>
        <AlertTriangle className="h-5 w-5" />
        <div className="flex-1">
          <div className="font-semibold">Risk Level: {impact.risk_level.toUpperCase()}</div>
          <div className="text-sm opacity-90">
            {impact.risk_level === 'high' && 'These changes may significantly impact active claims'}
            {impact.risk_level === 'medium' && 'These changes may moderately impact active claims'}
            {impact.risk_level === 'low' && 'These changes have minimal impact on active claims'}
          </div>
        </div>
        <div className={`px-3 py-1 rounded-full text-xs font-medium ${getConfidenceColor(impact.confidence)}`}>
          {impact.confidence.toUpperCase()} CONFIDENCE
        </div>
      </div>

      {/* Impact Metrics */}
      <div className="grid grid-cols-3 gap-4 mb-4">
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center space-x-2 mb-2">
            <Activity className="h-5 w-5 text-blue-600" />
            <span className="text-sm font-medium text-gray-700">Affected Claims</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">{impact.affected_claims}</div>
          <div className="text-xs text-gray-600 mt-1">Active claims impacted</div>
        </div>

        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center space-x-2 mb-2">
            {impact.estimated_settlement_change >= 0 ? (
              <TrendingUp className="h-5 w-5 text-green-600" />
            ) : (
              <TrendingDown className="h-5 w-5 text-red-600" />
            )}
            <span className="text-sm font-medium text-gray-700">Settlement Change</span>
          </div>
          <div
            className={`text-2xl font-bold ${
              impact.estimated_settlement_change >= 0 ? 'text-green-600' : 'text-red-600'
            }`}
          >
            {impact.estimated_settlement_change > 0 ? '+' : ''}
            {impact.estimated_settlement_change.toFixed(2)}%
          </div>
          <div className="text-xs text-gray-600 mt-1">Estimated change in settlement ratio</div>
        </div>

        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="flex items-center space-x-2 mb-2">
            <Users className="h-5 w-5 text-purple-600" />
            <span className="text-sm font-medium text-gray-700">Patients to Notify</span>
          </div>
          <div className="text-2xl font-bold text-gray-900">{impact.patients_to_notify.length}</div>
          <div className="text-xs text-gray-600 mt-1">Require notification of changes</div>
        </div>
      </div>

      {/* Patients List */}
      {impact.patients_to_notify.length > 0 && (
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <h4 className="text-sm font-semibold text-gray-700 mb-3">
            Patients Requiring Notification ({impact.patients_to_notify.length})
          </h4>
          <div className="max-h-40 overflow-y-auto">
            <div className="grid grid-cols-3 gap-2">
              {impact.patients_to_notify.slice(0, 30).map((patientId) => (
                <div
                  key={patientId}
                  className="px-3 py-2 bg-gray-50 rounded border border-gray-200 text-sm font-mono"
                >
                  {patientId}
                </div>
              ))}
            </div>
            {impact.patients_to_notify.length > 30 && (
              <div className="mt-2 text-sm text-gray-600 text-center">
                ... and {impact.patients_to_notify.length - 30} more patients
              </div>
            )}
          </div>
        </div>
      )}

      {/* Recommendations */}
      <div className="mt-4 p-4 bg-white rounded-lg border border-gray-200">
        <h4 className="text-sm font-semibold text-gray-700 mb-2">Recommendations</h4>
        <ul className="space-y-2 text-sm text-gray-600">
          {impact.affected_claims > 0 && (
            <li className="flex items-start space-x-2">
              <span className="text-blue-600 mt-0.5">•</span>
              <span>Review affected claims to ensure policy changes are applied correctly</span>
            </li>
          )}
          {impact.patients_to_notify.length > 0 && (
            <li className="flex items-start space-x-2">
              <span className="text-blue-600 mt-0.5">•</span>
              <span>Send notification emails to affected patients about policy changes</span>
            </li>
          )}
          {impact.estimated_settlement_change < -5 && (
            <li className="flex items-start space-x-2">
              <span className="text-red-600 mt-0.5">•</span>
              <span>
                Significant decrease in settlement ratio detected - consider reviewing changes before
                deployment
              </span>
            </li>
          )}
          {impact.risk_level === 'high' && (
            <li className="flex items-start space-x-2">
              <span className="text-red-600 mt-0.5">•</span>
              <span>High risk level - recommend stakeholder approval before proceeding</span>
            </li>
          )}
          {impact.confidence === 'low' && (
            <li className="flex items-start space-x-2">
              <span className="text-yellow-600 mt-0.5">•</span>
              <span>
                Low confidence in impact analysis - manual review recommended for critical changes
              </span>
            </li>
          )}
        </ul>
      </div>
    </div>
  )
}
