import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { Search, CheckCircle, XCircle, AlertCircle, FileText, Loader2, Users, User } from 'lucide-react'
import { apiClient } from '@/lib/api'
import { cn } from '@/lib/utils'
import CSVUploader from '@/components/batch/CSVUploader'
import ColumnMapper from '@/components/batch/ColumnMapper'
import BatchProgress from '@/components/batch/BatchProgress'
import BatchResults from '@/components/batch/BatchResults'

interface EligibilityRequest {
  patientId: string
  procedureCodes: string[]
  diagnosisCodes: string[]
}

interface EligibilityResponse {
  coverageStatus: 'covered' | 'not_covered' | 'partial'
  coveragePercentage: number
  patientResponsibility: number
  policyReferences: string[]
  preAuthRequired: boolean
  documentationTemplate?: string
  details: string
}

export default function EligibilityCheck() {
  const [mode, setMode] = useState<'single' | 'batch'>('single')
  const [patientId, setPatientId] = useState('')
  const [procedureCode, setProcedureCode] = useState('')
  const [diagnosisCode, setDiagnosisCode] = useState('')
  
  // Batch mode state
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [columnMapping, setColumnMapping] = useState<Record<string, string> | null>(null)
  const [batchId, setBatchId] = useState<string | null>(null)
  const [showResults, setShowResults] = useState(false)

  const eligibilityMutation = useMutation({
    mutationFn: async (request: EligibilityRequest) => {
      return apiClient.post<EligibilityResponse>('/eligibility/check', request)
    },
  })

  const createBatchMutation = useMutation({
    mutationFn: async (file: File) => {
      const response = await apiClient.post<{
        batchId: string
        uploadUrl: string
      }>('/eligibility/batch/create', {
        hospitalId: 'HOSP001', // TODO: Get from user context
        fileName: file.name
      })
      return { ...response, file }
    },
  })

  const processBatchMutation = useMutation({
    mutationFn: async (params: { batchId: string; columnMapping: Record<string, string> }) => {
      return apiClient.post('/eligibility/batch/process', params)
    },
  })

  const handleCheck = () => {
    if (patientId && procedureCode) {
      eligibilityMutation.mutate({
        patientId,
        procedureCodes: [procedureCode],
        diagnosisCodes: diagnosisCode ? [diagnosisCode] : [],
      })
    }
  }

  const handleFileSelect = async (file: File) => {
    setSelectedFile(file)
    setColumnMapping(null)
    setBatchId(null)
    setShowResults(false)
  }

  const handleFileClear = () => {
    setSelectedFile(null)
    setColumnMapping(null)
    setBatchId(null)
    setShowResults(false)
  }

  const handleColumnMappingComplete = async (mapping: Record<string, string>) => {
    if (!selectedFile) return
    
    setColumnMapping(mapping)
    
    // Create batch job and upload file
    try {
      const { batchId, uploadUrl, file } = await createBatchMutation.mutateAsync(selectedFile)
      
      // Upload file to S3
      await fetch(uploadUrl, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': 'text/csv'
        }
      })
      
      // Start processing
      await processBatchMutation.mutateAsync({ batchId, columnMapping: mapping })
      
      setBatchId(batchId)
    } catch (error) {
      console.error('Error processing batch:', error)
    }
  }

  const handleBatchComplete = () => {
    setShowResults(true)
  }

  const handleNewBatch = () => {
    setSelectedFile(null)
    setColumnMapping(null)
    setBatchId(null)
    setShowResults(false)
  }

  const result = eligibilityMutation.data

  const getCoverageIcon = (status: string) => {
    switch (status) {
      case 'covered':
        return <CheckCircle className="h-8 w-8 text-green-500" />
      case 'not_covered':
        return <XCircle className="h-8 w-8 text-red-500" />
      case 'partial':
        return <AlertCircle className="h-8 w-8 text-yellow-500" />
      default:
        return null
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-4 md:p-6">
      <div className="max-w-4xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl md:text-3xl font-bold mb-2">Treatment Eligibility Check</h1>
          <p className="text-gray-600">Check if procedures are covered by patient insurance</p>
        </div>

        {/* Mode Toggle */}
        <div className="bg-white rounded-lg shadow p-4">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => setMode('single')}
              className={cn(
                'flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors',
                mode === 'single'
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              )}
            >
              <User className="h-5 w-5" />
              <span>Single Check</span>
            </button>
            <button
              onClick={() => setMode('batch')}
              className={cn(
                'flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors',
                mode === 'batch'
                  ? 'bg-primary text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              )}
            >
              <Users className="h-5 w-5" />
              <span>Batch Check</span>
            </button>
          </div>
        </div>

        {/* Single Mode */}
        {mode === 'single' && (
          <>
            <div className="bg-white rounded-lg shadow p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Patient ID *
                </label>
                <input
                  type="text"
                  value={patientId}
                  onChange={(e) => setPatientId(e.target.value)}
                  placeholder="Enter patient ID"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent text-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Procedure Code *
                </label>
                <input
                  type="text"
                  value={procedureCode}
                  onChange={(e) => setProcedureCode(e.target.value)}
                  placeholder="e.g., 99213"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent text-lg"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Diagnosis Code (Optional)
                </label>
                <input
                  type="text"
                  value={diagnosisCode}
                  onChange={(e) => setDiagnosisCode(e.target.value)}
                  placeholder="e.g., J20.9"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent text-lg"
                />
              </div>

              <button
                onClick={handleCheck}
                disabled={!patientId || !procedureCode || eligibilityMutation.isPending}
                className="w-full py-3 bg-primary text-white rounded-lg font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center space-x-2"
              >
                {eligibilityMutation.isPending ? (
                  <>
                    <Loader2 className="h-5 w-5 animate-spin" />
                    <span>Checking...</span>
                  </>
                ) : (
                  <>
                    <Search className="h-5 w-5" />
                    <span>Check Eligibility</span>
                  </>
                )}
              </button>
            </div>

            {result && (
              <div className="bg-white rounded-lg shadow p-6 space-y-6">
                <div className="flex items-center space-x-4">
                  {getCoverageIcon(result.coverageStatus)}
                  <div>
                    <h2 className="text-xl font-bold">
                      {result.coverageStatus === 'covered' && 'Covered'}
                      {result.coverageStatus === 'not_covered' && 'Not Covered'}
                      {result.coverageStatus === 'partial' && 'Partially Covered'}
                    </h2>
                    <p className="text-gray-600">{result.details}</p>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Coverage Percentage</p>
                    <p className="text-2xl font-bold text-primary">
                      {result.coveragePercentage}%
                    </p>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-600 mb-1">Patient Responsibility</p>
                    <p className="text-2xl font-bold text-gray-900">
                      ${result.patientResponsibility.toFixed(2)}
                    </p>
                  </div>
                </div>

                {result.preAuthRequired && (
                  <div className={cn(
                    'p-4 rounded-lg border-l-4',
                    'bg-yellow-50 border-yellow-500'
                  )}>
                    <div className="flex items-start space-x-3">
                      <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
                      <div>
                        <p className="font-medium text-yellow-900">Pre-authorization Required</p>
                        <p className="text-sm text-yellow-700 mt-1">
                          This procedure requires pre-authorization before treatment
                        </p>
                      </div>
                    </div>
                  </div>
                )}

                {result.policyReferences.length > 0 && (
                  <div>
                    <h3 className="font-medium text-gray-900 mb-2">Policy References</h3>
                    <ul className="space-y-1">
                      {result.policyReferences.map((ref, idx) => (
                        <li key={idx} className="text-sm text-gray-600 flex items-start">
                          <span className="mr-2">•</span>
                          <span>{ref}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {result.documentationTemplate && (
                  <button className="w-full py-3 border-2 border-primary text-primary rounded-lg font-medium hover:bg-primary hover:text-white transition-colors flex items-center justify-center space-x-2">
                    <FileText className="h-5 w-5" />
                    <span>Download Pre-authorization Template</span>
                  </button>
                )}
              </div>
            )}

            {eligibilityMutation.isError && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <p className="text-red-800">
                  Error checking eligibility. Please try again.
                </p>
              </div>
            )}
          </>
        )}

        {/* Batch Mode */}
        {mode === 'batch' && (
          <div className="space-y-6">
            {!selectedFile && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold mb-4">Upload CSV File</h2>
                <CSVUploader
                  onFileSelect={handleFileSelect}
                  onClear={handleFileClear}
                  selectedFile={selectedFile}
                />
              </div>
            )}

            {selectedFile && !columnMapping && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold mb-4">Map CSV Columns</h2>
                <ColumnMapper
                  file={selectedFile}
                  onMappingComplete={handleColumnMappingComplete}
                  onCancel={handleFileClear}
                />
              </div>
            )}

            {batchId && !showResults && (
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold mb-4">Processing Batch</h2>
                <BatchProgress
                  batchId={batchId}
                  onComplete={handleBatchComplete}
                />
              </div>
            )}

            {batchId && showResults && (
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold">Batch Results</h2>
                  <button
                    onClick={handleNewBatch}
                    className="px-4 py-2 text-sm bg-primary text-white rounded-lg hover:bg-primary/90"
                  >
                    New Batch
                  </button>
                </div>
                <BatchResults batchId={batchId} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

