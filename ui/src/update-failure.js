export const GITHUB_LATEST_RELEASE_URL = 'https://github.com/collectorscoveco-oss/cd_v2_script/releases/latest'

function getBridgeUrl(apiBase) {
  try {
    return new URL(apiBase).origin
  } catch {
    return String(apiBase ?? '').trim().replace(/\/api$/, '').replace(/\/+$/, '')
  }
}

function isReleaseUi(locationLike = {}) {
  return String(locationLike?.port || '') === '8766'
}

function isNetworkFetchFailure(message) {
  return /failed to fetch|networkerror when attempting to fetch resource|load failed|network request failed/i.test(message)
}

export function summarizeUpdateFailure(error, apiBase, locationLike = {}) {
  const message = error instanceof Error ? error.message : String(error ?? '')
  if (!isNetworkFetchFailure(message)) {
    return { message: message || 'Update failed', releaseUrl: '' }
  }

  const bridgeUrl = getBridgeUrl(apiBase) || String(apiBase ?? '').trim() || 'the bridge/server URL'
  const connectionMessage = `Couldn't reach the bridge/server at ${bridgeUrl}. Check that the bridge/server PC is running and that this UI is pointing at the right bridge/server URL.`

  if (isReleaseUi(locationLike)) {
    return {
      message: `${connectionMessage} Opening the latest GitHub release page now.`,
      releaseUrl: GITHUB_LATEST_RELEASE_URL,
    }
  }

  return { message: connectionMessage, releaseUrl: '' }
}
