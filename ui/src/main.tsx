import React, { useEffect, useMemo, useState } from 'react'
import { Activity, Gamepad2, RefreshCcw, Save, Settings, Sparkles, Volume2, Zap } from 'lucide-react'
import { createRoot } from 'react-dom/client'
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
type Action = { id: string; label: string; category: string }
type State = {
  profile: { key: string; name: string; theme: { accent: string; panel: string } }
  profiles: Profile[]
  buttons: DeckButton[]
  encoder: { event: string; action?: string; label: string }[]
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

function categoryIcon(category: string) {
  if (category === 'Sonar') return <Volume2 size={18} />
  if (category === 'Hotkey') return <Zap size={18} />
  if (category === 'Media') return <Activity size={18} />
  return <Sparkles size={18} />
}

function App() {
  const [state, setState] = useState<State | null>(null)
  const [selected, setSelected] = useState<DeckButton | null>(null)
  const [labelDraft, setLabelDraft] = useState('')
  const [error, setError] = useState('')
  const [tab, setTab] = useState<'mapping' | 'actions' | 'profiles' | 'hardware'>('mapping')

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
  }, [selected?.event])

  const accent = state?.profile.theme.accent ?? '#32d3ff'
  const actionGroups = useMemo(() => {
    const groups: Record<string, Action[]> = {}
    for (const action of state?.actions ?? []) {
      groups[action.category] = groups[action.category] || []
      groups[action.category].push(action)
    }
    return groups
  }, [state])

  async function fire(event: string) {
    try {
      setError('')
      const next = await api<State>('/fire', { method: 'POST', body: JSON.stringify({ event }) })
      setState(next)
    } catch (err) {
      setError(String(err))
    }
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
              <span>Click to run. Select a card to edit its display name.</span>
            </div>
            <div className="deckGrid">
              {state?.buttons.map((button) => (
                <button
                  key={button.event}
                  className={`deckCard ${selected?.event === button.event ? 'picked' : ''}`}
                  onClick={() => fire(button.event)}
                  onContextMenu={(e) => { e.preventDefault(); setSelected(button) }}
                  style={{ '--cardColor': button.color } as React.CSSProperties}
                >
                  <div className="stripe" />
                  <div className="cardTop"><span>{button.index}</span><b>{button.category}</b></div>
                  <div className="cardIcon">{categoryIcon(button.category)}</div>
                  <strong>{button.label}</strong>
                  <small>{button.event.replace('_PRESS', '')}</small>
                </button>
              ))}
            </div>
            <div className="hintBox">Tip: left-click fires the button. Right-click selects it for name editing without firing.</div>
          </section>

          <aside className="inspector">
            {tab === 'mapping' && (
              <>
                <div className="sectionTitle"><h3>Button Display Name</h3><span>Change the label shown on the deck.</span></div>
                {selected ? (
                  <div className="formStack">
                    <label>Selected control</label>
                    <div className="readOnly">{selected.event}</div>
                    <label>Display name</label>
                    <input value={labelDraft} onChange={(e) => setLabelDraft(e.target.value)} />
                    <button className="primary" onClick={saveLabel}><Save size={16} /> Save Name</button>
                    <button className="ghost" onClick={() => setLabelDraft('')}>Clear Draft</button>
                  </div>
                ) : (
                  <div className="empty">Right-click a deck button to select it for editing.</div>
                )}
              </>
            )}

            {tab === 'actions' && (
              <>
                <div className="sectionTitle"><h3>Available Actions</h3><span>Read-only in this prototype.</span></div>
                <div className="actionList">
                  {Object.entries(actionGroups).map(([group, actions]) => (
                    <details key={group} open>
                      <summary>{group} · {actions.length}</summary>
                      {actions.map((action) => <code key={action.id}>{action.id}</code>)}
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
                <div className="statusCard"><Settings /> Arduino: not connected yet</div>
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
