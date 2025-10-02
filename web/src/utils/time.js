export function parseHHMM(value) {
  const [hours, minutes] = value.split(':').map(Number)
  return hours * 60 + minutes
}

export function minutesToHHMM(minutes) {
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}`
}

export function inMinutes(value) {
  return parseHHMM(value)
}

export function crowdLevel(now = new Date()) {
  const minutes = now.getHours() * 60 + now.getMinutes()
  if (minutes < 9 * 60) return { key: 'low', value: 18 }
  if (minutes < 11 * 60) return { key: 'rising', value: 45 }
  if (minutes < 15 * 60) return { key: 'peak', value: 85 }
  if (minutes < 18 * 60) return { key: 'busy', value: 70 }
  return { key: 'low', value: 25 }
}
