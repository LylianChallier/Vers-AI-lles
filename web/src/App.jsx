import { useEffect, useMemo, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import {
  Accessibility,
  Baby,
  Clock,
  CloudRain,
  CloudSun,
  Compass,
  Crown,
  GraduationCap,
  Info,
  Languages,
  MapPin,
  MessageCircle,
  Sparkles,
  Sun,
  Ticket,
  Users,
  Wand2,
  Trash2,
} from 'lucide-react'
import './App.css'
import 'leaflet/dist/leaflet.css'
import { MapContainer, TileLayer, Marker, Polyline, LayersControl, Popup } from 'react-leaflet'
import L from 'leaflet'
import marker2x from 'leaflet/dist/images/marker-icon-2x.png'
import marker1x from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

const INITIAL_ASSISTANT_MESSAGE = {
  role: 'assistant',
  text:
    'Bienvenue! I’m your Versailles Concierge. Share your timing, preferences, or constraints and I’ll craft a tailored plan for your visit.',
}

const STORAGE_KEYS = {
  session: 'versailles-concierge-session',
  messages: 'versailles-concierge-messages',
  persona: 'versailles-concierge-persona',
  lang: 'versailles-concierge-lang',
}

function getStoredJSON(key, fallback) {
  if (typeof window === 'undefined') return fallback
  try {
    const raw = window.localStorage.getItem(key)
    if (!raw) return fallback
    const parsed = JSON.parse(raw)
    return parsed === null ? fallback : parsed
  } catch (error) {
    return fallback
  }
}

function getStoredValue(key, fallback) {
  if (typeof window === 'undefined') return fallback
  try {
    const raw = window.localStorage.getItem(key)
    return raw === null ? fallback : raw
  } catch (error) {
    return fallback
  }
}

function createSessionId() {
  if (typeof window === 'undefined') return `session-${Date.now()}`
  return window.crypto?.randomUUID?.() || `session-${Date.now()}`
}

const API_BASE_URL =
  typeof window !== 'undefined'
    ? import.meta.env.VITE_API_BASE_URL?.trim() ||
      (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'
        ? 'http://localhost:8002'
        : `${window.location.origin.replace(/\/$/, '')}`)
    : ''

// Live weather will be fetched from the backend. Keep a minimal fallback.
const MOCK_WEATHER = {
  condition: 'partly-cloudy',
  tempC: 22,
  advice:
    'Sunny morning → start with the Gardens; Hall of Mirrors after 14:30 when tours thin out.',
}

const HOURS = {
  chateau: { open: '09:00', close: '18:30', last: '17:45' },
  trianon: { open: '12:00', close: '18:30', last: '17:45' },
}

const QUICK_CHIPS = [
  'Avoid queues',
  'Best time for Hall of Mirrors',
  'Family-friendly route',
  'Need wheelchair tips',
  'Where to eat?',
  'Half-day itinerary',
]

const PERSONA_HINTS = {
  classic: 'Persona: adult visitors seeking a balanced art-and-garden itinerary.',
  kid: 'Persona: family with children — keep it playful and outdoor friendly.',
  scholar: 'Persona: curious visitors looking for historical depth and cultural insights.',
}

const LANG_HINTS = {
  fr: 'Réponds en français clair et chaleureux.',
  en: 'Respond in English with concise sentences.',
}

function parseHHMM(value) {
  const [hours, minutes] = value.split(':').map(Number)
  return hours * 60 + minutes
}

function minutesToHHMM(minutes) {
  const hours = Math.floor(minutes / 60)
  const mins = minutes % 60
  return `${String(hours).padStart(2, '0')}:${String(mins).padStart(2, '0')}`
}

function inMinutes(value) {
  return parseHHMM(value)
}

function crowdLevel(now = new Date()) {
  const minutes = now.getHours() * 60 + now.getMinutes()
  if (minutes < 9 * 60) return { label: 'Low', value: 18 }
  if (minutes < 11 * 60) return { label: 'Rising', value: 45 }
  if (minutes < 15 * 60) return { label: 'Peak', value: 85 }
  if (minutes < 18 * 60) return { label: 'Busy', value: 70 }
  return { label: 'Low', value: 25 }
}

function Pill({ children, icon: Icon, onClick, type = 'button', disabled }) {
  return (
    <button type={type} className="pill" onClick={onClick} disabled={disabled}>
      {Icon ? <Icon size={16} /> : null}
      <span>{children}</span>
    </button>
  )
}

function Card({ children, className = '' }) {
  return <div className={['card', className].filter(Boolean).join(' ')}>{children}</div>
}

function SectionTitle({ icon: Icon, title, right }) {
  return (
    <div className="section-title">
      <div className="section-title__main">
        {Icon ? <Icon size={18} className="section-title__icon" /> : null}
        <h3>{title}</h3>
      </div>
      {right ? <div className="section-title__right">{right}</div> : null}
    </div>
  )
}

function Progress({ value }) {
  const safeValue = Math.min(100, Math.max(0, value))
  return (
    <div className="progress">
      <div className="progress__fill" style={{ width: `${safeValue}%` }} />
    </div>
  )
}

function Chip({ children }) {
  return <span className="chip">{children}</span>
}

function WeatherGlyph({ condition }) {
  if (condition === 'rain') return <CloudRain className="weather-icon" size={20} />
  if (condition === 'sunny') return <Sun className="weather-icon" size={20} />
  return <CloudSun className="weather-icon" size={20} />
}

function toLeafletCoords(geometry) {
  if (!geometry || typeof geometry !== 'object') return []
  if (geometry.type === 'LineString' && Array.isArray(geometry.coordinates)) {
    return [geometry.coordinates.map(([lon, lat]) => [lat, lon])]
  }
  if (geometry.type === 'MultiLineString' && Array.isArray(geometry.coordinates)) {
    return geometry.coordinates.map((segment) =>
      Array.isArray(segment) ? segment.map(([lon, lat]) => [lat, lon]) : []
    )
  }
  return []
}

// Fix des icônes Leaflet avec Vite
L.Icon.Default.mergeOptions({
  iconRetinaUrl: marker2x,
  iconUrl: marker1x,
  shadowUrl: markerShadow,
})

function RouteMap({ coords = [], markers = [] }) {
  const mapNodeRef = useRef(null)
  const mapRef = useRef(null)
  const markerRefs = useRef([])
  const polylineRef = useRef(null)

  useEffect(() => {
    if (!mapRef.current && mapNodeRef.current) {
      mapRef.current = L.map(mapNodeRef.current, {
        center: [48.8049, 2.1204],
        zoom: 14,
        zoomControl: false,
      })
      L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19,
      }).addTo(mapRef.current)
    }

    return () => {
      if (mapRef.current) {
        mapRef.current.remove()
        mapRef.current = null
      }
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return

    // Reset existing markers
    markerRefs.current.forEach((marker) => {
      if (marker) map.removeLayer(marker)
    })
    markerRefs.current = []

    markers.forEach((m) => {
      if (!m || typeof m.lat !== 'number' || typeof m.lon !== 'number') return
      const marker = L.marker([m.lat, m.lon]).addTo(map)
      markerRefs.current.push(marker)
    })

    if (polylineRef.current) {
      map.removeLayer(polylineRef.current)
      polylineRef.current = null
    }

    if (Array.isArray(coords) && coords.length > 1) {
      polylineRef.current = L.polyline(coords, { color: '#f1c45b', weight: 5, opacity: 0.9 }).addTo(map)
    }

    const boundsPoints = []
    markerRefs.current.forEach((marker) => boundsPoints.push(marker.getLatLng()))
    if (Array.isArray(coords)) {
      coords.forEach((pt) => {
        if (Array.isArray(pt) && pt.length === 2) boundsPoints.push(L.latLng(pt[0], pt[1]))
      })
    }

    if (boundsPoints.length) {
      const bounds = L.latLngBounds(boundsPoints)
      map.fitBounds(bounds.pad(0.2), { animate: false })
    } else {
      map.setView([48.8049, 2.1204], 14)
    }
  }, [coords, markers])

  return <div ref={mapNodeRef} className="leaflet-map" />
}

