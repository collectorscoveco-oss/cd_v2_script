import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Activity, Gamepad2, Maximize2, Minimize2, RefreshCcw, Save, Settings } from 'lucide-react'
import { createRoot } from 'react-dom/client'
import { ActionIcon, ICON_CHOICES } from './actionIcons'
import { resolveApiBase } from './api-base.js'
import './styles.css'

type DeckButton = {
  index: number
  event: string
  action?: string
  label: string
  category: string
  target?: string
  icon?: string
  color: string
  autoColor?: string
  customColor?: string
}

type Profile = { key: string; name: string }
type Action = { id: string; label: string; category: string; target?: string; editableTarget?: boolean }
type Diagnostics = { summary: string[]; probe: { endpoint?: string; base?: string; ok?: boolean; error?: string; data?: unknown }[] }
type UpdateResponse = { mode: 'git' | 'release'; message: string; snapshot: State; update_url?: string }
type State = {
  profile: { key: string; name: string; theme: { accent: string; panel: string } }
  profiles: Profile[]
  buttons: DeckButton[]
  encoder: { event: string; action?: string; label: string }[]
  specials: { event: string; action?: string; label: string }[]
  actions: Action[]
  log: string[]
  lastAction?: { ok: boolean; event?: string; action?: string; message: string }
}

const API_OVERRIDE_STORAGE_KEY = 'sonardeck.apiBaseOverride'

function createApiClient(base: string) {
  return async function api<T>(path: string, init?: RequestInit): Promise<T> {
    const res = await fetch(base + path, {
      ...init,
      headers: { 'content-type': 'application/json', ...(init?.headers || {}) },
    })
    const data = await res.json()
    if (!data.ok) throw new Error(data.error || 'SonarDeck API error')
    return data.state ?? data
  }
}

