import { useEffect, useRef } from 'react'
import { CloudRain, CloudSun, Sun } from 'lucide-react'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import marker2x from 'leaflet/dist/images/marker-icon-2x.png'
import marker1x from 'leaflet/dist/images/marker-icon.png'
import markerShadow from 'leaflet/dist/images/marker-shadow.png'

L.Icon.Default.mergeOptions({
  iconRetinaUrl: marker2x,
  iconUrl: marker1x,
  shadowUrl: markerShadow,
})

export function Pill({ children, icon: Icon, onClick, type = 'button', disabled }) {
  return (
    <button type={type} className="pill" onClick={onClick} disabled={disabled}>
      {Icon ? <Icon size={16} /> : null}
      <span>{children}</span>
    </button>
  )
}

export function Card({ children, className = '' }) {
  return <div className={['card', className].filter(Boolean).join(' ')}>{children}</div>
}

export function SectionTitle({ icon: Icon, title, right }) {
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

export function Progress({ value }) {
  const safeValue = Math.min(100, Math.max(0, value))
  return (
    <div className="progress">
      <div className="progress__fill" style={{ width: `${safeValue}%` }} />
    </div>
  )
}

export function Chip({ children }) {
  return <span className="chip">{children}</span>
}

export function WeatherGlyph({ condition }) {
  if (condition === 'rain') return <CloudRain className="weather-icon" size={20} />
  if (condition === 'sunny') return <Sun className="weather-icon" size={20} />
  return <CloudSun className="weather-icon" size={20} />
}

export function RouteMap({ coords = [], markers = [] }) {
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
