import { ChevronDown } from 'lucide-react'

interface PolicyVersion {
  version: number
  createdAt: string
  createdBy: string
  description?: string
}

interface VersionSelectorProps {
  label: string
  versions: PolicyVersion[]
  selectedVersion: number | null
  onSelect: (version: number) => void
  excludeVersion?: number | null
}

export default function VersionSelector({
  label,
  versions,
  selectedVersion,
  onSelect,
  excludeVersion,
}: VersionSelectorProps) {
  const availableVersions = versions.filter((v) => v.version !== excludeVersion)
  const selectedVersionData = versions.find((v) => v.version === selectedVersion)

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-2">{label}</label>
      <div className="relative">
        <select
          value={selectedVersion || ''}
          onChange={(e) => onSelect(Number(e.target.value))}
          className="w-full px-4 py-3 border border-gray-300 rounded-lg appearance-none bg-white focus:outline-none focus:ring-2 focus:ring-primary focus:border-transparent"
        >
          <option value="">Select a version</option>
          {availableVersions.map((version) => (
            <option key={version.version} value={version.version}>
              Version {version.version} - {new Date(version.createdAt).toLocaleDateString()}
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400 pointer-events-none" />
      </div>
      {selectedVersionData && (
        <div className="mt-2 p-3 bg-gray-50 rounded-lg text-sm">
          <div className="flex items-center justify-between mb-1">
            <span className="font-medium text-gray-700">Version {selectedVersionData.version}</span>
            <span className="text-gray-500">
              {new Date(selectedVersionData.createdAt).toLocaleString()}
            </span>
          </div>
          <div className="text-gray-600">
            <span className="font-medium">Created by:</span> {selectedVersionData.createdBy}
          </div>
          {selectedVersionData.description && (
            <div className="mt-1 text-gray-600">
              <span className="font-medium">Description:</span> {selectedVersionData.description}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
