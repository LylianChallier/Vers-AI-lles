import { TRANSLATIONS } from '../constants/translations'

export function createInitialMessage(language) {
  const locale = TRANSLATIONS[language] ?? TRANSLATIONS.en
  return {
    role: 'assistant',
    text: locale.initialAssistant,
  }
}

export function getLocaleText(value, language) {
  if (value == null) return ''
  if (typeof value === 'string') return value
  if (typeof value === 'object') {
    if (value[language]) return value[language]
    if (value.en) return value.en
    if (value.fr) return value.fr
    const fallback = Object.values(value).find((entry) => typeof entry === 'string')
    return typeof fallback === 'string' ? fallback : ''
  }
  return String(value)
}
