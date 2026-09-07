const DEFAULT_BRIDGE_PORT = 8765
const API_SUFFIX = '/api'

export function normalizeApiBase(value) {
  const trimmed = String(value ?? '').trim()
  if (!trimmed) return ''
  return trimmed.replace(/\/+$/, '').replace(/\/api$/, '')
}

export function getDefaultApiBase(locationLike = window.location) {
  const hostname = String(locationLike?.hostname || '127.0.0.1')
  const host = hostname.includes(':') && !hostname.startsWith('[') ? `[${hostname}]` : hostname
  return `http://${host}:${DEFAULT_BRIDGE_PORT}${API_SUFFIX}`
}

export function resolveApiBase(locationLike = window.location, override = '') {
  const cleanOverride = normalizeApiBase(override)
  return cleanOverride ? `${cleanOverride}${API_SUFFIX}` : getDefaultApiBase(locationLike)
}
