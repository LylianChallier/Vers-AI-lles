import { motion } from 'framer-motion'
import { MessageCircle, Trash2 } from 'lucide-react'
import { Card, SectionTitle, Pill } from './common'

export function ChatPanel({
  copy,
  messages,
  isLoading,
  input,
  onInputChange,
  onSubmit,
  onClear,
  suggestions,
  onSuggestion,
  feedRef,
}) {
  return (
    <Card className="chat-card">
      <div className="chat-card__header">
        <SectionTitle icon={MessageCircle} title={copy.title} />
        <div className="chat-card__meta">
          <div className="chat-card__status">
            <span className="chat-card__status-dot" />
            {copy.status}
          </div>
          <Pill icon={Trash2} onClick={onClear}>
            {copy.clear}
          </Pill>
        </div>
      </div>

      <div className="chat-feed" ref={feedRef}>
        {messages.map((message, index) => (
          <motion.div
            key={`${message.role}-${index}`}
            className={['chat-bubble', message.role, message.isError ? 'is-error' : ''].filter(Boolean).join(' ')}
            initial={{ y: 6, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: index * 0.04 }}
          >
            <p>{message.text}</p>
          </motion.div>
        ))}
        {isLoading ? (
          <div className="chat-bubble assistant pending" aria-live="polite">
            <p>{copy.assistantLoading}</p>
          </div>
        ) : null}
      </div>

      <form className="chat-input" onSubmit={onSubmit}>
        <div className="chat-input__field">
          <textarea
            rows={2}
            value={input}
            onChange={(event) => onInputChange(event.target.value)}
            placeholder={copy.placeholder}
            disabled={isLoading}
          />
          <div className="chat-input__chips">
            {suggestions.slice(0, 3).map((item) => (
              <button
                key={item.key}
                type="button"
                onClick={() => onSuggestion(item.label)}
                disabled={isLoading}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
        <button type="submit" className="chat-input__send" disabled={isLoading || !input.trim()}>
          {isLoading ? copy.sendLoading : copy.sendIdle}
        </button>
      </form>
    </Card>
  )
}
