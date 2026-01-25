import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  Lightbulb, 
  CheckCircle, 
  ChevronDown, 
  ChevronUp,
  TrendingUp,
  Loader2
} from 'lucide-react'
import { apiClient } from '@/lib/api'
import { cn } from '@/lib/utils'

interface RiskFactor {
  name: string
  value: number
  weight: number
  contribution: number
}

interface Recommendation {
  recommendation_id: string
  priority: 'high' | 'medium' | 'low'
  title: string
  description: string
  action_steps: string[]
  expected_impact: number
  effort: 'high' | 'medium' | 'low'
  category: string
  completed?: boolean
}

interface RecommendationsListProps {
  patientId: string
  riskFactors: RiskFactor[]
  riskLevel: 'high' | 'medium' | 'low'
}

export default function RecommendationsList({ 
  patientId, 
  riskFactors, 
  riskLevel 
}: RecommendationsListProps) {
  const [expandedRec, setExpandedRec] = useState<string | null>(null)
  const queryClient = useQueryClient()

  const { data: recommendations, isLoading } = useQuery({
    queryKey: ['recommendations', patientId],
    queryFn: async () => {
      const response = await apiClient.get<Recommendation[]>(
        `/patient/${patientId}/recommendations`
      )
      return response
    },
  })

  const completeMutation = useMutation({
    mutationFn: async (recommendationId: string) => {
      return apiClient.post(`/patient/${patientId}/recommendations/${recommendationId}/complete`, {})
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['recommendations', patientId] })
    },
  })

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high':
        return 'text-red-600 bg-red-50 border-red-200'
      case 'medium':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200'
      case 'low':
        return 'text-blue-600 bg-blue-50 border-blue-200'
      default:
        return 'text-gray-600 bg-gray-50 border-gray-200'
    }
  }

  const getEffortBadge = (effort: string) => {
    const colors = {
      high: 'bg-red-100 text-red-700',
      medium: 'bg-yellow-100 text-yellow-700',
      low: 'bg-green-100 text-green-700'
    }
    return colors[effort as keyof typeof colors] || 'bg-gray-100 text-gray-700'
  }

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="h-6 w-6 animate-spin text-primary" />
        </div>
      </div>
    )
  }

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4 flex items-center">
          <Lightbulb className="h-5 w-5 mr-2 text-yellow-500" />
          Risk Mitigation Recommendations
        </h2>
        <div className="text-center py-8 text-gray-500">
          <Lightbulb className="h-12 w-12 mx-auto mb-3 text-gray-300" />
          <p>No recommendations at this time</p>
          <p className="text-sm mt-1">Keep up the good work!</p>
        </div>
      </div>
    )
  }

  // Separate completed and active recommendations
  const activeRecs = recommendations.filter(r => !r.completed)
  const completedRecs = recommendations.filter(r => r.completed)

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold flex items-center">
          <Lightbulb className="h-5 w-5 mr-2 text-yellow-500" />
          Risk Mitigation Recommendations
        </h2>
        <div className="text-sm text-gray-600">
          {activeRecs.length} active • {completedRecs.length} completed
        </div>
      </div>

      {/* Active Recommendations */}
      {activeRecs.length > 0 && (
        <div className="space-y-3 mb-6">
          <h3 className="text-sm font-semibold text-gray-700 uppercase">Active Recommendations</h3>
          {activeRecs.map((rec) => (
            <div
              key={rec.recommendation_id}
              className={cn(
                'border-2 rounded-lg overflow-hidden transition-all',
                getPriorityColor(rec.priority)
              )}
            >
              {/* Recommendation Header */}
              <div
                className="p-4 cursor-pointer hover:bg-opacity-50"
                onClick={() => setExpandedRec(
                  expandedRec === rec.recommendation_id ? null : rec.recommendation_id
                )}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center space-x-2 mb-2">
                      <span className={cn(
                        'px-2 py-1 text-xs font-semibold rounded uppercase',
                        getPriorityColor(rec.priority)
                      )}>
                        {rec.priority}
                      </span>
                      <span className={cn(
                        'px-2 py-1 text-xs font-semibold rounded',
                        getEffortBadge(rec.effort)
                      )}>
                        {rec.effort} effort
                      </span>
                      <div className="flex items-center text-sm text-green-600">
                        <TrendingUp className="h-4 w-4 mr-1" />
                        <span className="font-medium">-{rec.expected_impact}% risk</span>
                      </div>
                    </div>
                    <h3 className="font-semibold text-lg mb-1">{rec.title}</h3>
                    <p className="text-sm text-gray-700">{rec.description}</p>
                  </div>
                  <div className="ml-4">
                    {expandedRec === rec.recommendation_id ? 
                      <ChevronUp className="h-5 w-5" /> : 
                      <ChevronDown className="h-5 w-5" />
                    }
                  </div>
                </div>
              </div>

              {/* Expanded Details */}
              {expandedRec === rec.recommendation_id && (
                <div className="border-t bg-white p-4 space-y-4">
                  <div>
                    <h4 className="font-semibold mb-2">Action Steps:</h4>
                    <ol className="space-y-2">
                      {rec.action_steps.map((step, idx) => (
                        <li key={idx} className="flex items-start text-sm">
                          <span className="font-semibold mr-2 text-primary">{idx + 1}.</span>
                          <span>{step}</span>
                        </li>
                      ))}
                    </ol>
                  </div>

                  <div className="flex items-center justify-between pt-3 border-t">
                    <div className="text-sm text-gray-600">
                      Category: <span className="font-medium capitalize">{rec.category.replace('_', ' ')}</span>
                    </div>
                    <button
                      onClick={() => completeMutation.mutate(rec.recommendation_id)}
                      disabled={completeMutation.isPending}
                      className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 flex items-center space-x-2"
                    >
                      {completeMutation.isPending ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin" />
                          <span>Marking...</span>
                        </>
                      ) : (
                        <>
                          <CheckCircle className="h-4 w-4" />
                          <span>Mark as Completed</span>
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Completed Recommendations */}
      {completedRecs.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-semibold text-gray-700 uppercase">Completed Recommendations</h3>
          {completedRecs.map((rec) => (
            <div
              key={rec.recommendation_id}
              className="border border-gray-200 rounded-lg p-4 bg-gray-50"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <CheckCircle className="h-5 w-5 text-green-500" />
                  <div>
                    <h3 className="font-medium text-gray-700">{rec.title}</h3>
                    <p className="text-sm text-gray-500">
                      Expected impact: -{rec.expected_impact}% risk reduction
                    </p>
                  </div>
                </div>
                <span className="text-xs text-gray-500 uppercase">Completed</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
