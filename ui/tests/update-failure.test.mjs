import assert from 'node:assert/strict'
import test from 'node:test'

import { GITHUB_LATEST_RELEASE_URL, summarizeUpdateFailure } from '../src/update-failure.js'

test('summarizeUpdateFailure turns fetch failures into bridge messages on dev checkouts', () => {
  const result = summarizeUpdateFailure(new TypeError('Failed to fetch'), 'http://192.168.1.50:8765/api', { port: '5173' })

  assert.equal(result.releaseUrl, '')
  assert.equal(
    result.message,
    "Couldn't reach the bridge/server at http://192.168.1.50:8765. Check that the bridge/server PC is running and that this UI is pointing at the right bridge/server URL.",
  )
})

test('summarizeUpdateFailure opens the GitHub release page from release ui fetch failures', () => {
  const result = summarizeUpdateFailure(new TypeError('Failed to fetch'), 'http://192.168.1.50:8766/api', { port: '8766' })

  assert.equal(result.releaseUrl, GITHUB_LATEST_RELEASE_URL)
  assert.match(result.message, /bridge\/server at http:\/\/192\.168\.1\.50:8766/)
  assert.match(result.message, /Opening the latest GitHub release page now\./)
})

test('summarizeUpdateFailure preserves non-network update errors', () => {
  const result = summarizeUpdateFailure(new Error('Update failed while running git pull --ff-only'), 'http://192.168.1.50:8765/api', { port: '5173' })

  assert.equal(result.releaseUrl, '')
  assert.equal(result.message, 'Update failed while running git pull --ff-only')
})
