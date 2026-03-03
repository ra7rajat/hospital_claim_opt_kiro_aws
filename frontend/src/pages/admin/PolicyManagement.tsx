import { useState } from 'react'
import { useMutation, useQuery } from '@tanstack/react-query'
import PolicyUpload from '@/components/PolicyUpload'
import PolicyList from '@/components/PolicyList'
import PolicySearch from '@/components/PolicySearch'
import VersionComparison from '@/components/version/VersionComparison'
import { apiClient } from '@/lib/api'

interface Policy {
  id: string
  name: string
  status: 'processing' | 'completed' | 'failed'
  uploadedAt: string
  version: number
  extractionConfidence?: number
}

interface PoliciesResponse {
  policies: Policy[]
  total: number
}

export default function PolicyManagement() {
  const [searchQuery, setSearchQuery] = useState('')
  const [statusFilter, setStatusFilter] = useState<'all' | 'processing' | 'completed' | 'failed'>('all')
  const [selectedPolicyForComparison, setSelectedPolicyForComparison] = useState<string | null>(null)

  // Fetch policies
  const { data, refetch } = useQuery<PoliciesResponse>({
    queryKey: ['policies', statusFilter],
    queryFn: async () => {
      const params = statusFilter !== 'all' ? `?status=${statusFilter}` : ''
      return apiClient.get<PoliciesResponse>(`/policies${params}`)
    },
  })

  const policies = data?.policies || []

  // Upload mutation
  const uploadMutation = useMutation({
    mutationFn: async (file: File) => {
      const formData = new FormData()
      formData.append('file', file)
      return apiClient.post('/policies/upload', formData)
    },
    onSuccess: () => {
      refetch()
    },
  })

  const handleUpload = (file: File) => {
    uploadMutation.mutate(file)
  }

  const handlePolicyClick = (policy: Policy) => {
    console.log('Policy clicked:', policy)
    // Navigate to policy details or open modal
  }

  const handleVersionHistory = (policyId: string) => {
    setSelectedPolicyForComparison(policyId)
  }

  const filteredPolicies = policies.filter((policy) =>
    policy.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="p-6 space-y-6">
      <div>
        <h1 className="text-3xl font-bold mb-2">Policy Management</h1>
        <p className="text-gray-600">Upload and manage insurance policies</p>
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Upload New Policy</h2>
        <PolicyUpload onUpload={handleUpload} isUploading={uploadMutation.isPending} />
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">Existing Policies</h2>
        <PolicySearch
          value={searchQuery}
          onChange={setSearchQuery}
          onFilter={setStatusFilter}
          currentFilter={statusFilter}
        />
        <div className="mt-6">
          {filteredPolicies.length > 0 ? (
            <PolicyList
              policies={filteredPolicies}
              onPolicyClick={handlePolicyClick}
              onVersionHistory={handleVersionHistory}
            />
          ) : (
            <div className="text-center py-12 text-gray-500">
              No policies found
            </div>
          )}
        </div>
      </div>

      {/* Version Comparison Modal */}
      {selectedPolicyForComparison && (
        <VersionComparison
          policyId={selectedPolicyForComparison}
          onClose={() => setSelectedPolicyForComparison(null)}
        />
      )}
    </div>
  )
}

