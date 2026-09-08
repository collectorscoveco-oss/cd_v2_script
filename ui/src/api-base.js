const DEFAULT_BRIDGE_PORT = 8765
const RELEASE_UI_PORTS = new Set(['8766'])
const API_SUFFIX = '/api'

export function normalizeApiBase(value) {
  const trimmed = String(value ?? '').trim()
  if (!trimmed) return ''
  return trimmed.replace(/\/+$/, '').replace(/\/api$/, '')
}

export function getDefaultApiBase(locationLike = window.location) {
  const hostname = String(locationLike?.hostname || '127.0.0.1')
  const host = hostname.includes(':') && !hostname.startsWith('[') ? `[${hostname}]` : hostname
  const port = String(locationLike?.port || '')
  if (RELEASE_UI_PORTS.has(port)) {
    const origin = String(locationLike?.origin || '').replace(/\/+$/, '')
    if (origin && origin !== 'null') return `${origin}${API_SUFFIX}`
  }
  return `http://${host}:${DEFAULT_BRIDGE_PORT}${API_SUFFIX}`
}

export function resolveApiBase(locationLike = window.location, override = '') {
  const cleanOverride = normalizeApiBase(override)
  return cleanOverride ? `${cleanOverride}${API_SUFFIX}` : getDefaultApiBase(locationLike)
}
