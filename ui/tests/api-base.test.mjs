import assert from 'node:assert/strict'
import test from 'node:test'

import { getDefaultApiBase, normalizeApiBase, resolveApiBase } from '../src/api-base.js'

test('defaults to the dev bridge port on Vite pages', () => {
  assert.equal(getDefaultApiBase({ hostname: '192.168.1.50', port: '5173', origin: 'http://192.168.1.50:5173' }), 'http://192.168.1.50:8765/api')
  assert.equal(getDefaultApiBase({ hostname: '::1', port: '5173', origin: 'http://[::1]:5173' }), 'http://[::1]:8765/api')
})

test('normalizes override values before appending /api', () => {
  assert.equal(normalizeApiBase(' http://10.0.0.8:9000/api/ '), 'http://10.0.0.8:9000')
  assert.equal(resolveApiBase({ hostname: '192.168.1.50' }, 'http://10.0.0.8:9000'), 'http://10.0.0.8:9000/api')
  assert.equal(resolveApiBase({ hostname: '192.168.1.50' }, 'http://10.0.0.8:9000/api/'), 'http://10.0.0.8:9000/api')
})

test('uses the current origin when the installed app is opened on the release port', () => {
  assert.equal(resolveApiBase({ hostname: '10.1.2.3', port: '8766', origin: 'http://10.1.2.3:8766' }, ''), 'http://10.1.2.3:8766/api')
})

test('falls back to the dev bridge port when the app is opened from vite', () => {
  assert.equal(resolveApiBase({ hostname: '10.1.2.3', port: '5173', origin: 'http://10.1.2.3:5173' }, ''), 'http://10.1.2.3:8765/api')
})
