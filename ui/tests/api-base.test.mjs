import assert from 'node:assert/strict'
import test from 'node:test'

import { getDefaultApiBase, normalizeApiBase, resolveApiBase } from '../src/api-base.js'

test('defaults to the current hostname on the bridge port', () => {
  assert.equal(getDefaultApiBase({ hostname: '192.168.1.50' }), 'http://192.168.1.50:8765/api')
  assert.equal(getDefaultApiBase({ hostname: '::1' }), 'http://[::1]:8765/api')
})

test('normalizes override values before appending /api', () => {
  assert.equal(normalizeApiBase(' http://10.0.0.8:9000/api/ '), 'http://10.0.0.8:9000')
  assert.equal(resolveApiBase({ hostname: '192.168.1.50' }, 'http://10.0.0.8:9000'), 'http://10.0.0.8:9000/api')
  assert.equal(resolveApiBase({ hostname: '192.168.1.50' }, 'http://10.0.0.8:9000/api/'), 'http://10.0.0.8:9000/api')
})

test('falls back to the browser host when override is blank', () => {
  assert.equal(resolveApiBase({ hostname: '10.1.2.3' }, ''), 'http://10.1.2.3:8765/api')
})
