export const API_OVERRIDE_STORAGE_KEY = 'sonardeck.apiBaseOverride'
export const HOST_HISTORY_STORAGE_KEY = 'sonardeck.hostUrlHistory'
const HOST_HISTORY_LIMIT = 6
const FALLBACK_STORAGE = {
  getItem() {
    return null
  },
  setItem() {},
  removeItem() {},
}

function normalizeHostUrlValue(value: unknown) {
  const trimmed = String(value ?? '').trim()
  if (!trimmed) return ''
  return trimmed.replace(/\/+$/, '').replace(/\/api$/, '')
}

function isLoopbackHostUrl(url: string) {
  try {
    const hostname = new URL(url).hostname.toLowerCase()
    return hostname === 'localhost' || hostname === '127.0.0.1' || hostname === '[::1]' || hostname === '::1'
  } catch {
    return /(^|:\/\/)(localhost|127\.0\.0\.1|\[::1\]|::1)(:\d+)?$/i.test(url)
  }
}

export function isConnectableHostUrl(url: string) {
  return Boolean(url) && !isLoopbackHostUrl(url)
}

function readStoredUrls(storageLike: Pick<Storage, 'getItem'>): string[] {
  try {
    const raw = storageLike.getItem(HOST_HISTORY_STORAGE_KEY)
    if (!raw) return []
    const parsed: unknown = JSON.parse(raw)
    if (!Array.isArray(parsed)) return []
    return parsed.map((entry) => normalizeHostUrlValue(entry)).filter((entry): entry is string => Boolean(entry))
  } catch {
    return []
  }
}

export function getPreferredHostUrl(
  locationLike: Pick<Location, 'origin'> = typeof window !== 'undefined' ? window.location : ({ origin: '' } as Pick<Location, 'origin'>),
  override = '',
  storageLike: Pick<Storage, 'getItem'> = typeof window !== 'undefined' ? window.localStorage : FALLBACK_STORAGE,
) {
  const cleanOverride = normalizeHostUrlValue(override)
  if (isConnectableHostUrl(cleanOverride)) return cleanOverride

  const currentOrigin = normalizeHostUrlValue(locationLike?.origin || '')
  if (isConnectableHostUrl(currentOrigin)) return currentOrigin

  return loadHostHistory(storageLike).find((entry) => isConnectableHostUrl(entry)) ?? ''
}

export function loadHostHistory(storageLike: Pick<Storage, 'getItem'> = window.localStorage) {
  const history: string[] = []
  for (const entry of readStoredUrls(storageLike)) {
    if (!isConnectableHostUrl(entry) || history.includes(entry)) continue
    history.push(entry)
    if (history.length >= HOST_HISTORY_LIMIT) break
  }
  return history
}

export function saveHostHistory(storageLike: Pick<Storage, 'getItem' | 'setItem' | 'removeItem'> = window.localStorage, url = '') {
  const cleanUrl = normalizeHostUrlValue(url)
  if (!isConnectableHostUrl(cleanUrl)) {
    storageLike.removeItem(HOST_HISTORY_STORAGE_KEY)
    return []
  }

  const next = [cleanUrl, ...loadHostHistory(storageLike).filter((entry) => entry !== cleanUrl)].slice(0, HOST_HISTORY_LIMIT)
  storageLike.setItem(HOST_HISTORY_STORAGE_KEY, JSON.stringify(next))
  return next
}

export function getQuickPickHostUrls(
  locationLike: Pick<Location, 'origin'> = window.location,
  storageLike: Pick<Storage, 'getItem'> = window.localStorage,
  override = '',
) {
  const current = getPreferredHostUrl(locationLike, override)
  const picks: string[] = []
  for (const entry of [current, ...loadHostHistory(storageLike)]) {
    const cleanEntry = normalizeHostUrlValue(entry)
    if (!isConnectableHostUrl(cleanEntry) || picks.includes(cleanEntry)) continue
    picks.push(cleanEntry)
  }
  return picks
}
