import { Info, Sun, Users, Clock } from 'lucide-react'
import { Card, SectionTitle, Progress, Chip, WeatherGlyph } from './common'
import { HOURS } from '../constants/translations'

export function MetaSummary({ copy, crowd, crowdLabel, weather, weatherLoading, weatherError, weatherFallbackAdvice, hoursInfoText }) {
  return (
    <div className="meta-grid">
      <Card>
        <SectionTitle icon={Users} title={copy.crowd.title} right={<Chip>{crowdLabel}</Chip>} />
        <div className="meta-grid__body">
          <Progress value={crowd.value} />
          <p className="meta-note">{copy.crowd.tip}</p>
        </div>
      </Card>

      <Card>
        <SectionTitle icon={Clock} title={copy.hours.title} />
        <div className="hours-grid">
          <div>
            <span className="hours-grid__label">{copy.hours.chateau}</span>
            <strong>
              {HOURS.chateau.open}–{HOURS.chateau.close}
            </strong>
            <span className="hours-grid__muted">{copy.hours.lastEntry} {HOURS.chateau.last}</span>
          </div>
          <div>
            <span className="hours-grid__label">{copy.hours.trianon}</span>
            <strong>
              {HOURS.trianon.open}–{HOURS.trianon.close}
            </strong>
            <span className="hours-grid__muted">{copy.hours.lastEntry} {HOURS.trianon.last}</span>
          </div>
        </div>
        <div className="hours-hint">
          <Info size={16} />
          <span>{hoursInfoText}</span>
        </div>
      </Card>

      <Card>
        <SectionTitle icon={Sun} title={copy.weather.title} />
        <div className="weather-block">
          <div className="weather-block__icon">
            <WeatherGlyph condition={weather.condition} />
          </div>
          <div>
            <strong className="weather-block__title">
              {weatherLoading ? '…' : `${Math.round(weather.tempC)}°C`} • {weather.condition.replace('-', ' ')}
            </strong>
            <p>{weatherLoading ? copy.weather.loading : weather.advice}</p>
            {weatherError ? (
              <p className="meta-note" style={{ color: '#b33' }}>
                {copy.weather.fallbackLabel + ': ' + weatherFallbackAdvice}
              </p>
            ) : null}
          </div>
        </div>
      </Card>
    </div>
  )
}
