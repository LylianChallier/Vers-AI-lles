import { Card, SectionTitle, Pill, RouteMap } from './common'
import { Compass } from 'lucide-react'

export function MapPanel({
  copy,
  open,
  onClose,
  origin,
  destination,
  profile,
  setOrigin,
  setDestination,
  setProfile,
  onFetchVersailles,
  onFetchBetween,
  onFetchMulti,
  onAskConcierge,
  routeCoords,
  markerA,
  markerB,
  routeSteps,
  routeError,
  routeLoading,
}) {
  if (!open) return null

  return (
    <Card className="map-card">
      <SectionTitle
        icon={Compass}
        title={copy.title}
        right={<Pill onClick={onClose}>{copy.hide}</Pill>}
      />
      <div className="map-card__body">
        <div className="map-controls">
          <input
            className="map-input"
            placeholder={copy.controls.originPlaceholder}
            value={origin}
            onChange={(e) => setOrigin(e.target.value)}
          />
          <input
            className="map-input"
            placeholder={copy.controls.destinationPlaceholder}
            value={destination}
            onChange={(e) => setDestination(e.target.value)}
          />
          <select className="map-select" value={profile} onChange={(e) => setProfile(e.target.value)}>
            <option value="walking">{copy.controls.profile.walking}</option>
            <option value="driving">{copy.controls.profile.driving}</option>
            <option value="cycling">{copy.controls.profile.cycling}</option>
          </select>
        </div>
        <div className="map-actions">
          <Pill onClick={onFetchVersailles}>{copy.buttons.versaillesFromOrigin}</Pill>
          <Pill onClick={onFetchBetween} disabled={!origin.trim() || !destination.trim()}>
            {copy.buttons.routeAB}
          </Pill>
          <Pill onClick={onFetchMulti}>{copy.buttons.multiDemo}</Pill>
          <Pill onClick={onAskConcierge}>{copy.buttons.askConcierge}</Pill>
        </div>
        <div className="map-view">
          <RouteMap coords={routeCoords} markers={[markerA, markerB]} />
        </div>
        {routeSteps && routeSteps.length ? (
          <div className="directions">
            <div className="directions__header">{copy.directionsTitle}</div>
            <ol className="directions__list">
              {routeSteps.map((step, idx) => {
                const road = step?.road || ''
                const type = step?.type || ''
                const modifier = step?.modifier ? ` (${step.modifier})` : ''
                const distance = typeof step?.distance_m === 'number' ? `${Math.round(step.distance_m)} m` : ''
                return (
                  <li key={idx} className="directions__item">
                    <span className="directions__primary">{type}{modifier}{road ? ` — ${road}` : ''}</span>
                    <span className="directions__meta">{distance}</span>
                  </li>
                )
              })}
            </ol>
          </div>
        ) : null}
        {routeError ? <p className="meta-note" style={{ color: '#f99' }}>{routeError}</p> : null}
        {routeLoading ? <p className="meta-note">{copy.loading}</p> : null}
      </div>
    </Card>
  )
}
