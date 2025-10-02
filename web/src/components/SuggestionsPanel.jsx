import { Sparkles, Wand2 } from 'lucide-react'
import { Card, SectionTitle } from './common'

export function SuggestionsPanel({ title, suggestions, onSelect, disabled }) {
  return (
    <Card>
      <SectionTitle icon={Sparkles} title={title} />
      <div className="suggestions">
        {suggestions.map((item) => (
          <button
            key={item.key}
            type="button"
            className="suggestion"
            onClick={() => onSelect(item.label)}
            disabled={disabled}
          >
            <Wand2 size={16} />
            {item.label}
          </button>
        ))}
      </div>
    </Card>
  )
}
