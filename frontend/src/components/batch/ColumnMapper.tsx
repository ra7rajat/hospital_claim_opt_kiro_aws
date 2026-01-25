import { useState, useEffect } from 'react'
import { CheckCircle, AlertCircle, Save, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ColumnMapperProps {
  file: File
  onMappingComplete: (mapping: Record<string, string>) => void
  onCancel: () => void
}

interface RequiredField {
  key: string
  label: string
  required: boolean
  description: string
}

const REQUIRED_FIELDS: RequiredField[] = [
  {
    key: 'patientId',
    label: 'Patient ID',
    required: true,
    description: 'Unique identifier for the patient'
  },
  {
    key: 'patientName',
    label: 'Patient Name',
    required: true,
    description: 'Full name of the patient'
  },
  {
    key: 'dateOfBirth',
    label: 'Date of Birth',
    required: true,
    description: 'Patient date of birth (YYYY-MM-DD or MM/DD/YYYY)'
  },
  {
    key: 'policyNumber',
    label: 'Policy Number',
    required: true,
    description: 'Insurance policy number'
  },
  {
    key: 'procedureCode',
    label: 'Procedure Code',
    required: true,
    description: 'CPT or procedure code'
  }
]

// Common column name variations for auto-detection
const COLUMN_VARIATIONS: Record<string, string[]> = {
  patientId: ['patient_id', 'patient id', 'id', 'patient number', 'mrn', 'patientid'],
  patientName: ['patient_name', 'patient name', 'name', 'full name', 'patient', 'patientname'],
  dateOfBirth: ['date_of_birth', 'date of birth', 'dob', 'birth date', 'birthdate', 'dateofbirth'],
  policyNumber: ['policy_number', 'policy number', 'policy', 'insurance number', 'policy id', 'policynumber'],
  procedureCode: ['procedure_code', 'procedure code', 'procedure', 'cpt code', 'cpt', 'procedurecode']
}

export default function ColumnMapper({
  file,
  onMappingComplete,
  onCancel
}: ColumnMapperProps) {
  const [csvColumns, setCsvColumns] = useState<string[]>([])
  const [mapping, setMapping] = useState<Record<string, string>>({})
  const [savedMappings, setSavedMappings] = useState<Record<string, Record<string, string>>>({})
  const [previewData, setPreviewData] = useState<string[][]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    parseCSVHeaders()
    loadSavedMappings()
  }, [file])

  const parseCSVHeaders = async () => {
    try {
      setLoading(true)
      const text = await file.text()
      const lines = text.split('\n').filter(line => line.trim())
      
      if (lines.length === 0) {
        setError('CSV file is empty')
        return
      }

      // Parse headers
      const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''))
      setCsvColumns(headers)

      // Parse preview data (first 3 rows)
      const preview = lines.slice(1, 4).map(line => 
        line.split(',').map(cell => cell.trim().replace(/^"|"$/g, ''))
      )
      setPreviewData(preview)

      // Auto-detect column mapping
      const autoMapping = autoDetectMapping(headers)
      setMapping(autoMapping)

      setLoading(false)
    } catch (err) {
      setError('Failed to parse CSV file')
      setLoading(false)
    }
  }

  const autoDetectMapping = (headers: string[]): Record<string, string> => {
    const detected: Record<string, string> = {}

    for (const field of REQUIRED_FIELDS) {
      const variations = COLUMN_VARIATIONS[field.key] || []
      
      // Check for exact match first
      if (headers.includes(field.key)) {
        detected[field.key] = field.key
        continue
      }

      // Check for variations (case-insensitive)
      for (const header of headers) {
        if (variations.includes(header.toLowerCase())) {
          detected[field.key] = header
          break
        }
      }
    }

    return detected
  }

  const loadSavedMappings = () => {
    try {
      const saved = localStorage.getItem('csvColumnMappings')
      if (saved) {
        setSavedMappings(JSON.parse(saved))
      }
    } catch (err) {
      console.error('Failed to load saved mappings:', err)
    }
  }

  const saveMappingConfig = () => {
    try {
      const mappingName = prompt('Enter a name for this mapping configuration:')
      if (!mappingName) return

      const updated = {
        ...savedMappings,
        [mappingName]: mapping
      }
      setSavedMappings(updated)
      localStorage.setItem('csvColumnMappings', JSON.stringify(updated))
      alert('Mapping configuration saved!')
    } catch (err) {
      alert('Failed to save mapping configuration')
    }
  }

  const loadMappingConfig = (name: string) => {
    const config = savedMappings[name]
    if (config) {
      setMapping(config)
    }
  }

  const handleMappingChange = (fieldKey: string, csvColumn: string) => {
    setMapping(prev => ({
      ...prev,
      [fieldKey]: csvColumn
    }))
  }

  const isValid = (): boolean => {
    // Check all required fields are mapped
    for (const field of REQUIRED_FIELDS) {
      if (field.required && !mapping[field.key]) {
        return false
      }
    }

    // Check mapped columns exist in CSV
    for (const csvColumn of Object.values(mapping)) {
      if (csvColumn && !csvColumns.includes(csvColumn)) {
        return false
      }
    }

    return true
  }

  const handleSubmit = () => {
    if (isValid()) {
      onMappingComplete(mapping)
    }
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">{error}</p>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Instructions */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p className="text-sm text-blue-900">
          Map your CSV columns to the required fields. We've auto-detected some mappings for you.
          Fields marked with <span className="text-red-600">*</span> are required.
        </p>
      </div>

      {/* Saved Mappings */}
      {Object.keys(savedMappings).length > 0 && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Load Saved Mapping
          </label>
          <select
            onChange={(e) => e.target.value && loadMappingConfig(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
          >
            <option value="">Select a saved mapping...</option>
            {Object.keys(savedMappings).map(name => (
              <option key={name} value={name}>{name}</option>
            ))}
          </select>
        </div>
      )}

      {/* Column Mapping */}
      <div className="space-y-4">
        {REQUIRED_FIELDS.map(field => {
          const isMapped = !!mapping[field.key]
          const isValidMapping = isMapped && csvColumns.includes(mapping[field.key])

          return (
            <div key={field.key} className="border border-gray-200 rounded-lg p-4">
              <div className="flex items-start justify-between mb-2">
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    <label className="font-medium text-gray-900">
                      {field.label}
                      {field.required && <span className="text-red-600 ml-1">*</span>}
                    </label>
                    {isValidMapping && (
                      <CheckCircle className="h-4 w-4 text-green-600" />
                    )}
                    {field.required && !isValidMapping && (
                      <AlertCircle className="h-4 w-4 text-yellow-600" />
                    )}
                  </div>
                  <p className="text-sm text-gray-500 mt-1">{field.description}</p>
                </div>
              </div>

              <select
                value={mapping[field.key] || ''}
                onChange={(e) => handleMappingChange(field.key, e.target.value)}
                className={cn(
                  'w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent',
                  isValidMapping
                    ? 'border-green-300 bg-green-50'
                    : field.required && !isMapped
                    ? 'border-yellow-300 bg-yellow-50'
                    : 'border-gray-300'
                )}
              >
                <option value="">Select CSV column...</option>
                {csvColumns.map(col => (
                  <option key={col} value={col}>{col}</option>
                ))}
              </select>

              {/* Preview Data */}
              {mapping[field.key] && previewData.length > 0 && (
                <div className="mt-2 p-2 bg-gray-50 rounded text-sm">
                  <p className="text-gray-600 mb-1">Preview:</p>
                  <div className="space-y-1">
                    {previewData.map((row, idx) => {
                      const colIndex = csvColumns.indexOf(mapping[field.key])
                      return (
                        <p key={idx} className="text-gray-800 font-mono text-xs">
                          {row[colIndex] || '(empty)'}
                        </p>
                      )
                    })}
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>

      {/* Validation Message */}
      {!isValid() && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-start space-x-2">
            <AlertCircle className="h-5 w-5 text-yellow-600 mt-0.5" />
            <div>
              <p className="font-medium text-yellow-900">Incomplete Mapping</p>
              <p className="text-sm text-yellow-700 mt-1">
                Please map all required fields before continuing.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center justify-between pt-4 border-t">
        <button
          onClick={saveMappingConfig}
          disabled={!isValid()}
          className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <Save className="h-4 w-4" />
          <span>Save Mapping</span>
        </button>

        <div className="flex items-center space-x-3">
          <button
            onClick={onCancel}
            className="flex items-center space-x-2 px-4 py-2 text-sm text-gray-700 bg-gray-100 rounded-lg hover:bg-gray-200"
          >
            <X className="h-4 w-4" />
            <span>Cancel</span>
          </button>
          <button
            onClick={handleSubmit}
            disabled={!isValid()}
            className="flex items-center space-x-2 px-6 py-2 text-sm bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <CheckCircle className="h-4 w-4" />
            <span>Continue</span>
          </button>
        </div>
      </div>
    </div>
  )
}
