import { MapContainer, TileLayer, LayersControl, Marker, Polyline, Popup } from 'react-leaflet'
import { Card, SectionTitle, Pill } from './common'
import { MapPin, Compass } from 'lucide-react'

export function PlanPanel({
  copy,
  title,
  timeline,
  onRequestLocation,
  locationButtonLabel,
  locationLoading,
  locationInfoText,
  locationInfoClass,
  hasMapData,
  showMap,
  toggleMap,
  mapCenterLat,
  mapCenterLon,
  planWaypoints,
  planSegments,
  userLocation,
}) {
  return (
    <Card>
      <SectionTitle
        icon={MapPin}
        title={title}
        right={
          <Pill icon={Compass} onClick={toggleMap} disabled={!hasMapData}>
            {showMap ? copy.closeMap : copy.openMap}
          </Pill>
        }
      />
      <div className="timeline">
        {timeline.map((stop, index) => (
          <div key={`${stop.t}-${index}`} className="timeline__item">
            <div className="timeline__step">{index + 1}</div>
            <div>
              <div className="timeline__title">{stop.title}</div>
              {stop.note ? <div className="timeline__note">{stop.note}</div> : null}
            </div>
            <div className="timeline__time">{stop.t}</div>
          </div>
        ))}
        {timeline.length === 0 ? <div className="timeline__note">{copy.empty}</div> : null}
      </div>
      <div className="location-share">
        <Pill icon={MapPin} onClick={onRequestLocation} disabled={locationLoading}>
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
                <Popup>{copy.youAreHere}</Popup>
              </Marker>
            ) : null}
          </MapContainer>
        </div>
      ) : null}
    </Card>
  )
}
