import { cn } from '@/lib/utils'

interface RiskFactor {
  name: string
  value: number
  weight: number
  contribution: number
}

interface RiskVisualizationProps {
  factors: RiskFactor[]
}

export default function RiskVisualization({ factors }: RiskVisualizationProps) {
  const getFactorColor = (value: number) => {
    if (value >= 70) return 'bg-red-500'
    if (value >= 40) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  const getFactorTextColor = (value: number) => {
    if (value >= 70) return 'text-red-600'
    if (value >= 40) return 'text-yellow-600'
    return 'text-green-600'
  }

  return (
    <div className="space-y-4">
      <h3 className="text-lg font-semibold">Risk Factor Breakdown</h3>
      
      <div className="space-y-4">
        {factors.map((factor, idx) => (
          <div key={idx} className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center space-x-2">
                <span className="font-medium">{factor.name}</span>
                <span className="text-gray-500">(Weight: {(factor.weight * 100).toFixed(0)}%)</span>
              </div>
              <div className="flex items-center space-x-3">
                <span className={cn('font-semibold', getFactorTextColor(factor.value))}>
                  {factor.value.toFixed(1)}
                </span>
                <span className="text-gray-600">
                  Contribution: {factor.contribution.toFixed(1)}
                </span>
              </div>
            </div>
            
            {/* Progress Bar */}
            <div className="relative h-6 bg-gray-200 rounded-full overflow-hidden">
              <div
                className={cn('h-full transition-all duration-500', getFactorColor(factor.value))}
                style={{ width: `${Math.min(100, factor.value)}%` }}
              />
              <div className="absolute inset-0 flex items-center justify-center">
                <span className="text-xs font-medium text-gray-700">
                  {factor.value.toFixed(1)}%
                </span>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center space-x-6 text-sm pt-4 border-t">
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-green-500 rounded"></div>
          <span className="text-gray-600">Low Risk (0-39)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-yellow-500 rounded"></div>
          <span className="text-gray-600">Medium Risk (40-69)</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-red-500 rounded"></div>
          <span className="text-gray-600">High Risk (70+)</span>
        </div>
      </div>
    </div>
  )
}
