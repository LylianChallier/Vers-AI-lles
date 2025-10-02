import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { Compass } from 'lucide-react'
import './App.css'

import {
  TRANSLATIONS,
  WEATHER_FALLBACK,
  HOURS,
  LANG_HINTS,
  SUGGESTION_KEYS,
} from './constants/translations'
import { createInitialMessage, getLocaleText } from './utils/locale'
import { toLeafletCoords } from './utils/map'
import { crowdLevel, inMinutes } from './utils/time'
import { Header } from './components/Header'
import { MetaSummary } from './components/MetaSummary'
import { MapPanel } from './components/MapPanel'
import { PlanPanel } from './components/PlanPanel'
import { SuggestionsPanel } from './components/SuggestionsPanel'
import { ChatPanel } from './components/ChatPanel'
import { Pill } from './components/common'

const STORAGE_KEYS = {
  session: 'versailles-concierge-session',
  messages: 'versailles-concierge-messages',
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

function VersaillesConcierge() {
  const [lang, setLang] = useState(() => getStoredValue(STORAGE_KEYS.lang, 'en'))
  const copy = useMemo(() => TRANSLATIONS[lang] ?? TRANSLATIONS.en, [lang])

  const [input, setInput] = useState('')
  const [messages, setMessages] = useState(() => {
    const stored = getStoredJSON(STORAGE_KEYS.messages, null)
    if (Array.isArray(stored) && stored.length) {
      return stored
    }
    const initialLang = getStoredValue(STORAGE_KEYS.lang, 'en')
    return [createInitialMessage(initialLang)]
  })
  const [plan, setPlan] = useState(null)
  const [showMap, setShowMap] = useState(false)
  const [userLocation, setUserLocation] = useState(null)
  const [locationError, setLocationError] = useState('')
  const [locationLoading, setLocationLoading] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [sessionId, setSessionId] = useState(() => getStoredValue(STORAGE_KEYS.session, createSessionId()))

  const [weather, setWeather] = useState(() => {
    const initialLang = getStoredValue(STORAGE_KEYS.lang, 'en')
    const fallback = WEATHER_FALLBACK[initialLang] ?? WEATHER_FALLBACK.en
    return { ...fallback }
  })
  const [weatherLoading, setWeatherLoading] = useState(false)
  const [weatherError, setWeatherError] = useState('')

  const [mapOpen, setMapOpen] = useState(false)
  const [profile, setProfile] = useState('walking')
  const [origin, setOrigin] = useState('Versailles Château Rive Gauche')
  const [destination, setDestination] = useState('Château de Versailles, France')
  const [routeCoords, setRouteCoords] = useState([])
  const [routeSegments, setRouteSegments] = useState([])
  const [routeLoading, setRouteLoading] = useState(false)
  const [routeError, setRouteError] = useState('')
  const [routeSteps, setRouteSteps] = useState([])
  const [markerA, setMarkerA] = useState(null)
  const [markerB, setMarkerB] = useState(null)

  const crowd = useMemo(() => crowdLevel(new Date()), [])
  const suggestions = useMemo(
    () => SUGGESTION_KEYS.map((key) => ({ key, label: copy.suggestions[key] })),
    [copy]
  )
  const chatFeedRef = useRef(null)
  const abortControllerRef = useRef(null)
  const weatherAbortRef = useRef(null)

  const normalizeReply = (raw) => {
    if (!raw || typeof raw !== 'string') return copy.chat.errorGeneral
    let s = raw.trim()
    if (/^json\b/i.test(s)) {
      const braceIndex = s.indexOf('{')
      s = braceIndex >= 0 ? s.slice(braceIndex) : s
    }
    s = s.replace(/^```json\s*/i, '').replace(/```$/i, '').trim()
    try {
      const obj = JSON.parse(s)
      if (obj && typeof obj.response === 'string') {
        return obj.response.trim() || copy.chat.errorGeneral
      }
    } catch (_) {}
    return s || copy.chat.errorGeneral
  }

  const sendLocationToServer = useCallback(
    async (loc) => {
      try {
        const response = await fetch(`${API_BASE_URL}/tools/share_location`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            ...loc,
            ts: Date.now(),
            session_id: sessionId,
          }),
        })
        if (!response.ok) throw new Error(`HTTP ${response.status}`)
      } catch (error) {
        console.error('share_location failed:', error)
      }
    },
    [sessionId]
  )

  const nowMins = new Date().getHours() * 60 + new Date().getMinutes()
  const minsLeft = Math.max(0, inMinutes(HOURS.chateau.last) - nowMins)

  const weatherFallbackAdvice = (WEATHER_FALLBACK[lang] ?? WEATHER_FALLBACK.en).advice

  const planTimeline = useMemo(() => {
    if (!Array.isArray(plan?.timeline)) return []
    return plan.timeline.map((stop) => ({
      t: stop.t,
      title: getLocaleText(stop.title, lang),
      note: getLocaleText(stop.note, lang),
    }))
  }, [plan, lang])

  const planWaypoints = Array.isArray(plan?.waypoints) ? plan.waypoints : []
  const planSegments = useMemo(() => toLeafletCoords(plan?.geometry), [plan?.geometry])
  const hasMapData = planWaypoints.length > 0 || planSegments.some((segment) => segment.length > 0) || !!userLocation
  const mapCenterLat = planWaypoints[0]?.lat ?? userLocation?.lat ?? 48.8049
  const mapCenterLon = planWaypoints[0]?.lon ?? userLocation?.lon ?? 2.1204

  const locationButtonLabel = locationLoading
    ? copy.plan.locationButton.loading
    : userLocation
    ? copy.plan.locationButton.refresh
    : copy.plan.locationButton.request
  const locationInfoText = userLocation
    ? copy.plan.locationShared(userLocation)
    : locationError || copy.plan.locationPrompt
  const locationInfoHasError = Boolean(locationError)
  const locationInfoClass = locationInfoHasError ? 'location-share__info location-share__info--error' : 'location-share__info'

  const crowdLabel = copy.crowd.labels[crowd.key] || copy.crowd.labels.low
  const hoursInfoText = minsLeft > 0 ? copy.hours.entryInfo(HOURS.chateau.open) : copy.hours.entryLate

  const rawPlanTitle = getLocaleText(plan?.title, lang).trim()
  const normalizedPlanTitle = rawPlanTitle
    ? rawPlanTitle === 'Suggested plan' || rawPlanTitle === 'Plan suggéré'
      ? copy.plan.title
      : rawPlanTitle
    : copy.plan.title

  useEffect(() => {
    if (!chatFeedRef.current) return
    chatFeedRef.current.scrollTo({ top: chatFeedRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, isLoading])

  useEffect(() => {
    setLocationError('')
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
      window.localStorage.setItem(STORAGE_KEYS.lang, lang)
    } catch (error) {}
  }, [lang])

  useEffect(() => {
    if (messages.length === 1 && messages[0]?.role === 'assistant') {
      const updated = createInitialMessage(lang)
      if (messages[0]?.text !== updated.text) {
        setMessages([updated])
      }
    }
  }, [lang, messages])

  useEffect(() => {
    if (!userLocation) return
    const formatted = `${userLocation.lat}, ${userLocation.lon}`
    setOrigin(formatted)
  }, [userLocation])

  const fetchWeather = async () => {
    setWeatherLoading(true)
    setWeatherError('')

    try {
      weatherAbortRef.current?.abort()
    } catch {}
    const controller = new AbortController()
    weatherAbortRef.current = controller

    try {
      const payload = {
        date: new Date().toISOString().slice(0, 10),
        start_time: new Date().toTimeString().slice(0, 5),
        duration_min: 180,
        place: 'Château de Versailles, France',
        lang,
      }

      const response = await fetch(`${API_BASE_URL}/tools/weather`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: controller.signal,
      })

      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const data = await response.json()

      const label = data?.summary?.label || 'pleasant'
      const fallback = WEATHER_FALLBACK[lang] ?? WEATHER_FALLBACK.en
      const advice = data?.summary?.advice || fallback.advice
      const nextHour = Array.isArray(data?.hourly) && data.hourly.length > 0 ? data.hourly[0] : null
      const tempC = nextHour?.temp_c ?? fallback.tempC

      const condition = ({
        heavy_rain: 'rain',
        rain_risk: 'rain',
        mixed: 'partly-cloudy',
        heat: 'sunny',
        windy: 'partly-cloudy',
        pleasant: 'sunny',
      })[label] || 'partly-cloudy'

      setWeather({ condition, tempC, advice })
    } catch (error) {
      setWeatherError(copy.weather.error)
      setWeather((prev) => ({ ...prev, advice: weatherFallbackAdvice }))
    } finally {
      setWeatherLoading(false)
    }
  }

  useEffect(() => {
    fetchWeather()
  }, [lang])

  const geometryToSegments = (geometry) => {
    try {
      if (!geometry || typeof geometry !== 'object') return []
      if (geometry.type === 'LineString') {
        return [geometry.coordinates.map((c) => [c[1], c[0]])]
      }
      if (geometry.type === 'MultiLineString' && Array.isArray(geometry.coordinates)) {
        return geometry.coordinates.map((coords) =>
          Array.isArray(coords) ? coords.map((c) => [c[1], c[0]]) : []
        )
      }
      return []
    } catch {
      return []
    }
  }

  const fetchVersaillesRoute = async () => {
    setRouteLoading(true)
    setRouteError('')
    setRouteSteps([])
    try {
      const response = await fetch(`${API_BASE_URL}/tools/versailles_route`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ origin, profile }),
      })
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const data = await response.json()
      setMarkerA({ lat: data?.origin?.lat, lon: data?.origin?.lon })
      setMarkerB({ lat: data?.destination?.lat, lon: data?.destination?.lon })
      const segments = geometryToSegments(data?.geometry)
      setRouteSegments(segments)
      setRouteCoords(segments.length ? segments.flat() : [])
      setRouteSteps(Array.isArray(data?.steps) ? data.steps : [])
      setMapOpen(true)
    } catch (error) {
      setRouteError(error?.message || copy.mapCard.error)
    } finally {
      setRouteLoading(false)
    }
  }

  const fetchRouteBetween = async () => {
    if (!origin.trim() || !destination.trim()) return
    setRouteLoading(true)
    setRouteError('')
    setRouteSteps([])
    try {
      const response = await fetch(`${API_BASE_URL}/tools/route`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ origin, destination, profile }),
      })
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const data = await response.json()
      setMarkerA({ lat: data?.origin?.lat, lon: data?.origin?.lon })
      setMarkerB({ lat: data?.destination?.lat, lon: data?.destination?.lon })
      const segments = geometryToSegments(data?.geometry)
      setRouteSegments(segments)
      setRouteCoords(segments.length ? segments.flat() : [])
      setRouteSteps(Array.isArray(data?.steps) ? data.steps : [])
      setMapOpen(true)
    } catch (error) {
      setRouteError(error?.message || copy.mapCard.error)
    } finally {
      setRouteLoading(false)
    }
  }

  const fetchRouteMultiDemo = async () => {
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
      const response = await fetch(`${API_BASE_URL}/tools/route_multi`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ places, profile }),
      })
      if (!response.ok) throw new Error(`HTTP ${response.status}`)
      const data = await response.json()
      const segments = geometryToSegments(data?.geometry)
      setRouteSegments(segments)
      setRouteCoords(segments.length ? segments.flat() : [])
      const waypoints = Array.isArray(data?.waypoints) ? data.waypoints : []
      setMarkerA(waypoints[0] ? { lat: waypoints[0].lat, lon: waypoints[0].lon } : null)
      setMarkerB(waypoints[waypoints.length - 1] ? { lat: waypoints[waypoints.length - 1].lat, lon: waypoints[waypoints.length - 1].lon } : null)
      const steps = []
      if (Array.isArray(data?.segments)) {
        for (const segment of data.segments) {
          if (Array.isArray(segment?.steps)) steps.push(...segment.steps)
        }
      }
      setRouteSteps(steps)
      setMapOpen(true)
    } catch (error) {
      setRouteError(error?.message || copy.mapCard.error)
    } finally {
      setRouteLoading(false)
    }
  }

  const requestUserLocation = () => {
    if (typeof navigator === 'undefined' || !navigator.geolocation) {
      setLocationError(copy.plan.locationErrors.unsupported)
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
        sendLocationToServer(normalized)
        setLocationLoading(false)
        setShowMap(true)
      },
      (error) => {
        setLocationLoading(false)
        let message
        switch (error.code) {
          case 1:
            message = copy.plan.locationErrors.permission
            break
          case 2:
            message = copy.plan.locationErrors.unavailable
            break
          case 3:
            message = copy.plan.locationErrors.timeout
            break
          default:
            message = copy.plan.locationErrors.unknown
        }
        setLocationError(message)
      },
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    )
  }

  const pushRouteToChat = () => {
    const text = copy.mapCard.prompts.ask(origin, destination)
    sendMessage(text)
  }

  const sendMessage = async (rawText) => {
    const text = rawText.trim()
    if (!text || isLoading) return

    const langHint = LANG_HINTS[lang] ?? ''
    const locationHint = userLocation ? copy.plan.locationHint(userLocation) : ''
    const enrichedText = [langHint, locationHint, text].filter(Boolean).join('\n')

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
        setPlan(data.plan)
        const segments = toLeafletCoords(data.plan.geometry)
        const hasWaypoints = Array.isArray(data.plan.waypoints) && data.plan.waypoints.length > 0
        const hasPolyline = segments.some((segment) => segment.length > 0)
        if (!hasWaypoints && !hasPolyline) {
          setShowMap(false)
        }
      } else if (Object.prototype.hasOwnProperty.call(data, 'plan')) {
        setPlan(null)
        setShowMap(false)
      }

      const route = data?.route
      if (route && route.geometry) {
        try {
          setMarkerA(route.origin ? { lat: route.origin.lat, lon: route.origin.lon } : null)
          setMarkerB(route.destination ? { lat: route.destination.lat, lon: route.destination.lon } : null)
          const segments = geometryToSegments(route.geometry)
          setRouteSegments(segments)
          setRouteCoords(segments.length ? segments.flat() : [])
          setRouteSteps(Array.isArray(route?.steps) ? route.steps : [])
          setMapOpen(true)
        } catch (_) {}
      }

      setMessages((prev) => {
        const next = [...prev, { role: 'assistant', text: reply }]
        if (route) {
          const km = typeof route.distance_m === 'number' ? route.distance_m / 1000 : 0
          const minutes = typeof route.duration_s === 'number' ? Math.round(route.duration_s / 60) : 0
          const profileLabel = route.profile || 'walking'
          next.push({
            role: 'assistant',
            text: copy.route.summary(km, minutes, profileLabel),
          })
        }
        return next
      })
    } catch (error) {
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: `${copy.chat.errorGeneral}\n\n${copy.chat.errorDetailsPrefix} ${error.message}`,
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

  const handleQuickChip = (label) => {
    if (isLoading) return
    sendMessage(label)
  }

  const clearConversation = async () => {
    abortControllerRef.current?.abort()
    const previousSession = sessionId
    const freshSessionId = createSessionId()
    const initialMessage = createInitialMessage(lang)

    setIsLoading(false)
    setMessages([initialMessage])
    setSessionId(freshSessionId)
    setInput('')
    setRouteCoords([])
    setRouteSegments([])
    setRouteSteps([])
    setPlan(null)
    setShowMap(false)

    if (typeof window !== 'undefined') {
      try {
        window.localStorage.setItem(STORAGE_KEYS.messages, JSON.stringify([initialMessage]))
        window.localStorage.setItem(STORAGE_KEYS.session, freshSessionId)
      } catch (error) {}
    }

    if (previousSession && previousSession !== 'session-default') {
      try {
        await fetch(`${API_BASE_URL}/chat/sessions/${previousSession}`, {
          method: 'DELETE',
        })
      } catch (error) {}
    }
  }

  return (
    <div className="app-shell">
      <div className="app-shell__backdrop" aria-hidden />

      <Header copy={copy.app} lang={lang} onLangChange={setLang} />

      <MetaSummary
        copy={copy}
        crowd={crowd}
        crowdLabel={crowdLabel}
        weather={weather}
        weatherLoading={weatherLoading}
      weatherError={weatherError}
      weatherFallbackAdvice={weatherFallbackAdvice}
      hoursInfoText={hoursInfoText}
    />

      <main className="app-main container">
        <div className="plan-column">
          <MapPanel
            copy={copy.mapCard}
            open={mapOpen}
            onClose={() => setMapOpen(false)}
            origin={origin}
            destination={destination}
            profile={profile}
            setOrigin={setOrigin}
            setDestination={setDestination}
            setProfile={setProfile}
            onFetchVersailles={fetchVersaillesRoute}
            onFetchBetween={fetchRouteBetween}
            onFetchMulti={fetchRouteMultiDemo}
            onAskConcierge={pushRouteToChat}
            routeCoords={routeCoords}
            markerA={markerA}
            markerB={markerB}
            routeSteps={routeSteps}
            routeError={routeError}
            routeLoading={routeLoading}
          />

          <PlanPanel
            copy={copy.plan}
            title={normalizedPlanTitle}
            timeline={planTimeline}
            onRequestLocation={requestUserLocation}
            locationButtonLabel={locationButtonLabel}
            locationLoading={locationLoading}
            locationInfoText={locationInfoText}
            locationInfoClass={locationInfoClass}
            hasMapData={hasMapData}
            showMap={showMap}
            toggleMap={() => setShowMap((value) => !value)}
            mapCenterLat={mapCenterLat}
            mapCenterLon={mapCenterLon}
            planWaypoints={planWaypoints}
            planSegments={planSegments}
            userLocation={userLocation}
          />

          <SuggestionsPanel
            title={copy.suggestionsTitle}
            suggestions={suggestions}
            onSelect={handleQuickChip}
            disabled={isLoading}
          />
        </div>

        <ChatPanel
          copy={copy.chat}
          messages={messages}
          isLoading={isLoading}
          input={input}
          onInputChange={setInput}
          onSubmit={handleSubmit}
          onClear={clearConversation}
          suggestions={suggestions}
          onSuggestion={handleQuickChip}
          feedRef={chatFeedRef}
        />
      </main>

      <motion.button
        type="button"
        className="compass-button"
        initial={{ y: 40, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ delay: 0.3, type: 'spring', stiffness: 150 }}
        aria-label={copy.compassLabel}
        onClick={() => setMapOpen((value) => !value)}
      >
        <Compass size={24} />
      </motion.button>

      <footer className="app-footer container">{copy.footer}</footer>
    </div>
  )
}

export default VersaillesConcierge
