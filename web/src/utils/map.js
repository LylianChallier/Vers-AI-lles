export function toLeafletCoords(geometry) {
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
