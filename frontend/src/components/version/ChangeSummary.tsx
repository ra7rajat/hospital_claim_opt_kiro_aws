import { TrendingUp, TrendingDown, Minus, FileText } from 'lucide-react'

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

interface ChangeSummaryProps {
  comparison: ComparisonResult
}

export default function ChangeSummary({ comparison }: ChangeSummaryProps) {
  const totalChanges = comparison.added.length + comparison.removed.length + comparison.modified.length
  const totalRules = totalChanges + comparison.unchanged.length

  // Group changes by category
  const categoryCounts = new Map<string, { added: number; removed: number; modified: number }>()

  comparison.added.forEach((rule) => {
    const current = categoryCounts.get(rule.category) || { added: 0, removed: 0, modified: 0 }
    categoryCounts.set(rule.category, { ...current, added: current.added + 1 })
  })

  comparison.removed.forEach((rule) => {
    const current = categoryCounts.get(rule.category) || { added: 0, removed: 0, modified: 0 }
    categoryCounts.set(rule.category, { ...current, removed: current.removed + 1 })
  })

  comparison.modified.forEach((rule) => {
    const current = categoryCounts.get(rule.category) || { added: 0, removed: 0, modified: 0 }
    categoryCounts.set(rule.category, { ...current, modified: current.modified + 1 })
  })

  return (
    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 border border-blue-200">
      <div className="flex items-center space-x-2 mb-4">
        <FileText className="h-6 w-6 text-blue-600" />
        <h3 className="text-lg font-semibold text-gray-900">Change Summary</h3>
      </div>

      {/* Overall Statistics */}
      <div className="grid grid-cols-4 gap-4 mb-6">
        <div className="bg-white rounded-lg p-4 border border-gray-200">
          <div className="text-2xl font-bold text-gray-900">{totalChanges}</div>
          <div className="text-sm text-gray-600">Total Changes</div>
        </div>
        <div className="bg-green-50 rounded-lg p-4 border border-green-200">
          <div className="flex items-center space-x-2 mb-1">
            <TrendingUp className="h-5 w-5 text-green-600" />
            <div className="text-2xl font-bold text-green-900">{comparison.added.length}</div>
          </div>
          <div className="text-sm text-green-700">Added Rules</div>
        </div>
        <div className="bg-red-50 rounded-lg p-4 border border-red-200">
          <div className="flex items-center space-x-2 mb-1">
            <TrendingDown className="h-5 w-5 text-red-600" />
            <div className="text-2xl font-bold text-red-900">{comparison.removed.length}</div>
          </div>
          <div className="text-sm text-red-700">Removed Rules</div>
        </div>
        <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200">
          <div className="flex items-center space-x-2 mb-1">
            <Minus className="h-5 w-5 text-yellow-600" />
            <div className="text-2xl font-bold text-yellow-900">{comparison.modified.length}</div>
          </div>
          <div className="text-sm text-yellow-700">Modified Rules</div>
        </div>
      </div>

      {/* Category Breakdown */}
      {categoryCounts.size > 0 && (
        <div>
          <h4 className="text-sm font-semibold text-gray-700 mb-3">Changes by Category</h4>
          <div className="space-y-2">
            {Array.from(categoryCounts.entries()).map(([category, counts]) => {
              const categoryTotal = counts.added + counts.removed + counts.modified
              return (
                <div key={category} className="bg-white rounded-lg p-3 border border-gray-200">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-medium text-gray-900">{category}</span>
                    <span className="text-sm text-gray-600">{categoryTotal} changes</span>
                  </div>
                  <div className="flex items-center space-x-4 text-sm">
                    {counts.added > 0 && (
                      <div className="flex items-center space-x-1 text-green-700">
                        <TrendingUp className="h-4 w-4" />
                        <span>{counts.added} added</span>
                      </div>
                    )}
                    {counts.removed > 0 && (
                      <div className="flex items-center space-x-1 text-red-700">
                        <TrendingDown className="h-4 w-4" />
                        <span>{counts.removed} removed</span>
                      </div>
                    )}
                    {counts.modified > 0 && (
                      <div className="flex items-center space-x-1 text-yellow-700">
                        <Minus className="h-4 w-4" />
                        <span>{counts.modified} modified</span>
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      )}

      {/* Change Percentage */}
      <div className="mt-4 pt-4 border-t border-blue-200">
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600">
            {comparison.unchanged.length} rules unchanged ({((comparison.unchanged.length / totalRules) * 100).toFixed(1)}%)
          </span>
          <span className="text-gray-600">
            {totalChanges} rules changed ({((totalChanges / totalRules) * 100).toFixed(1)}%)
          </span>
        </div>
        <div className="mt-2 h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-green-500 via-yellow-500 to-red-500"
            style={{ width: `${(totalChanges / totalRules) * 100}%` }}
          />
        </div>
      </div>
    </div>
  )
}
