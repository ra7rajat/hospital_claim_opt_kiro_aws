import { Search } from 'lucide-react'

interface PolicySearchProps {
  value: string
  onChange: (value: string) => void
  onFilter: (filter: 'all' | 'processing' | 'completed' | 'failed') => void
  currentFilter: string
}

export default function PolicySearch({ value, onChange, onFilter, currentFilter }: PolicySearchProps) {
  return (
    <div className="space-y-4">
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search policies..."
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent"
        />
      </div>
      <div className="flex space-x-2">
        {['all', 'processing', 'completed', 'failed'].map((filter) => (
          <button
            key={filter}
            onClick={() => onFilter(filter as any)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              currentFilter === filter
                ? 'bg-primary text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {filter.charAt(0).toUpperCase() + filter.slice(1)}
          </button>
        ))}
      </div>
    </div>
  )
}
