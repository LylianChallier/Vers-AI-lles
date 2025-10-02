export function LangToggle({ value, onChange }) {
  const options = [
    { key: 'fr', label: 'FR' },
    { key: 'en', label: 'EN' },
  ]

  return (
    <div className="toggle-group">
      {options.map((option) => (
        <button
          type="button"
          key={option.key}
          className={`toggle-button toggle-button--compact ${value === option.key ? 'is-active' : ''}`.trim()}
          onClick={() => onChange(option.key)}
        >
          {option.label}
        </button>
      ))}
    </div>
  )
}
