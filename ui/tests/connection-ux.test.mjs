import assert from 'node:assert/strict'
import test from 'node:test'

import {
  getPreferredHostUrl,
  getQuickPickHostUrls,
  loadHostHistory,
  saveHostHistory,
  HOST_HISTORY_STORAGE_KEY,
} from '../src/connection-ux.js'

function makeStorage(seed = {}) {
  const data = new Map(Object.entries(seed))
  return {
    getItem(key) {
      return data.has(key) ? String(data.get(key)) : null
    },
    setItem(key, value) {
      data.set(key, String(value))
    },
    removeItem(key) {
      data.delete(key)
    },
    dump() {
      return Object.fromEntries(data.entries())
    },
  }
}

test('getPreferredHostUrl uses a saved override when present', () => {
  assert.equal(
    getPreferredHostUrl({ origin: 'http://10.0.0.10:5173' }, ' http://10.0.0.25:8766/api/ '),
    'http://10.0.0.25:8766',
  )
})

test('getPreferredHostUrl falls back to the current page origin', () => {
  assert.equal(getPreferredHostUrl({ origin: 'http://10.0.0.10:5173' }, ''), 'http://10.0.0.10:5173')
})

test('getPreferredHostUrl ignores loopback origins when no better host exists', () => {
  const storage = makeStorage({ [HOST_HISTORY_STORAGE_KEY]: JSON.stringify(['http://10.0.0.25:8766']) })

  assert.equal(getPreferredHostUrl({ origin: 'http://127.0.0.1:5173' }, '', storage), 'http://10.0.0.25:8766')
  assert.deepEqual(getQuickPickHostUrls({ origin: 'http://127.0.0.1:5173' }, storage, ''), ['http://10.0.0.25:8766'])
})

test('saveHostHistory stores the most recent host first and dedupes entries', () => {
  const storage = makeStorage({ [HOST_HISTORY_STORAGE_KEY]: JSON.stringify(['http://10.0.0.10:8766', 'http://10.0.0.11:8766']) })

  const next = saveHostHistory(storage, 'http://10.0.0.11:8766/api/')

  assert.deepEqual(next, ['http://10.0.0.11:8766', 'http://10.0.0.10:8766'])
  assert.equal(storage.getItem(HOST_HISTORY_STORAGE_KEY), JSON.stringify(['http://10.0.0.11:8766', 'http://10.0.0.10:8766']))
})

test('saveHostHistory ignores loopback urls', () => {
  const storage = makeStorage()

  assert.deepEqual(saveHostHistory(storage, 'http://127.0.0.1:8766'), [])
  assert.equal(storage.getItem(HOST_HISTORY_STORAGE_KEY), null)
})

test('loadHostHistory ignores malformed storage contents', () => {
  const storage = makeStorage({ [HOST_HISTORY_STORAGE_KEY]: '{not json' })

  assert.deepEqual(loadHostHistory(storage), [])
})

test('getQuickPickHostUrls includes the current page origin first', () => {
  const storage = makeStorage({ [HOST_HISTORY_STORAGE_KEY]: JSON.stringify(['http://10.0.0.25:8766', 'http://10.0.0.10:8766']) })

  assert.deepEqual(
    getQuickPickHostUrls({ origin: 'http://10.0.0.42:5173' }, storage, ''),
    ['http://10.0.0.42:5173', 'http://10.0.0.25:8766', 'http://10.0.0.10:8766'],
  )
})
