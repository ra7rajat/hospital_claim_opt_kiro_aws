import { useState } from 'react'
import { X, AlertTriangle, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { apiClient } from '@/lib/api'
import VersionSelector from './VersionSelector'
import ChangeSummary from './ChangeSummary'
import ImpactAnalysis from './ImpactAnalysis'
import RollbackConfirmation from './RollbackConfirmation'

interface PolicyVersion {
  version: number
  createdAt: string
  createdBy: string
  description?: string
}

interface VersionComparisonProps {
  policyId: string
  onClose: () => void
}

interface ComparisonResult {
  added: Array<{
    rule_id: string
    category: string
    description: string
    details: any
  }>
  removed: Array<{
    rule_id: string
    category: string
    description: string
    details: any
  }>
  modified: Array<{
    rule_id: string
    category: string
    field: string
    old_value: any
    new_value: any
  }>
  unchanged: Array<{
    rule_id: string
    category: string
  }>
}

interface ImpactAnalysisResult {
  affected_claims: number
  estimated_settlement_change: number
  patients_to_notify: string[]
  confidence: 'high' | 'medium' | 'low'
  risk_level: 'high' | 'medium' | 'low'
}

export default function VersionComparison({ policyId, onClose }: VersionComparisonProps) {
  const [version1, setVersion1] = useState<number | null>(null)
  const [version2, setVersion2] = useState<number | null>(null)
  const [showRollbackDialog, setShowRollbackDialog] = useState(false)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')

  // Fetch available versions
  const { data: versions = [] } = useQuery<PolicyVersion[]>({
    queryKey: ['policy-versions', policyId],
    queryFn: async () => {
      return apiClient.get<PolicyVersion[]>(`/policies/${policyId}/versions`)
    },
  })

  // Fetch comparison data
  const { data: comparison, isLoading: isLoadingComparison } = useQuery<ComparisonResult>({
    queryKey: ['policy-comparison', policyId, version1, version2],
    queryFn: async () => {
      if (!version1 || !version2) return null
      return apiClient.get<ComparisonResult>(
        `/policies/${policyId}/compare?version1=${version1}&version2=${version2}`
      )
    },
    enabled: !!version1 && !!version2,
  })

  // Fetch impact analysis
  const { data: impact, isLoading: isLoadingImpact } = useQuery<ImpactAnalysisResult>({
    queryKey: ['policy-impact', policyId, version1, version2],
    queryFn: async () => {
      if (!version1 || !version2) return null
      return apiClient.get<ImpactAnalysisResult>(
        `/policies/${policyId}/impact?version1=${version1}&version2=${version2}`
      )
    },
    enabled: !!version1 && !!version2,
  })

  const handleRollback = () => {
    setShowRollbackDialog(true)
  }

  const categories = comparison
    ? Array.from(
        new Set([
          ...comparison.added.map((r) => r.category),
          ...comparison.removed.map((r) => r.category),
          ...comparison.modified.map((r) => r.category),
        ])
      )
    : []

  const filteredComparison = comparison
    ? {
        added:
          selectedCategory === 'all'
            ? comparison.added
            : comparison.added.filter((r) => r.category === selectedCategory),
        removed:
          selectedCategory === 'all'
            ? comparison.removed
            : comparison.removed.filter((r) => r.category === selectedCategory),
        modified:
          selectedCategory === 'all'
            ? comparison.modified
            : comparison.modified.filter((r) => r.category === selectedCategory),
        unchanged: comparison.unchanged,
      }
    : null

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div>
            <h2 className="text-2xl font-bold">Policy Version Comparison</h2>
            <p className="text-gray-600 mt-1">Compare two policy versions to see changes</p>
          </div>
          <button
            onClick={onClose}
            className="p-2 hover:bg-gray-100 rounded-full transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Version Selectors */}
        <div className="p-6 border-b bg-gray-50">
          <div className="grid grid-cols-2 gap-6">
            <VersionSelector
              label="Version 1 (Older)"
              versions={versions}
              selectedVersion={version1}
              onSelect={setVersion1}
              excludeVersion={version2}
            />
            <VersionSelector
              label="Version 2 (Newer)"
              versions={versions}
              selectedVersion={version2}
              onSelect={setVersion2}
              excludeVersion={version1}
            />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {!version1 || !version2 ? (
            <div className="text-center py-12 text-gray-500">
              <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p>Please select two versions to compare</p>
            </div>
          ) : isLoadingComparison || isLoadingImpact ? (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
              <p className="mt-4 text-gray-600">Loading comparison...</p>
            </div>
          ) : comparison ? (
            <div className="space-y-6">
              {/* Change Summary */}
              <ChangeSummary comparison={comparison} />

              {/* Impact Analysis */}
              {impact && <ImpactAnalysis impact={impact} />}

              {/* Category Filter */}
              {categories.length > 0 && (
                <div className="flex items-center space-x-2">
                  <span className="text-sm font-medium text-gray-700">Filter by category:</span>
                  <button
                    onClick={() => setSelectedCategory('all')}
                    className={`px-3 py-1 rounded-full text-sm ${
                      selectedCategory === 'all'
                        ? 'bg-primary text-white'
                        : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                    }`}
                  >
                    All
                  </button>
                  {categories.map((category) => (
                    <button
                      key={category}
                      onClick={() => setSelectedCategory(category)}
                      className={`px-3 py-1 rounded-full text-sm ${
                        selectedCategory === category
                          ? 'bg-primary text-white'
                          : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                      }`}
                    >
                      {category}
                    </button>
                  ))}
                </div>
              )}

              {/* Detailed Changes */}
              <div className="space-y-4">
                {/* Added Rules */}
                {filteredComparison && filteredComparison.added.length > 0 && (
                  <div className="border border-green-200 rounded-lg overflow-hidden">
                    <div className="bg-green-50 px-4 py-3 border-b border-green-200">
                      <div className="flex items-center space-x-2">
                        <TrendingUp className="h-5 w-5 text-green-600" />
                        <h3 className="font-semibold text-green-900">
                          Added Rules ({filteredComparison.added.length})
                        </h3>
                      </div>
                    </div>
                    <div className="divide-y divide-green-100">
                      {filteredComparison.added.map((rule, index) => (
                        <div key={index} className="p-4 bg-green-50">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-1">
                                <span className="text-xs font-medium text-green-700 bg-green-100 px-2 py-1 rounded">
                                  {rule.category}
                                </span>
                                <span className="text-sm font-mono text-gray-600">
                                  {rule.rule_id}
                                </span>
                              </div>
                              <p className="text-sm text-gray-900">{rule.description}</p>
                              {rule.details && (
                                <pre className="mt-2 text-xs bg-white p-2 rounded border border-green-200 overflow-x-auto">
                                  {JSON.stringify(rule.details, null, 2)}
                                </pre>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Removed Rules */}
                {filteredComparison && filteredComparison.removed.length > 0 && (
                  <div className="border border-red-200 rounded-lg overflow-hidden">
                    <div className="bg-red-50 px-4 py-3 border-b border-red-200">
                      <div className="flex items-center space-x-2">
                        <TrendingDown className="h-5 w-5 text-red-600" />
                        <h3 className="font-semibold text-red-900">
                          Removed Rules ({filteredComparison.removed.length})
                        </h3>
                      </div>
                    </div>
                    <div className="divide-y divide-red-100">
                      {filteredComparison.removed.map((rule, index) => (
                        <div key={index} className="p-4 bg-red-50">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-1">
                                <span className="text-xs font-medium text-red-700 bg-red-100 px-2 py-1 rounded">
                                  {rule.category}
                                </span>
                                <span className="text-sm font-mono text-gray-600">
                                  {rule.rule_id}
                                </span>
                              </div>
                              <p className="text-sm text-gray-900 line-through">{rule.description}</p>
                              {rule.details && (
                                <pre className="mt-2 text-xs bg-white p-2 rounded border border-red-200 overflow-x-auto">
                                  {JSON.stringify(rule.details, null, 2)}
                                </pre>
                              )}
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Modified Rules */}
                {filteredComparison && filteredComparison.modified.length > 0 && (
                  <div className="border border-yellow-200 rounded-lg overflow-hidden">
                    <div className="bg-yellow-50 px-4 py-3 border-b border-yellow-200">
                      <div className="flex items-center space-x-2">
                        <Minus className="h-5 w-5 text-yellow-600" />
                        <h3 className="font-semibold text-yellow-900">
                          Modified Rules ({filteredComparison.modified.length})
                        </h3>
                      </div>
                    </div>
                    <div className="divide-y divide-yellow-100">
                      {filteredComparison.modified.map((rule, index) => (
                        <div key={index} className="p-4 bg-yellow-50">
                          <div className="flex items-start justify-between">
                            <div className="flex-1">
                              <div className="flex items-center space-x-2 mb-1">
                                <span className="text-xs font-medium text-yellow-700 bg-yellow-100 px-2 py-1 rounded">
                                  {rule.category}
                                </span>
                                <span className="text-sm font-mono text-gray-600">
                                  {rule.rule_id}
                                </span>
                              </div>
                              <p className="text-sm font-medium text-gray-700 mb-2">
                                Field: {rule.field}
                              </p>
                              <div className="grid grid-cols-2 gap-4">
                                <div className="bg-red-50 p-3 rounded border border-red-200">
                                  <p className="text-xs font-medium text-red-700 mb-1">Old Value</p>
                                  <pre className="text-xs text-gray-900 overflow-x-auto">
                                    {JSON.stringify(rule.old_value, null, 2)}
                                  </pre>
                                </div>
                                <div className="bg-green-50 p-3 rounded border border-green-200">
                                  <p className="text-xs font-medium text-green-700 mb-1">New Value</p>
                                  <pre className="text-xs text-gray-900 overflow-x-auto">
                                    {JSON.stringify(rule.new_value, null, 2)}
                                  </pre>
                                </div>
                              </div>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* No Changes */}
                {filteredComparison &&
                  filteredComparison.added.length === 0 &&
                  filteredComparison.removed.length === 0 &&
                  filteredComparison.modified.length === 0 && (
                    <div className="text-center py-12 text-gray-500">
                      <p>No changes found in the selected category</p>
                    </div>
                  )}
              </div>
            </div>
          ) : (
            <div className="text-center py-12 text-gray-500">
              <AlertTriangle className="h-12 w-12 mx-auto mb-4 text-gray-400" />
              <p>Failed to load comparison data</p>
            </div>
          )}
        </div>

        {/* Footer */}
        {version1 && version2 && comparison && (
          <div className="p-6 border-t bg-gray-50 flex items-center justify-between">
            <div className="text-sm text-gray-600">
              Comparing version {version1} with version {version2}
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={onClose}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100 transition-colors"
              >
                Close
              </button>
              {version1 < version2 && (
                <button
                  onClick={handleRollback}
                  className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                >
                  Rollback to Version {version1}
                </button>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Rollback Confirmation Dialog */}
      {showRollbackDialog && version1 && (
        <RollbackConfirmation
          policyId={policyId}
          targetVersion={version1}
          onClose={() => setShowRollbackDialog(false)}
          onSuccess={() => {
            setShowRollbackDialog(false)
            onClose()
          }}
        />
      )}
    </div>
  )
}
