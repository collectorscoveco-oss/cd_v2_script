import React, { useEffect, useMemo, useRef, useState } from 'react'
import { Activity, Gamepad2, RefreshCcw, Save, Settings } from 'lucide-react'
import { createRoot } from 'react-dom/client'
import { ActionIcon } from './actionIcons'
import './styles.css'

type DeckButton = {
  index: number
  event: string
  action?: string
  label: string
  category: string
  color: string
}

type Profile = { key: string; name: string }
type Action = { id: string; label: string; category: string; target?: string; editableTarget?: boolean }
type State = {
  profile: { key: string; name: string; theme: { accent: string; panel: string } }
  profiles: Profile[]
  buttons: DeckButton[]
  encoder: { event: string; action?: string; label: string }[]
  specials: { event: string; action?: string; label: string }[]
  actions: Action[]
  log: string[]
}

const API = 'http://127.0.0.1:8765/api'

async function api<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(API + path, {
    ...init,
    headers: { 'content-type': 'application/json', ...(init?.headers || {}) },
  })
  const data = await res.json()
  if (!data.ok) throw new Error(data.error || 'SonarDeck API error')
  return data.state ?? data
}

function App() {
  const [state, setState] = useState<State | null>(null)
  const [selected, setSelected] = useState<DeckButton | null>(null)
  const [labelDraft, setLabelDraft] = useState('')
  const [actionDraft, setActionDraft] = useState('')
  const [appKey, setAppKey] = useState('')
  const [appPath, setAppPath] = useState('')
  const [appLabel, setAppLabel] = useState('')
  const [targetDraft, setTargetDraft] = useState('')
  const [setupMode, setSetupMode] = useState<'existing' | 'exe' | 'website'>('existing')
  const [error, setError] = useState('')
  const [tab, setTab] = useState<'mapping' | 'actions' | 'profiles' | 'hardware'>('mapping')
  const longPressTimer = useRef<number | null>(null)
  const longPressFired = useRef(false)

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

  useEffect(() => {
    refresh()
  }, [])

  useEffect(() => {
    setLabelDraft(selected?.label ?? '')
    setActionDraft(selected?.action ?? '')
    setSetupMode('existing')
  }, [selected?.event, selected?.action])

  const accent = state?.profile.theme.accent ?? '#32d3ff'
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

  return (
    <main className="app" style={{ '--accent': accent } as React.CSSProperties}>
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
      </aside>

      <section className="content">
        <header className="topbar">
          <div>
            <span className="eyebrow">Current page</span>
            <h2>{state?.profile.name ?? 'Loading...'}</h2>
          </div>
          <div className="profilePills">
            {state?.profiles.map((profile) => (
              <button key={profile.key} className={profile.key === state.profile.key ? 'selected' : ''} onClick={() => switchProfile(profile.key)}>
                {profile.name}
              </button>
            ))}
          </div>
        </header>

        {error && <div className="error">{error}</div>}

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
                  <div className="cardIcon"><ActionIcon action={button.action} label={button.label} category={button.category} size={34} /></div>
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
                            <label>{currentAction.category === 'Website' ? 'URL / protocol' : 'App path / command'}</label>
                            <input value={targetDraft} onChange={(e) => setTargetDraft(e.target.value)} />
                            <button className="ghost" onClick={saveCurrentActionTarget}>Save This Action Path/URL</button>
                          </div>
                        )}
                        <label>Button name</label>
                        <input value={labelDraft} onChange={(e) => setLabelDraft(e.target.value)} placeholder="Example: Spotify" />
                        <button className="primary" onClick={saveMapping}><Save size={16} /> Save Button</button>
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
                        <button className="primary" onClick={() => addManualAppAction(true)}>Create App Button</button>
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
                        <button className="primary" onClick={() => addManualAppAction(true)}>Create Shortcut Button</button>
                        <div className="hintBox smallHint">Note: app protocols like spotify: are shown as App buttons now, not Website buttons.</div>
                      </>
                    )}

                    <button className="ghost" onClick={saveLabel}>Save Name Only</button>
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
                          <ActionIcon action={action.id} label={action.label} category={action.category} size={16} />
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
                <div className="statusCard"><Activity /> Bridge API: http://127.0.0.1:8765</div>
              </>
            )}
          </aside>
        </div>

        <footer className="logBar">
          {(state?.log ?? []).slice(-4).map((line, idx) => <span key={idx}>{line}</span>)}
        </footer>
      </section>
    </main>
  )
}

createRoot(document.getElementById('root')!).render(<App />)