function App() {
  const [state, setState] = useState<State | null>(null)
  const [selected, setSelected] = useState<DeckButton | null>(null)
  const [labelDraft, setLabelDraft] = useState('')
  const [actionDraft, setActionDraft] = useState('')
  const [appKey, setAppKey] = useState('')
  const [appPath, setAppPath] = useState('')
  const [appLabel, setAppLabel] = useState('')
  const [hotkeyKey, setHotkeyKey] = useState('discord_mute')
  const [hotkeyLabel, setHotkeyLabel] = useState('Discord Mute')
  const [hotkeyCombo, setHotkeyCombo] = useState('ctrl+alt+shift+m')
  const [targetDraft, setTargetDraft] = useState('')
  const [iconDraft, setIconDraft] = useState('auto')
  const [colorDraft, setColorDraft] = useState('#8b5cf6')
  const [useAutoColor, setUseAutoColor] = useState(true)
  const [setupMode, setSetupMode] = useState<'existing' | 'exe' | 'website' | 'hotkey'>('existing')
  const [error, setError] = useState('')
  const [diagnostics, setDiagnostics] = useState<Diagnostics | null>(null)
  const [tab, setTab] = useState<'mapping' | 'actions' | 'profiles' | 'hardware'>('mapping')
  const [viewMode, setViewMode] = useState<'editor' | 'deck'>('editor')
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [apiBaseOverride, setApiBaseOverride] = useState(() => window.localStorage.getItem(API_OVERRIDE_STORAGE_KEY) ?? '')
  const [apiBaseDraft, setApiBaseDraft] = useState(() => window.localStorage.getItem(API_OVERRIDE_STORAGE_KEY) ?? '')
  const longPressTimer = useRef<number | null>(null)
  const longPressFired = useRef(false)

  useEffect(() => {
    setApiBaseDraft(apiBaseOverride)
  }, [apiBaseOverride])

  const apiBase = useMemo(() => resolveApiBase(window.location, apiBaseOverride), [apiBaseOverride])
  const api = useMemo(() => createApiClient(apiBase), [apiBase])

  useEffect(() => {
    const syncFullscreen = () => setIsFullscreen(Boolean(document.fullscreenElement))
    syncFullscreen()
    document.addEventListener('fullscreenchange', syncFullscreen)
    return () => document.removeEventListener('fullscreenchange', syncFullscreen)
  }, [])

  async function requestDeckFullscreen() {
    if (!document.fullscreenElement && document.documentElement.requestFullscreen) {
      try {
        await document.documentElement.requestFullscreen()
      } catch {
        // Fullscreen is optional; keep deck mode even if the browser blocks it.
      }
    }
  }

  async function enterDeckMode() {
    setViewMode('deck')
    await requestDeckFullscreen()
  }

  async function exitDeckMode() {
    setViewMode('editor')
    if (document.fullscreenElement && document.exitFullscreen) {
      try {
        await document.exitFullscreen()
      } catch {
        // Ignore and continue back to the editor.
      }
    }
  }

  async function toggleFullscreen() {
    try {
      if (document.fullscreenElement && document.exitFullscreen) {
        await document.exitFullscreen()
      } else if (document.documentElement.requestFullscreen) {
        await document.documentElement.requestFullscreen()
      }
    } catch (err) {
      setError(String(err))
    }
  }

  async function refresh() {
    try {
      setError('')
      const next = await api<State>('/state')
      setState(next)
      if (selected) {
        const updated = next.buttons.find((b) => b.event === selected.event)
        if (updated) setSelected(updated)
      }
    } catch (err) {
      setError(String(err))
    }
  }

  function saveApiBaseOverride() {
    const clean = apiBaseDraft.trim()
    setApiBaseOverride(clean)
    if (clean) {
      window.localStorage.setItem(API_OVERRIDE_STORAGE_KEY, clean)
    } else {
      window.localStorage.removeItem(API_OVERRIDE_STORAGE_KEY)
    }
  }

  function clearApiBaseOverride() {
    setApiBaseOverride('')
    setApiBaseDraft('')
    window.localStorage.removeItem(API_OVERRIDE_STORAGE_KEY)
  }

  useEffect(() => {
    refresh()
  }, [apiBase])
  useEffect(() => {
    setLabelDraft(selected?.label ?? '')
    setActionDraft(selected?.action ?? '')
    setIconDraft(selected?.icon || 'auto')
    setColorDraft(selected?.customColor || selected?.autoColor || selected?.color || '#8b5cf6')
    setUseAutoColor(!selected?.customColor)
    setSetupMode('existing')
  }, [selected?.event, selected?.action, selected?.icon, selected?.color, selected?.customColor])

  const accent = state?.profile.theme.accent ?? '#32d3ff'
  const connectionHost = useMemo(() => {
    try {
      return new URL(apiBase).host
    } catch {
      return apiBase
    }
  }, [apiBase])
  const connectionStatus = state ? 'Connected' : error ? 'Disconnected' : 'Connecting...'
  const actionGroups = useMemo(() => {
    const groups: Record<string, Action[]> = {}
    for (const action of state?.actions ?? []) {
      groups[action.category] = groups[action.category] || []
      groups[action.category].push(action)
    }
    return groups
  }, [state])
  const currentAction = useMemo(() => state?.actions.find((action) => action.id === actionDraft), [state, actionDraft])

  useEffect(() => {
    setTargetDraft(currentAction?.target ?? '')
  }, [currentAction?.id, currentAction?.target])

  async function fire(event: string) {
    try {
      setError('')
      const next = await api<State>('/fire', { method: 'POST', body: JSON.stringify({ event }) })
      setState(next)
      if (next.lastAction && !next.lastAction.ok) {
        setError(next.lastAction.message)
      }
    } catch (err) {
      setError(String(err))
    }
  }

  function buttonDown(button: DeckButton) {
    if (button.event !== 'BTN_10_PRESS') return
    longPressFired.current = false
    if (longPressTimer.current) window.clearTimeout(longPressTimer.current)
    longPressTimer.current = window.setTimeout(() => {
      longPressFired.current = true
      fire('BTN_10_LONG')
    }, 650)
  }

  function buttonUp(button: DeckButton) {
    if (button.event !== 'BTN_10_PRESS') return
    if (longPressTimer.current) {
      window.clearTimeout(longPressTimer.current)
      longPressTimer.current = null
    }
  }

  function buttonClick(button: DeckButton) {
    if (button.event === 'BTN_10_PRESS' && longPressFired.current) {
      longPressFired.current = false
      return
    }
    fire(button.event)
  }

  async function switchProfile(profile: string) {
    const next = await api<State>('/profile', { method: 'POST', body: JSON.stringify({ profile }) })
    setState(next)
    setSelected(null)
  }

  async function saveLabel() {
    if (!state || !selected) return
    const next = await api<State>('/label', {
      method: 'POST',
      body: JSON.stringify({ profile: state.profile.key, event: selected.event, label: labelDraft }),
    })
    setState(next)
    setSelected(next.buttons.find((b) => b.event === selected.event) ?? null)
  }

  async function saveIcon() {
    if (!state || !selected) return
    const next = await api<State>('/icon', {
      method: 'POST',
      body: JSON.stringify({ profile: state.profile.key, event: selected.event, icon: iconDraft === 'auto' ? '' : iconDraft }),
    })
    setState(next)
    setSelected(next.buttons.find((b) => b.event === selected.event) ?? null)
  }

  async function saveColor() {
    if (!state || !selected) return
    const next = await api<State>('/color', {
      method: 'POST',
      body: JSON.stringify({ profile: state.profile.key, event: selected.event, color: useAutoColor ? '' : colorDraft }),
    })
    setState(next)
    setSelected(next.buttons.find((b) => b.event === selected.event) ?? null)
  }

  async function saveAppearance() {
    await saveIcon()
    await saveColor()
  }

  async function saveMapping() {
    if (!state || !selected) return
    const next = await api<State>('/mapping', {
      method: 'POST',
      body: JSON.stringify({
        profile: state.profile.key,
        event: selected.event,
        action: actionDraft,
        label: labelDraft,
      }),
    })
    setState(next)
    setSelected(next.buttons.find((b) => b.event === selected.event) ?? null)
  }

  async function clearMapping() {
    if (!state || !selected) return
    const next = await api<State>('/mapping', {
      method: 'POST',
      body: JSON.stringify({ profile: state.profile.key, event: selected.event, action: '', label: '' }),
    })
    setState(next)
    setSelected(next.buttons.find((b) => b.event === selected.event) ?? null)
  }

  async function addManualAppAction(assignToSelected: boolean) {
    if (!state) return
    const key = appKey || appLabel || 'custom_app'
    const label = appLabel || appKey || 'Custom App'
    const next = await api<State>('/app-action', {
      method: 'POST',
      body: JSON.stringify({
        key,
        label,
        command: appPath,
        profile: assignToSelected && selected ? state.profile.key : '',
        event: assignToSelected && selected ? selected.event : '',
        kind: setupMode === 'website' ? 'open' : 'launch',
      }),
    })
    setState(next)
    if (selected) setSelected(next.buttons.find((b) => b.event === selected.event) ?? null)
    const cleanKey = key.trim().toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '')
    setActionDraft(`app.${setupMode === 'website' ? 'open' : 'launch'}.${cleanKey}`)
  }

  async function addHotkeyAction(assignToSelected: boolean) {
    if (!state) return
    const key = hotkeyKey || hotkeyLabel || 'custom_hotkey'
    const label = hotkeyLabel || hotkeyKey || 'Custom Hotkey'
    const next = await api<State>('/hotkey-action', {
      method: 'POST',
      body: JSON.stringify({
        key,
        label,
        combo: hotkeyCombo,
        profile: assignToSelected && selected ? state.profile.key : '',
        event: assignToSelected && selected ? selected.event : '',
      }),
    })
    setState(next)
    if (selected) setSelected(next.buttons.find((b) => b.event === selected.event) ?? null)
    const cleanKey = key.trim().toLowerCase().replace(/[^a-z0-9]+/g, '_').replace(/^_+|_+$/g, '')
    setActionDraft(`hotkey.${cleanKey}`)
  }

  async function saveCurrentActionTarget() {
    if (!currentAction?.editableTarget) return
    const next = await api<State>('/action-target', {
      method: 'POST',
      body: JSON.stringify({ action: currentAction.id, target: targetDraft }),
    })
    setState(next)
  }

  async function quickAssign(action: string, label: string) {
    if (!state || !selected) return
    setActionDraft(action)
    setLabelDraft(label)
    const next = await api<State>('/mapping', {
      method: 'POST',
      body: JSON.stringify({ profile: state.profile.key, event: selected.event, action, label }),
    })
    setState(next)
    setSelected(next.buttons.find((b) => b.event === selected.event) ?? null)
  }

  async function updateApp() {
    const ok = window.confirm('Check for updates now? Dev checkouts run git pull + npm install; release ZIP users open the latest GitHub release page so you can download the updated ZIP and rerun scripts/run_release.bat. On another device, use the bridge/server LAN URL, not 127.0.0.1.')
    if (!ok) return
    try {
      setError('')
      const res = await fetch(apiBase + '/update', {
        method: 'POST',
        headers: { 'content-type': 'application/json' },
        body: JSON.stringify({}),
      })
      const data = await res.json() as { ok: boolean; error?: string; state?: UpdateResponse }
      if (!data.ok) throw new Error(data.error || 'Update failed')
      const payload = data.state
      if (!payload) return
      if (payload.snapshot) setState(payload.snapshot)
      if (payload.mode === 'release' && payload.update_url) {
        const opened = window.open(payload.update_url, '_blank', 'noopener,noreferrer')
        if (!opened) window.location.href = payload.update_url
      }
      window.alert(payload.message)
    } catch (err) {
      setError(String(err))
    }
  }

  async function runDiagnostics() {
    try {
      setError('')
      const next = await api<State & { diagnostics: Diagnostics }>('/diagnostics', { method: 'POST', body: JSON.stringify({}) })
      setState(next)
      setDiagnostics(next.diagnostics)
    } catch (err) {
      setError(String(err))
    }
  }

  const deckMode = viewMode === 'deck'

  return (
    <main className={`app ${deckMode ? 'deckMode' : ''}`} style={{ '--accent': accent } as React.CSSProperties}>
      {!deckMode && (
        <aside className="sidebar">
        <div className="brand">
          <div className="brandIcon"><Gamepad2 size={24} /></div>
          <div>
            <h1>SonarDeck Studio</h1>
            <p>Modern UI prototype</p>
          </div>
        </div>
        <nav>
          {(['mapping', 'actions', 'profiles', 'hardware'] as const).map((item) => (
            <button key={item} className={tab === item ? 'active' : ''} onClick={() => setTab(item)}>
              {item[0].toUpperCase() + item.slice(1)}
            </button>
          ))}
        </nav>
        <button className="ghost" onClick={refresh}><RefreshCcw size={16} /> Refresh bridge</button>
        <button className="ghost updateButton" onClick={updateApp}>Check / Install Updates</button>
        <div className="connectionPanel">
          <div className="sectionTitle compactTitle">
            <h3>Connection</h3>
            <span>Bridge/server URL</span>
          </div>
          <div className="connectionSummary">
            <Activity size={16} />
            <div>
              <b>Bridge/server URL in use</b>
              <code>{apiBase}</code>
            </div>
          </div>
          <label>Bridge/server URL override</label>
          <input
            value={apiBaseDraft}
            onChange={(e) => setApiBaseDraft(e.target.value)}
            placeholder="Optional: http://192.168.1.50:8766, http://192.168.1.50:8765, https://bridge.example.com, or a Cloudflare tunnel"
          />
          <div className="quickRow">
            <button className="ghost" onClick={saveApiBaseOverride}>Save bridge/server URL</button>
            <button className="ghost" onClick={clearApiBaseOverride}>Use current host</button>
          </div>
          <div className="hintBox smallHint">Point this UI at the bridge/server URL. On a release ZIP, that is usually the LAN URL on port 8766, like http://192.168.1.50:8766. On a dev checkout it is usually the bridge port on 8765. The bridge can live on the gaming PC or on a separate server PC; this UI can run wherever you need it. If you are on the release ZIP, the update button will open the latest release page instead of trying to run git pull.</div>
          <div className="hintBox smallHint">Trusted LAN only: the bridge is unauthenticated right now, so do not expose it beyond devices you control.</div>
        </div>
        </aside>
      )}

      <section className="content">
        <header className="topbar">
          <div>
            <span className="eyebrow">{deckMode ? 'Deck mode' : 'Current page'}</span>
            <h2>{state?.profile.name ?? 'Loading...'}</h2>
            {deckMode && <p>Buttons only. Leave the deck with the editor button or fullscreen toggle.</p>}
          </div>
          <div className="topbarActions">
            {deckMode ? (
              <>
                <button className="ghost" onClick={exitDeckMode}><Minimize2 size={16} /> Exit to editor</button>
                <button className="ghost" onClick={toggleFullscreen}>{isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}</button>
              </>
            ) : (
              <>
                <button className="ghost" onClick={enterDeckMode}><Maximize2 size={16} /> Deck mode</button>
                <button className="ghost" onClick={toggleFullscreen}>{isFullscreen ? 'Exit fullscreen' : 'Fullscreen'}</button>
                <button className="ghost" onClick={refresh}><RefreshCcw size={16} /> Refresh bridge</button>
                <button className="ghost updateButton" onClick={updateApp}>Check / Install Updates</button>
              </>
            )}
            <div className="connectionChip">
              <Activity size={14} />
              <div>
                <span>{connectionStatus}</span>
                <b>{connectionHost}</b>
              </div>
            </div>
            <div className="profilePills">
              {state?.profiles.map((profile) => (
                <button key={profile.key} className={profile.key === state.profile.key ? 'selected' : ''} onClick={() => switchProfile(profile.key)}>
                  {profile.name}
                </button>
              ))}
            </div>
          </div>
        </header>

        {error && <div className="error">{error}</div>}
        {!deckMode && state?.lastAction?.message && (
          <div className={state.lastAction.ok ? 'actionStatus ok' : 'actionStatus bad'}>
            Last button: {state.lastAction.message}
          </div>
        )}

        {deckMode ? (
          <section className="deckPanel deckFocusPanel">
            <div className="sectionTitle deckSectionTitle">
              <div>
                <h3>Virtual Deck</h3>
                <span>Touch-friendly deck mode. Only the deck and exit controls stay visible.</span>
              </div>
              <button className="ghost" onClick={exitDeckMode}><Minimize2 size={16} /> Back to editor</button>
            </div>
            <div className="deckGrid deckGridDeckMode">
              {state?.buttons.map((button) => (
                <button
                  key={button.event}
                  className={`deckCard ${button.event === 'BTN_10_PRESS' ? 'playCard' : ''} ${selected?.event === button.event ? 'picked' : ''}`}
                  onMouseDown={() => buttonDown(button)}
                  onMouseUp={() => buttonUp(button)}
                  onMouseLeave={() => buttonUp(button)}
                  onTouchStart={() => buttonDown(button)}
                  onTouchEnd={() => buttonUp(button)}
                  onClick={() => buttonClick(button)}
                  onContextMenu={(e) => { e.preventDefault(); setSelected(button) }}
                  style={{ '--cardColor': button.color } as React.CSSProperties}
                >
                  <div className="stripe" />
                  <div className="cardTop"><span>{button.index}</span><b>{button.category}</b></div>
                  <div className="cardIcon"><ActionIcon action={button.action} label={button.label} category={button.category} target={button.target} icon={button.icon} size={44} /></div>
                  <strong>{button.label}</strong>
                  <small>{button.event.replace('_PRESS', '')}</small>
                </button>
              ))}
            </div>
          </section>
        ) : (
          <>
            <div className="workspace">
          <section className="deckPanel">
            <div className="sectionTitle">
              <h3>Virtual Deck</h3>
              <span>Click to run. Hold Button 10 to switch pages.</span>
            </div>
            <div className="deckGrid">
              {state?.buttons.map((button) => (
                <button
                  key={button.event}
                  className={`deckCard ${button.event === 'BTN_10_PRESS' ? 'playCard' : ''} ${selected?.event === button.event ? 'picked' : ''}`}
                  onMouseDown={() => buttonDown(button)}
                  onMouseUp={() => buttonUp(button)}
                  onMouseLeave={() => buttonUp(button)}
                  onTouchStart={() => buttonDown(button)}
                  onTouchEnd={() => buttonUp(button)}
                  onClick={() => buttonClick(button)}
                  onContextMenu={(e) => { e.preventDefault(); setSelected(button) }}
                  style={{ '--cardColor': button.color } as React.CSSProperties}
                >
                  <div className="stripe" />
                  <div className="cardTop"><span>{button.index}</span><b>{button.category}</b></div>
                  <div className="cardIcon"><ActionIcon action={button.action} label={button.label} category={button.category} target={button.target} icon={button.icon} size={34} /></div>
                  <strong>{button.label}</strong>
                  <small>{button.event.replace('_PRESS', '')}</small>
                </button>
              ))}
            </div>
            <div className="hintBox">Tip: click Button 10 for Play/Pause. Hold Button 10 for Next Page. Right-click any card to manually remap it.</div>
          </section>

          <aside className="inspector">
            {tab === 'mapping' && (
              <>
                <div className="sectionTitle"><h3>Button Setup</h3><span>One place to fix app, website, media, and Sonar buttons.</span></div>
                {selected ? (
                  <div className="formStack">
                    <label>Selected button</label>
                    <div className="readOnly"><b>{selected.event}</b> · currently {selected.category} / {selected.label}</div>

                    <div className="modeGrid">
                      <button className={setupMode === 'existing' ? 'mode active' : 'mode'} onClick={() => setSetupMode('existing')}>Use existing action</button>
                      <button className={setupMode === 'exe' ? 'mode active' : 'mode'} onClick={() => setSetupMode('exe')}>Open an .exe</button>
                      <button className={setupMode === 'website' ? 'mode active' : 'mode'} onClick={() => setSetupMode('website')}>Open website/protocol</button>
                      <button className={setupMode === 'hotkey' ? 'mode active' : 'mode'} onClick={() => setSetupMode('hotkey')}>Keyboard shortcut</button>
                    </div>

                    <div className="quickRow">
                      <button className="ghost" onClick={() => quickAssign('media.play_pause', 'Play/Pause')}>Set Play/Pause</button>
                      <button className="ghost" onClick={() => quickAssign('app.open.spotify', 'Spotify')}>Set Spotify</button>
                    </div>

                    {setupMode === 'existing' && (
                      <>
                        <label>Action</label>
                        <select value={actionDraft} onChange={(e) => setActionDraft(e.target.value)}>
                          <option value="">Unmapped / Do nothing</option>
                          {state?.actions.map((action) => (
                            <option key={action.id} value={action.id}>{action.category} — {action.label} ({action.id})</option>
                          ))}
                        </select>
                        {currentAction?.editableTarget && (
                          <div className="editTargetBox">
                            <label>{currentAction.category === 'Hotkey' ? 'Shortcut keys' : currentAction.category === 'Website' ? 'URL / protocol' : 'App path / command'}</label>
                            <input value={targetDraft} onChange={(e) => setTargetDraft(e.target.value)} />
                            <button className="ghost" onClick={saveCurrentActionTarget}>Save This Action Path/URL</button>
                          </div>
                        )}
                        <label>Button name</label>
                        <input value={labelDraft} onChange={(e) => setLabelDraft(e.target.value)} placeholder="Example: Spotify" />
                        <label>Button icon</label>
                        <div className="iconPickerRow">
                          <div className="iconPreview"><ActionIcon action={actionDraft} label={labelDraft} category={selected.category} target={currentAction?.target} icon={iconDraft} size={24} /></div>
                          <select value={iconDraft} onChange={(e) => setIconDraft(e.target.value)}>
                            {ICON_CHOICES.map((choice) => (
                              <option key={choice.key} value={choice.key}>{choice.label}</option>
                            ))}
                          </select>
                        </div>
                        <label>Button color</label>
                        <div className="colorPickerRow">
                          <input type="color" value={colorDraft} onChange={(e) => { setColorDraft(e.target.value); setUseAutoColor(false) }} />
                          <button className={useAutoColor ? 'mode active' : 'mode'} onClick={() => { setUseAutoColor(true); setColorDraft(selected.autoColor || selected.color) }}>Auto color</button>
                        </div>
                        <button className="primary" onClick={async () => { await saveMapping(); await saveAppearance() }}><Save size={16} /> Save Button</button>
                      </>
                    )}

                    {setupMode === 'exe' && (
                      <>
                        <label>Button name</label>
                        <input value={appLabel} onChange={(e) => setAppLabel(e.target.value)} placeholder="Example: Spotify" />
                        <label>Short action key</label>
                        <input value={appKey} onChange={(e) => setAppKey(e.target.value)} placeholder="Example: spotify" />
                        <label>Full .exe path</label>
                        <input value={appPath} onChange={(e) => setAppPath(e.target.value)} placeholder={'C:\\Users\\crsma\\AppData\\Roaming\\Spotify\\Spotify.exe'} />
                        <label>Button icon</label>
                        <div className="iconPickerRow">
                          <div className="iconPreview"><ActionIcon action={appKey} label={appLabel} category="App" target={appPath} icon={iconDraft} size={24} /></div>
                          <select value={iconDraft} onChange={(e) => setIconDraft(e.target.value)}>
                            {ICON_CHOICES.map((choice) => <option key={choice.key} value={choice.key}>{choice.label}</option>)}
                          </select>
                        </div>
                        <label>Button color</label>
                        <div className="colorPickerRow">
                          <input type="color" value={colorDraft} onChange={(e) => { setColorDraft(e.target.value); setUseAutoColor(false) }} />
                          <button className={useAutoColor ? 'mode active' : 'mode'} onClick={() => { setUseAutoColor(true); setColorDraft(selected.autoColor || selected.color) }}>Auto color</button>
                        </div>
                        <button className="primary" onClick={async () => { await addManualAppAction(true); await saveAppearance() }}>Create App Button</button>
                      </>
                    )}

                    {setupMode === 'website' && (
                      <>
                        <label>Button name</label>
                        <input value={appLabel} onChange={(e) => setAppLabel(e.target.value)} placeholder="Example: Spotify" />
                        <label>Short action key</label>
                        <input value={appKey} onChange={(e) => setAppKey(e.target.value)} placeholder="Example: spotify" />
                        <label>Website URL or app protocol</label>
                        <input value={appPath} onChange={(e) => setAppPath(e.target.value)} placeholder="https://youtube.com or spotify:" />
                        <label>Button icon</label>
                        <div className="iconPickerRow">
                          <div className="iconPreview"><ActionIcon action={appKey} label={appLabel} category="Website" target={appPath} icon={iconDraft} size={24} /></div>
                          <select value={iconDraft} onChange={(e) => setIconDraft(e.target.value)}>
                            {ICON_CHOICES.map((choice) => <option key={choice.key} value={choice.key}>{choice.label}</option>)}
                          </select>
                        </div>
                        <label>Button color</label>
                        <div className="colorPickerRow">
                          <input type="color" value={colorDraft} onChange={(e) => { setColorDraft(e.target.value); setUseAutoColor(false) }} />
                          <button className={useAutoColor ? 'mode active' : 'mode'} onClick={() => { setUseAutoColor(true); setColorDraft(selected.autoColor || selected.color) }}>Auto color</button>
                        </div>
                        <button className="primary" onClick={async () => { await addManualAppAction(true); await saveAppearance() }}>Create Shortcut Button</button>
                        <div className="hintBox smallHint">Note: app protocols like spotify: are shown as App buttons now, not Website buttons.</div>
                      </>
                    )}

                    {setupMode === 'hotkey' && (
                      <>
                        <label>Button name</label>
                        <input value={hotkeyLabel} onChange={(e) => setHotkeyLabel(e.target.value)} placeholder="Example: Discord Mute" />
                        <label>Short action key</label>
                        <input value={hotkeyKey} onChange={(e) => setHotkeyKey(e.target.value)} placeholder="Example: discord_mute" />
                        <label>Shortcut keys</label>
                        <input value={hotkeyCombo} onChange={(e) => setHotkeyCombo(e.target.value)} placeholder="Example: ctrl+alt+shift+m" />
                        <div className="hintBox smallHint">Use keys you can actually press in Discord. Recommended: ctrl+alt+shift+m. Put the same combo in Discord → User Settings → Keybinds → Toggle Mute.</div>
                        <label>Button icon</label>
                        <div className="iconPickerRow">
                          <div className="iconPreview"><ActionIcon action={hotkeyKey} label={hotkeyLabel} category="Hotkey" icon={iconDraft} size={24} /></div>
                          <select value={iconDraft} onChange={(e) => setIconDraft(e.target.value)}>
                            {ICON_CHOICES.map((choice) => <option key={choice.key} value={choice.key}>{choice.label}</option>)}
                          </select>
                        </div>
                        <label>Button color</label>
                        <div className="colorPickerRow">
                          <input type="color" value={colorDraft} onChange={(e) => { setColorDraft(e.target.value); setUseAutoColor(false) }} />
                          <button className={useAutoColor ? 'mode active' : 'mode'} onClick={() => { setUseAutoColor(true); setColorDraft(selected.autoColor || selected.color) }}>Auto color</button>
                        </div>
                        <button className="primary" onClick={async () => { await addHotkeyAction(true); await saveAppearance() }}>Create Hotkey Button</button>
                      </>
                    )}

                    <button className="ghost" onClick={saveLabel}>Save Name Only</button>
                    <button className="ghost" onClick={saveIcon}>Save Icon Only</button>
                    <button className="ghost" onClick={saveColor}>Save Color Only</button>
                    <button className="ghost" onClick={clearMapping}>Clear Button Mapping</button>
                  </div>
                ) : (
                  <div className="empty">Right-click a deck button to open the simple Button Setup panel.</div>
                )}
              </>
            )}

            {tab === 'actions' && (
              <>
                <div className="sectionTitle"><h3>Available Actions</h3><span>Use Mapping to add .exe paths and assign them.</span></div>
                <div className="actionList">
                  {Object.entries(actionGroups).map(([group, actions]) => (
                    <details key={group} open>
                      <summary>{group} · {actions.length}</summary>
                      {actions.map((action) => (
                        <code key={action.id} className="actionCode">
                          <ActionIcon action={action.id} label={action.label} category={action.category} target={action.target} size={16} />
                          <span>{action.id}</span>
                        </code>
                      ))}
                    </details>
                  ))}
                </div>
              </>
            )}

            {tab === 'profiles' && (
              <>
                <div className="sectionTitle"><h3>Pages</h3><span>Switch pages now; create/reorder comes next.</span></div>
                <div className="profileList">
                  {state?.profiles.map((profile) => <button key={profile.key} onClick={() => switchProfile(profile.key)}>{profile.name}</button>)}
                </div>
              </>
            )}

            {tab === 'hardware' && (
              <>
                <div className="sectionTitle"><h3>Hardware Status</h3><span>Ready for the Arduino phase.</span></div>
                <div className="statusCard"><Settings /> Arduino: planned 10 buttons; Button 10 short=Play/Pause, hold=Next Page</div>
                <div className="statusCard"><Activity /> Bridge API: {apiBase}</div>
                <button className="primary" onClick={runDiagnostics}>Run Sonar Diagnostics</button>
                {diagnostics && (
                  <div className="diagnosticsBox">
                    <b>Diagnostics summary</b>
                    {diagnostics.summary.map((line, idx) => <span key={idx}>{line}</span>)}
                    <b>Probe details</b>
                    {diagnostics.probe.map((item, idx) => (
                      <code key={idx}>{item.ok ? 'OK' : 'FAIL'} {item.endpoint} {item.error ? `- ${item.error}` : ''}</code>
                    ))}
                  </div>
                )}
              </>
            )}
          </aside>
        </div>

        <footer className="logBar">
          {(state?.log ?? []).slice(-4).map((line, idx) => <span key={idx}>{line}</span>)}
        </footer>
      </>
        )}
      </section>
    </main>
  )
}

createRoot(document.getElementById('root')!).render(<App />)
