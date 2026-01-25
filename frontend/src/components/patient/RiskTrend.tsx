import { useMemo } from 'react'
import { cn } from '@/lib/utils'

interface RiskTrendPoint {
  month: string
  risk_score: number
  claim_count: number
}

interface RiskTrendProps {
  data: RiskTrendPoint[]
}

export default function RiskTrend({ data }: RiskTrendProps) {
  // Calculate chart dimensions and scales
  const chartHeight = 200
  const chartWidth = 800
  const padding = { top: 20, right: 20, bottom: 40, left: 50 }
  
  const { maxRisk, points, xScale, yScale } = useMemo(() => {
    const maxRisk = Math.max(...data.map(d => d.risk_score), 100)
    const minRisk = 0
    
    const innerWidth = chartWidth - padding.left - padding.right
    const innerHeight = chartHeight - padding.top - padding.bottom
    
    const xScale = (index: number) => {
      return padding.left + (index / (data.length - 1)) * innerWidth
    }
    
    const yScale = (value: number) => {
      return padding.top + innerHeight - ((value - minRisk) / (maxRisk - minRisk)) * innerHeight
    }
    
    const points = data.map((d, i) => ({
      x: xScale(i),
      y: yScale(d.risk_score),
      ...d
    }))
    
    return { maxRisk, points, xScale, yScale }
  }, [data])
  
  // Create path for line chart
  const linePath = useMemo(() => {
    if (points.length === 0) return ''
    
    let path = `M ${points[0].x} ${points[0].y}`
    for (let i = 1; i < points.length; i++) {
      path += ` L ${points[i].x} ${points[i].y}`
    }
    return path
  }, [points])
  
  // Create path for area under line
  const areaPath = useMemo(() => {
    if (points.length === 0) return ''
    
    const bottomY = padding.top + (chartHeight - padding.top - padding.bottom)
    let path = `M ${points[0].x} ${bottomY}`
    path += ` L ${points[0].x} ${points[0].y}`
    for (let i = 1; i < points.length; i++) {
      path += ` L ${points[i].x} ${points[i].y}`
    }
    path += ` L ${points[points.length - 1].x} ${bottomY}`
    path += ' Z'
    return path
  }, [points])
  
  const getRiskColor = (score: number) => {
    if (score >= 70) return '#dc2626' // red-600
    if (score >= 40) return '#ca8a04' // yellow-600
    return '#16a34a' // green-600
  }
  
  // Format month for display
  const formatMonth = (month: string) => {
    const [year, monthNum] = month.split('-')
    const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    return `${monthNames[parseInt(monthNum) - 1]} ${year.slice(2)}`
  }
  
  if (data.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        No trend data available
      </div>
    )
  }
  
  return (
    <div className="space-y-4">
      {/* Chart */}
      <div className="overflow-x-auto">
        <svg 
          width={chartWidth} 
          height={chartHeight}
          className="mx-auto"
        >
          {/* Grid lines */}
          {[0, 25, 50, 75, 100].map((value) => {
            const y = yScale(value)
            return (
              <g key={value}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={chartWidth - padding.right}
                  y2={y}
                  stroke="#e5e7eb"
                  strokeWidth="1"
                />
                <text
                  x={padding.left - 10}
                  y={y + 4}
                  textAnchor="end"
                  fontSize="12"
                  fill="#6b7280"
                >
                  {value}
                </text>
              </g>
            )
          })}
          
          {/* Risk level zones */}
          <rect
            x={padding.left}
            y={yScale(100)}
            width={chartWidth - padding.left - padding.right}
            height={yScale(70) - yScale(100)}
            fill="#fee2e2"
            opacity="0.3"
          />
          <rect
            x={padding.left}
            y={yScale(70)}
            width={chartWidth - padding.left - padding.right}
            height={yScale(40) - yScale(70)}
            fill="#fef3c7"
            opacity="0.3"
          />
          <rect
            x={padding.left}
            y={yScale(40)}
            width={chartWidth - padding.left - padding.right}
            height={yScale(0) - yScale(40)}
            fill="#dcfce7"
            opacity="0.3"
          />
          
          {/* Area under line */}
          <path
            d={areaPath}
            fill="url(#gradient)"
            opacity="0.3"
          />
          
          {/* Gradient definition */}
          <defs>
            <linearGradient id="gradient" x1="0%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#3b82f6" stopOpacity="0.8" />
              <stop offset="100%" stopColor="#3b82f6" stopOpacity="0.1" />
            </linearGradient>
          </defs>
          
          {/* Line */}
          <path
            d={linePath}
            fill="none"
            stroke="#3b82f6"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
          
          {/* Data points */}
          {points.map((point, i) => (
            <g key={i}>
              <circle
                cx={point.x}
                cy={point.y}
                r="5"
                fill={getRiskColor(point.risk_score)}
                stroke="white"
                strokeWidth="2"
              />
              <title>
                {formatMonth(point.month)}: {point.risk_score.toFixed(1)} ({point.claim_count} claims)
              </title>
            </g>
          ))}
          
          {/* X-axis labels */}
          {points.map((point, i) => (
            <text
              key={i}
              x={point.x}
              y={chartHeight - padding.bottom + 20}
              textAnchor="middle"
              fontSize="12"
              fill="#6b7280"
            >
              {formatMonth(point.month)}
            </text>
          ))}
          
          {/* Y-axis label */}
          <text
            x={padding.left - 35}
            y={chartHeight / 2}
            textAnchor="middle"
            fontSize="12"
            fill="#6b7280"
            transform={`rotate(-90, ${padding.left - 35}, ${chartHeight / 2})`}
          >
            Risk Score
          </text>
        </svg>
      </div>
      
      {/* Summary Stats */}
      <div className="grid grid-cols-3 gap-4 text-center">
        <div>
          <p className="text-sm text-gray-600">Current Risk</p>
          <p className={cn('text-2xl font-bold', 
            data[data.length - 1].risk_score >= 70 ? 'text-red-600' :
            data[data.length - 1].risk_score >= 40 ? 'text-yellow-600' :
            'text-green-600'
          )}>
            {data[data.length - 1].risk_score.toFixed(1)}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Average Risk</p>
          <p className="text-2xl font-bold text-gray-700">
            {(data.reduce((sum, d) => sum + d.risk_score, 0) / data.length).toFixed(1)}
          </p>
        </div>
        <div>
          <p className="text-sm text-gray-600">Total Claims</p>
          <p className="text-2xl font-bold text-gray-700">
            {data.reduce((sum, d) => sum + d.claim_count, 0)}
          </p>
        </div>
      </div>
    </div>
  )
}
