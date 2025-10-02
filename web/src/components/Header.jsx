import { motion } from 'framer-motion'
import { Crown } from 'lucide-react'
import { LangToggle } from './LangToggle'

export function Header({ copy, lang, onLangChange }) {
  return (
    <header className="app-header container">
      <div className="app-header__top">
        <div className="brand">
          <motion.div
            className="brand__symbol"
            initial={{ scale: 0.9, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ type: 'spring', stiffness: 120 }}
          >
            <Crown size={24} />
          </motion.div>
          <div>
            <h1>{copy.title}</h1>
            <p>{copy.subtitle}</p>
          </div>
        </div>

        <div className="app-header__toggles">
          <LangToggle value={lang} onChange={onLangChange} />
        </div>
      </div>
    </header>
  )
}