function PersonaToggle({ value, onChange }) {
  const options = [
    { key: 'classic', label: 'Classic', icon: Crown },
    { key: 'kid', label: 'Kids', icon: Baby },
    { key: 'scholar', label: 'Scholar', icon: GraduationCap },
  ]

  return (
    <div className="toggle-group">
      {options.map((option) => (
        <button
          type="button"
          key={option.key}
          className={`toggle-button ${value === option.key ? 'is-active' : ''}`.trim()}
          onClick={() => onChange(option.key)}
        >
          <option.icon size={16} />
          <span>{option.label}</span>
        </button>
      ))}
    </div>
  )
}

function LangToggle({ value, onChange }) {
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

function VersaillesConcierge() {
  function normalizeReply(raw) {
    if (!raw || typeof raw !== 'string') return 'Je suis désolé·e, je ne peux pas répondre pour le moment.'
    let s = raw.trim()
    if (/^json\b/i.test(s)) {
      const braceIndex = s.indexOf('{')
      s = braceIndex >= 0 ? s.slice(braceIndex) : s
    }
    s = s.replace(/^```json\s*/i, '').replace(/```$/i, '').trim()
    try {
      const obj = JSON.parse(s)
      if (obj && typeof obj.response === 'string') {
        return obj.response.trim() || 'Je suis désolé·e, je ne peux pas répondre pour le moment.'
      }
    } catch (_) {}
    return s || 'Je suis désolé·e, je ne peux pas répondre pour le moment.'
  }
  const [persona, setPersona] = useState(() => getStoredValue(STORAGE_KEYS.persona, 'classic'))
  const [lang, setLang] = useState(() => getStoredValue(STORAGE_KEYS.lang, 'en'))
  const [input, setInput] = useState('')
  const [messages, setMessages] = useState(() => {
    const stored = getStoredJSON(STORAGE_KEYS.messages, null)
    if (Array.isArray(stored) && stored.length) {
      return stored
    }
    return [INITIAL_ASSISTANT_MESSAGE]
  })
  const [plan, setPlan] = useState(null)
  const [showMap, setShowMap] = useState(false)
  const [userLocation, setUserLocation] = useState(null)
  const [locationError, setLocationError] = useState('')
  const [locationLoading, setLocationLoading] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState(() => getStoredValue(STORAGE_KEYS.session, createSessionId()))

  const crowd = useMemo(() => crowdLevel(new Date()), [])
  const chatFeedRef = useRef(null)
  const abortControllerRef = useRef(null)
  const weatherAbortRef = useRef(null)

  const [weather, setWeather] = useState({ ...MOCK_WEATHER })
  const [weatherLoading, setWeatherLoading] = useState(false)
  const [weatherError, setWeatherError] = useState('')

  // ---- Map / routing state ----
  const [mapOpen, setMapOpen] = useState(false)
  const [profile, setProfile] = useState('walking')
  const [origin, setOrigin] = useState('Versailles Château Rive Gauche')
  const [destination, setDestination] = useState('Château de Versailles, France')
  const [routeCoords, setRouteCoords] = useState([]) // [[lat, lon], ...]
  const [routeSegments, setRouteSegments] = useState([]) // Array of [[lat, lon], ...]
  const [routeLoading, setRouteLoading] = useState(false)
  const [routeError, setRouteError] = useState('')
  const [routeSteps, setRouteSteps] = useState([])
  const [markerA, setMarkerA] = useState(null)
  const [markerB, setMarkerB] = useState(null)

  const nowMins = new Date().getHours() * 60 + new Date().getMinutes()
  const lastEntry = inMinutes(HOURS.chateau.last)
  const minsLeft = Math.max(0, lastEntry - nowMins)
  const planTimeline = Array.isArray(plan?.timeline) ? plan.timeline : []
  const planWaypoints = Array.isArray(plan?.waypoints) ? plan.waypoints : []
  const planSegments = useMemo(() => toLeafletCoords(plan?.geometry), [plan?.geometry])
  const hasMapData = planWaypoints.length > 0 || planSegments.some((segment) => segment.length > 0) || !!userLocation
  const mapCenterLat = planWaypoints[0]?.lat ?? userLocation?.lat ?? 48.8049
  const mapCenterLon = planWaypoints[0]?.lon ?? userLocation?.lon ?? 2.1204
  const locationButtonLabel = locationLoading
    ? lang === 'fr'
      ? 'Localisation…'
      : 'Locating…'
    : userLocation
    ? lang === 'fr'
      ? 'Actualiser ma position'
      : 'Update my location'
    : lang === 'fr'
    ? 'Utiliser ma position'
    : 'Use my location'
  const locationInfoText = userLocation
    ? lang === 'fr'
      ? `Position partagée (${userLocation.lat}, ${userLocation.lon}${
          userLocation.accuracy ? ` ±${userLocation.accuracy} m` : ''
        }).`
      : `Location shared (${userLocation.lat}, ${userLocation.lon}${
          userLocation.accuracy ? ` ±${userLocation.accuracy} m` : ''
        }).`
    : locationError ||
      (lang === 'fr'
        ? 'Autorisez la localisation pour adapter l’itinéraire et les trajets.'
        : 'Allow location so the concierge can tailor routes and timing tips.')
  const locationInfoHasError = Boolean(locationError)
  const locationInfoClass = locationInfoHasError ? 'location-share__info location-share__info--error' : 'location-share__info'

  useEffect(() => {
    if (!chatFeedRef.current) return
    chatFeedRef.current.scrollTo({ top: chatFeedRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, isLoading])

  // ---- Weather fetching ----
  function hhmm(n) {
    return String(n).padStart(2, '0')
  }

  function localDateStr(d = new Date()) {
    const y = d.getFullYear()
    const m = hhmm(d.getMonth() + 1)
    const day = hhmm(d.getDate())
    return `${y}-${m}-${day}`
  }

  function localTimeStr(d = new Date()) {
    return `${hhmm(d.getHours())}:${hhmm(d.getMinutes())}`
  }

  async function fetchWeather() {
    setWeatherLoading(true)
    setWeatherError('')

    // Abort any previous in-flight request
    try { weatherAbortRef.current?.abort() } catch {}
    const controller = new AbortController()
    weatherAbortRef.current = controller

    const payload = {
      date: localDateStr(),
      start_time: localTimeStr(),
      duration_min: 180,
      place: 'Château de Versailles, France',
      lang,
    }

    try {
      const res = await fetch(`${API_BASE_URL}/tools/weather`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: controller.signal,
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()

      const label = data?.summary?.label || 'pleasant'
      const advice = data?.summary?.advice || (lang === 'fr' ? 'Conditions favorables.' : 'See indoor/heat precautions based on forecast.')
      const nextHour = Array.isArray(data?.hourly) && data.hourly.length > 0 ? data.hourly[0] : null
      const tempC = nextHour?.temp_c ?? null

      const condition = ({
        heavy_rain: 'rain',
        rain_risk: 'rain',
        mixed: 'partly-cloudy',
        heat: 'sunny',
        windy: 'partly-cloudy',
        pleasant: 'sunny',
      })[label] || 'partly-cloudy'

      setWeather({ condition, tempC: tempC ?? 0, advice })
    } catch (err) {
      setWeatherError(err?.message || 'Weather fetch failed')
    } finally {
      setWeatherLoading(false)
    }
  }

  useEffect(() => {
    fetchWeather()
    // Refresh on language change to get localized advice
  }, [lang])

  useEffect(() => {
    if (typeof window === 'undefined') return
    try {
      window.localStorage.setItem(STORAGE_KEYS.messages, JSON.stringify(messages))
    } catch (error) {}
  }, [messages])

  useEffect(() => {
    if (typeof window === 'undefined') return
    try {
      window.localStorage.setItem(STORAGE_KEYS.session, sessionId)
    } catch (error) {}
  }, [sessionId])

  useEffect(() => {
    if (typeof window === 'undefined') return
    try {
      window.localStorage.setItem(STORAGE_KEYS.persona, persona)
    } catch (error) {}
  }, [persona])

  useEffect(() => {
    if (typeof window === 'undefined') return
    try {
      window.localStorage.setItem(STORAGE_KEYS.lang, lang)
    } catch (error) {}
  }, [lang])

  useEffect(() => {
    if (!userLocation) return
    const formatted = `${userLocation.lat}, ${userLocation.lon}`
    setOrigin(formatted)
  }, [userLocation])

  // ---- Routing helpers ----
  function lineStringToLatLngs(geometry) {
    try {
      if (!geometry || geometry.type !== 'LineString' || !Array.isArray(geometry.coordinates)) return []
      return geometry.coordinates.map((c) => [c[1], c[0]]) // [lon, lat] -> [lat, lon]
    } catch {
      return []
    }
  }

  function geometryToSegments(geometry) {
    try {
      if (!geometry || typeof geometry !== 'object') return []
      if (geometry.type === 'LineString') {
        return [lineStringToLatLngs(geometry)]
      }
      if (geometry.type === 'MultiLineString' && Array.isArray(geometry.coordinates)) {
        return geometry.coordinates.map((coords) => (Array.isArray(coords) ? coords.map((c) => [c[1], c[0]]) : []))
      }
      return []
    } catch {
      return []
    }
  }

  async function fetchVersaillesRoute() {
    setRouteLoading(true)
    setRouteError('')
    setRouteSteps([])
    try {
      const res = await fetch(`${API_BASE_URL}/tools/versailles_route`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ origin, profile }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setMarkerA({ lat: data?.origin?.lat, lon: data?.origin?.lon })
      setMarkerB({ lat: data?.destination?.lat, lon: data?.destination?.lon })
      const segs = geometryToSegments(data?.geometry)
      setRouteSegments(segs)
      setRouteCoords(segs.length ? segs.flat() : [])
      setRouteSteps(Array.isArray(data?.steps) ? data.steps : [])
    } catch (e) {
      setRouteError(e?.message || 'Route failed')
    } finally {
      setRouteLoading(false)
      setMapOpen(true)
    }
  }

  async function fetchRouteBetween() {
    if (!origin.trim() || !destination.trim()) return
    setRouteLoading(true)
    setRouteError('')
    setRouteSteps([])
    try {
      const res = await fetch(`${API_BASE_URL}/tools/route`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ origin, destination, profile }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      setMarkerA({ lat: data?.origin?.lat, lon: data?.origin?.lon })
      setMarkerB({ lat: data?.destination?.lat, lon: data?.destination?.lon })
      const segs = geometryToSegments(data?.geometry)
      setRouteSegments(segs)
      setRouteCoords(segs.length ? segs.flat() : [])
      setRouteSteps(Array.isArray(data?.steps) ? data.steps : [])
    } catch (e) {
      setRouteError(e?.message || 'Route failed')
    } finally {
      setRouteLoading(false)
      setMapOpen(true)
    }
  }

  async function fetchRouteMultiDemo() {
    setRouteLoading(true)
    setRouteError('')
    setRouteSteps([])
    try {
      const places = [
        origin || 'Versailles Château Rive Gauche',
        'Château de Versailles, France',
        'Jardins du Château de Versailles',
        'Grand Trianon, Versailles',
        'Petit Trianon, Versailles',
        'Hameau de la Reine, Versailles',
      ]
      const res = await fetch(`${API_BASE_URL}/tools/route_multi`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ places, profile }),
      })
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const data = await res.json()
      const segs = geometryToSegments(data?.geometry)
      setRouteSegments(segs)
      setRouteCoords(segs.length ? segs.flat() : [])
      const wps = Array.isArray(data?.waypoints) ? data.waypoints : []
      setMarkerA(wps[0] ? { lat: wps[0].lat, lon: wps[0].lon } : null)
      setMarkerB(wps[wps.length - 1] ? { lat: wps[wps.length - 1].lat, lon: wps[wps.length - 1].lon } : null)
      const flatSteps = []
      if (Array.isArray(data?.segments)) {
        for (const seg of data.segments) {
          if (Array.isArray(seg?.steps)) flatSteps.push(...seg.steps)
        }
      }
      setRouteSteps(flatSteps)
      setMapOpen(true)
    } catch (e) {
      setRouteError(e?.message || 'Route failed')
    } finally {
      setRouteLoading(false)
    }
  }

  const requestUserLocation = () => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      setLocationError(
        lang === 'fr'
          ? "La géolocalisation n'est pas disponible sur ce navigateur."
          : 'Geolocation is not available in this browser.'
      )
      return
    }

    setLocationLoading(true)
    setLocationError('')

    navigator.geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude, accuracy } = position.coords
        const normalized = {
          lat: Number(latitude.toFixed(5)),
          lon: Number(longitude.toFixed(5)),
          accuracy: Number.isFinite(accuracy) ? Math.round(accuracy) : null,
        }
        setUserLocation(normalized)
        setLocationLoading(false)
        setShowMap(true)
      },
      (error) => {
        setLocationLoading(false)
        let message
        switch (error.code) {
          case 1:
            message =
              lang === 'fr'
                ? 'Autorisation de localisation refusée. Vous pouvez réessayer depuis les paramètres du navigateur.'
                : 'Location permission denied. You can retry from your browser settings.'
            break
          case 2:
            message =
              lang === 'fr'
                ? 'Impossible de récupérer votre position pour le moment.'
                : 'Unable to retrieve your position right now.'
            break
          case 3:
            message =
              lang === 'fr'
                ? 'La localisation a pris trop de temps. Réessayez près d’une fenêtre ou en vérifiant votre connexion.'
                : 'Location timed out. Try again near a window or after checking your connection.'
            break
          default:
            message =
              lang === 'fr'
                ? 'Un imprévu a empêché la localisation. Réessayez dans un instant.'
                : 'Something went wrong while locating you. Please try again shortly.'
        }
        setLocationError(message)
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    )
  }

  function pushRouteToChat() {
    const text = lang === 'fr'
      ? `Point de départ: ${origin}. Destination: ${destination}. Propose un itinéraire de visite avec horaires optimisés et conseils météo.`
      : `Start at: ${origin}. Destination: ${destination}. Suggest a timed visit plan with weather-aware tips.`
    sendMessage(text)
  }

  const sendMessage = async (rawText) => {
    const text = rawText.trim()
    if (!text) return
    if (isLoading) return

    const personaHint = PERSONA_HINTS[persona] ?? ''
    const langHint = lang === 'fr' ? LANG_HINTS.fr : ''
    const locationHint = userLocation
      ? lang === 'fr'
        ? `Ma position actuelle: latitude ${userLocation.lat}, longitude ${userLocation.lon}${
            userLocation.accuracy ? ` (±${userLocation.accuracy} m)` : ''
          }.`
        : `My current position: latitude ${userLocation.lat}, longitude ${userLocation.lon}${
            userLocation.accuracy ? ` (±${userLocation.accuracy} m)` : ''
          }.`
      : ''
    const enrichedText = [personaHint, langHint, locationHint, text].filter(Boolean).join('\n')

    setMessages((prev) => [...prev, { role: 'user', text }])
    setInput('')
    setIsLoading(true)

    abortControllerRef.current?.abort()
    const controller = new AbortController()
    abortControllerRef.current = controller

    try {
      const response = await fetch(`${API_BASE_URL}/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: enrichedText, session_id: sessionId }),
        signal: controller.signal,
      })

      if (!response.ok) {
        throw new Error(`Server responded with ${response.status}`)
      }

      const data = await response.json()
      const reply = normalizeReply(data?.response || data?.answer || '')

      if (data?.plan && Array.isArray(data.plan.timeline)) {
        const planData = data.plan
        setPlan(planData)
        const hasWaypoints = Array.isArray(planData.waypoints) && planData.waypoints.length > 0
        const segments = toLeafletCoords(planData.geometry)
        const hasPolyline = segments.some((segment) => segment.length > 0)
        if (!hasWaypoints && !hasPolyline) {
          setShowMap(false)
        }
      } else if (Object.prototype.hasOwnProperty.call(data, 'plan')) {
        setPlan(null)
        setShowMap(false)
      }

      // If backend returned a route payload, project it on the map automatically
      const route = data?.route
      if (route && route.geometry) {
        try {
          setMarkerA(route.origin ? { lat: route.origin.lat, lon: route.origin.lon } : null)
          setMarkerB(route.destination ? { lat: route.destination.lat, lon: route.destination.lon } : null)
          const segs = geometryToSegments(route.geometry)
          setRouteSegments(segs)
          setRouteCoords(segs.length ? segs.flat() : [])
          setRouteSteps(Array.isArray(route?.steps) ? route.steps : [])
          setMapOpen(true)
        } catch (_) {}
      }

      setMessages((prev) => {
        const next = [...prev, { role: 'assistant', text: reply }]
        if (route) {
          const km = typeof route.distance_m === 'number' ? route.distance_m / 1000 : 0
          const minutes = typeof route.duration_s === 'number' ? Math.round(route.duration_s / 60) : 0
          const profile = route.profile || 'walking'
          next.push({
            role: 'assistant',
            text: `📍 Itinerary ≈ ${km.toFixed(1)} km · ≈ ${minutes} min (${profile})`,
          })
        }
        return next
      })
    } catch (error) {
      const fallback =
        "Le concierge rencontre un imprévu. Vérifiez que le backend est lancé (port 8002) ou réessayez dans un instant."
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: `${fallback}\n\nDétails techniques : ${error.message}`,
          isError: true,
        },
      ])
    } finally {
      setIsLoading(false)
    }
  }

  const handleSubmit = (event) => {
    event.preventDefault()
    if (!input.trim()) return
    sendMessage(input)
  }

  const handleQuickChip = (chip) => {
    if (isLoading) return
    sendMessage(chip)
  }

  const clearConversation = async () => {
    abortControllerRef.current?.abort()
    const previousSession = sessionId
    const freshSessionId = createSessionId()

    setIsLoading(false)
    setMessages([INITIAL_ASSISTANT_MESSAGE])
    setSessionId(freshSessionId)
    setInput('')
    setRouteCoords([])
    setRouteSegments([])
    setRouteSteps([])
    setPlan(null)
    setShowMap(false)

    if (typeof window !== 'undefined') {
      try {
        window.localStorage.setItem(STORAGE_KEYS.messages, JSON.stringify([INITIAL_ASSISTANT_MESSAGE]))
        window.localStorage.setItem(STORAGE_KEYS.session, freshSessionId)
      } catch (error) {}
    }

    if (previousSession && previousSession !== 'session-default') {
      try {
        await fetch(`${API_BASE_URL}/chat/sessions/${previousSession}`, {
          method: 'DELETE',
        })
      } catch (error) {
        // ignore cleanup errors
      }
    }
  }

  return (
    <div className="app-shell">
      <div className="app-shell__backdrop" aria-hidden />

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
              <h1>Versailles Concierge</h1>
              <p>Chat + Map assistant for the Château &amp; Gardens</p>
            </div>
          </div>

          <div className="app-header__toggles">
            <PersonaToggle value={persona} onChange={setPersona} />
            <LangToggle value={lang} onChange={setLang} />
          </div>
        </div>

        <div className="meta-grid">
          <Card>
            <SectionTitle icon={Users} title="Crowd now" right={<Chip>{crowd.label}</Chip>} />
            <div className="meta-grid__body">
              <Progress value={crowd.value} />
              <p className="meta-note">Tip: Peak 11:00–15:00. Hall of Mirrors calmer after 15:00.</p>
            </div>
          </Card>

          <Card>
            <SectionTitle icon={Clock} title="Today’s key hours" />
            <div className="hours-grid">
              <div>
                <span className="hours-grid__label">Château</span>
                <strong>
                  {HOURS.chateau.open}–{HOURS.chateau.close}
                </strong>
                <span className="hours-grid__muted">Last entry {HOURS.chateau.last}</span>
              </div>
              <div>
                <span className="hours-grid__label">Trianon</span>
                <strong>
                  {HOURS.trianon.open}–{HOURS.trianon.close}
                </strong>
                <span className="hours-grid__muted">Last entry {HOURS.trianon.last}</span>
              </div>
            </div>
            <div className="hours-hint">
              <Info size={16} />
              {minsLeft > 0 ? (
                <span>
                  If you hold a {HOURS.chateau.open} ticket, you must enter by {minutesToHHMM(inMinutes(HOURS.chateau.open) + 30)} (30‑minute window).
                </span>
              ) : (
                <span>Last admission has passed for today.</span>
              )}
            </div>
          </Card>

          <Card>
            <SectionTitle icon={Sun} title="Weather-aware tip" />
            <div className="weather-block">
              <div className="weather-block__icon">
                <WeatherGlyph condition={weather.condition} />
              </div>
              <div>
                <strong className="weather-block__title">
                  {weatherLoading ? '…' : `${Math.round(weather.tempC)}°C`} • {weather.condition.replace('-', ' ')}
                </strong>
                <p>
                  {weatherLoading
                    ? (lang === 'fr' ? 'Chargement des conseils météo…' : 'Loading weather advice…')
                    : weather.advice}
                </p>
                {weatherError ? (
                  <p className="meta-note" style={{ color: '#b33' }}>
                    {(lang === 'fr' ? 'Astuce temporaire' : 'Temporary tip') + ': ' + MOCK_WEATHER.advice}
                  </p>
                ) : null}
              </div>
            </div>
          </Card>
        </div>
      </header>

      <main className="app-main container">
        <div className="plan-column">
          {mapOpen ? (
            <Card className="map-card">
              <SectionTitle
                icon={Compass}
                title={lang === 'fr' ? 'Carte & itinéraire' : 'Map & Route'}
                right={<Pill onClick={() => setMapOpen(false)}>{lang === 'fr' ? 'Masquer' : 'Hide'}</Pill>}
              />
              <div className="map-card__body">
                <div className="map-controls">
                  <input
                    className="map-input"
                    placeholder={lang === 'fr' ? 'Origine (ex: Gare Rive Gauche)' : 'Origin (e.g., Rive Gauche Station)'}
                    value={origin}
                    onChange={(e) => setOrigin(e.target.value)}
                  />
                  <input
                    className="map-input"
                    placeholder={lang === 'fr' ? 'Destination' : 'Destination'}
                    value={destination}
                    onChange={(e) => setDestination(e.target.value)}
                  />
                  <select className="map-select" value={profile} onChange={(e) => setProfile(e.target.value)}>
                    <option value="walking">{lang === 'fr' ? 'Marche' : 'Walking'}</option>
                    <option value="driving">{lang === 'fr' ? 'Voiture' : 'Driving'}</option>
                    <option value="cycling">{lang === 'fr' ? 'Vélo' : 'Cycling'}</option>
                  </select>
                </div>
                <div className="map-actions">
                  <Pill onClick={fetchVersaillesRoute}>{lang === 'fr' ? 'Versailles depuis Origine' : 'To Château from Origin'}</Pill>
                  <Pill onClick={fetchRouteBetween} disabled={!origin.trim() || !destination.trim()}>
                    {lang === 'fr' ? 'Itinéraire A → B' : 'Route A → B'}
                  </Pill>
                  <Pill onClick={fetchRouteMultiDemo}>{lang === 'fr' ? 'Multi‑étapes (démo)' : 'Multi‑stop (demo)'}</Pill>
                  <Pill onClick={pushRouteToChat}>{lang === 'fr' ? 'Demander au Concierge' : 'Ask Concierge'}</Pill>
                </div>
                <div className="map-view">
                  <RouteMap coords={routeCoords} markers={[markerA, markerB]} />
                </div>
                {routeSteps && routeSteps.length ? (
                  <div className="directions">
                    <div className="directions__header">{lang === 'fr' ? 'Étapes clés' : 'Directions'}</div>
                    <ol className="directions__list">
                      {routeSteps.map((s, idx) => {
                        const road = s?.road || ''
                        const type = s?.type || ''
                        const mod = s?.modifier ? ` (${s.modifier})` : ''
                        const dist = typeof s?.distance_m === 'number' ? `${Math.round(s.distance_m)} m` : ''
                        return (
                          <li key={idx} className="directions__item">
                            <span className="directions__primary">{type}{mod}{road ? ` — ${road}` : ''}</span>
                            <span className="directions__meta">{dist}</span>
                          </li>
                        )
                      })}
                    </ol>
                  </div>
                ) : null}
                {routeError ? <p className="meta-note" style={{ color: '#f99' }}>{routeError}</p> : null}
                {routeLoading ? <p className="meta-note">{lang === 'fr' ? 'Calcul de l’itinéraire…' : 'Computing route…'}</p> : null}
              </div>
            </Card>
          ) : null}

          <Card>
            <SectionTitle
              icon={MapPin}
              title={plan?.title || (lang === 'fr' ? 'Plan suggéré' : 'Suggested plan')}
              right={
                <Pill icon={Compass} onClick={() => setShowMap((v) => !v)} disabled={!hasMapData}>
                  {showMap
                    ? lang === 'fr'
                      ? 'Fermer la carte'
                      : 'Close Map'
                    : lang === 'fr'
                      ? 'Afficher la carte'
                      : 'Open Map'}
                </Pill>
              }
            />
            <div className="timeline">
              {planTimeline.map((stop, index) => (
                <div key={`${stop.t}-${stop.title}-${index}`} className="timeline__item">
                  <div className="timeline__step">{index + 1}</div>
                  <div>
                    <div className="timeline__title">{stop.title}</div>
                    {stop.note ? <div className="timeline__note">{stop.note}</div> : null}
                  </div>
                  <div className="timeline__time">{stop.t}</div>
                </div>
              ))}
              {planTimeline.length === 0 ? (
                <div className="timeline__note">
                  {lang === 'fr'
                    ? 'Envoyez une demande au concierge pour générer un plan.'
                    : 'Send a request to the concierge to generate a plan.'}
                </div>
              ) : null}
            </div>
            <div className="location-share">
              <Pill icon={MapPin} onClick={requestUserLocation} disabled={locationLoading}>
                {locationButtonLabel}
              </Pill>
              <span className={locationInfoClass}>{locationInfoText}</span>
            </div>
            {showMap && hasMapData ? (
              <div className="map-wrap" style={{ height: 400, marginTop: 12, borderRadius: 12, overflow: 'hidden' }}>
                <MapContainer
                  center={[mapCenterLat, mapCenterLon]}
                  zoom={15}
                  style={{ height: '100%', width: '100%' }}
                  scrollWheelZoom={false}
                >
                  <LayersControl position="topright">
                    <LayersControl.BaseLayer checked name="OpenStreetMap">
                      <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                    </LayersControl.BaseLayer>
                  </LayersControl>

                  {planWaypoints.map((wp, i) => (
                    <Marker key={`${wp.lat}-${wp.lon}-${i}`} position={[wp.lat, wp.lon]} />
                  ))}

                  {planSegments.map((segment, i) =>
                    segment.length ? (
                      <Polyline key={`seg-${i}`} positions={segment} color="#f1c45b" weight={4} />
                    ) : null
                  )}

                  {userLocation ? (
                    <Marker position={[userLocation.lat, userLocation.lon]}>
                      <Popup>{lang === 'fr' ? 'Vous êtes ici' : 'You are here'}</Popup>
                    </Marker>
                  ) : null}
                </MapContainer>
              </div>
            ) : null}

            <div className="plan-actions">
              <Pill icon={Ticket}>Buy tickets</Pill>
              <Pill icon={Accessibility}>Accessibility</Pill>
              <Pill icon={Languages}>Languages</Pill>
            </div>
          </Card>

          <Card>
            <SectionTitle icon={Sparkles} title="Smart suggestions" />
            <div className="suggestions">
              {QUICK_CHIPS.map((chip) => (
                <button
                  key={chip}
                  type="button"
                  className="suggestion"
                  onClick={() => handleQuickChip(chip)}
                  disabled={isLoading}
                >
                  <Wand2 size={16} />
                  {chip}
                </button>
              ))}
            </div>
          </Card>
        </div>

        <Card className="chat-card">
          <div className="chat-card__header">
            <SectionTitle icon={MessageCircle} title="Chat with your Concierge" />
            <div className="chat-card__meta">
              <div className="chat-card__status">
                <span className="chat-card__status-dot" />
                Online
              </div>
              <Pill icon={Trash2} onClick={clearConversation}>
                {lang === 'fr' ? 'Effacer' : 'Clear chat'}
              </Pill>
            </div>
          </div>

          <div className="chat-feed" ref={chatFeedRef}>
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
                <p>Le concierge prépare sa réponse…</p>
              </div>
            ) : null}
          </div>

          <form className="chat-input" onSubmit={handleSubmit}>
            <div className="chat-input__field">
              <textarea
                rows={2}
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Ask for a plan, a time slot, or tips…"
                disabled={isLoading}
              />
              <div className="chat-input__chips">
                {QUICK_CHIPS.slice(0, 3).map((chip) => (
                  <button
                    key={chip}
                    type="button"
                    onClick={() => setInput((value) => (value ? `${value} ${chip}` : chip))}
                    disabled={isLoading}
                  >
                    {chip}
                  </button>
                ))}
              </div>
            </div>
            <button type="submit" className="chat-input__send" disabled={isLoading || !input.trim()}>
              {isLoading ? 'Sending…' : 'Send'}
            </button>
          </form>
        </Card>
      </main>

      <motion.button
        type="button"
        className="compass-button"
        initial={{ y: 40, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3, type: 'spring', stiffness: 150 }}
        aria-label="Open concierge map"
        onClick={() => setMapOpen((v) => !v)}
      >
        <Compass size={24} />
      </motion.button>

      <footer className="app-footer container">
        Inspired by Versailles’ gilded halls &amp; geometric gardens • Swap mock data for live APIs when ready
      </footer>
    </div>
  )
}

export default VersaillesConcierge
