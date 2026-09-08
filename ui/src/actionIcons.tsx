import React from 'react'
import {
  Activity,
  AppWindow,
  Bot,
  Clapperboard,
  Gamepad2,
  Globe,
  Keyboard,
  Mic,
  MonitorSpeaker,
  Music2,
  RadioTower,
  Settings,
  SkipBack,
  SkipForward,
  Sparkles,
  Volume2,
  VolumeX,
} from 'lucide-react'
import * as simpleIcons from 'simple-icons'
import {
  siBambulab,
  siDiscord,
  siElgato,
  siEpicgames,
  siGithub,
  siGooglechrome,
  siNvidia,
  siObsstudio,
  siPlex,
  siPlaystation,
  siSpotify,
  siSteam,
  siSteelseries,
  siTwitch,
  siVlcmediaplayer,
  siYoutube,
  type SimpleIcon,
} from 'simple-icons'

const siOrcaSlicer = {
  title: 'OrcaSlicer',
  slug: 'orcaslicer',
  hex: '20b8c7',
  source: 'https://github.com/SoftFever/OrcaSlicer',
  path: 'M12 2.1c2.2 0 4.4.8 6 2.4.5.5.5 1.3-.1 1.7l-1.7 1.1c.9.6 1.8 1.4 2.4 2.5 1.5 2.8.7 6.2-1.9 8.2-2.8 2.2-7.2 2.7-10.6 1.2-2.9-1.2-4.6-3.5-4.2-6 .2-1.4 1-2.6 2.1-3.4.4-.3.9 0 .9.5v1.3c1.4-1.8 3.5-3 5.9-3.2l-.8-2.8c-.2-.7.4-1.3 1.1-1.3h.8Zm1.4 6.5c-3.3 0-6 1.6-7.1 4.1-.3.7-.1 1.5.5 2 2.2 1.6 6.5 1.8 9 .2 1.6-1 2.1-2.8 1.3-4.2-.7-1.3-2.1-2.1-3.7-2.1Zm-3.8 3.5a1 1 0 1 0 0 2.1 1 1 0 0 0 0-2.1Zm5 0a1 1 0 1 0 0 2.1 1 1 0 0 0 0-2.1Z',
} as unknown as SimpleIcon

type ActionLike = {
  action?: string
  label?: string
  category?: string
  target?: string
  icon?: string
}

type Props = ActionLike & {
  size?: number
  className?: string
}

const BRAND_ICON_HINTS: Array<[RegExp, SimpleIcon]> = [
  [/spotify/i, siSpotify],
  [/discord/i, siDiscord],
  [/steelseries|steelseries_gg|\bgg\b|sonar/i, siSteelseries],
  [/youtube|yt\b/i, siYoutube],
  [/obs|obsstudio|stream/i, siObsstudio],
  [/orca|orcaslicer|orca slicer/i, siOrcaSlicer],
  [/bambu|bambu lab|bambu_studio/i, siBambulab],
  [/twitch/i, siTwitch],
  [/steam/i, siSteam],
  [/epic/i, siEpicgames],
  [/playstation|ps5|ps4/i, siPlaystation],
  [/nvidia/i, siNvidia],
  [/github/i, siGithub],
  [/chrome/i, siGooglechrome],
  [/vlc/i, siVlcmediaplayer],
  [/plex/i, siPlex],
  [/elgato|stream deck/i, siElgato],
]

const ALL_BRAND_ICONS = Object.values(simpleIcons).filter((value): value is SimpleIcon => {
  return Boolean(value && typeof value === 'object' && 'title' in value && 'path' in value && 'slug' in value)
})

function BrandIcon({ icon, size = 30, className }: { icon: SimpleIcon; size?: number; className?: string }) {
  return (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" role="img" aria-label={icon.title}>
      <path fill="currentColor" d={icon.path} />
    </svg>
  )
}

function simplify(text: string): string {
  return text
    .toLowerCase()
    .replace(/\.exe\b/g, '')
    .replace(/[_-]+/g, ' ')
    .replace(/\b(app|launch|open|manual|shortcut|button|x64|x86|64bit|32bit)\b/g, ' ')
    .replace(/[^a-z0-9]+/g, ' ')
    .trim()
}

function pathName(path?: string): string {
  if (!path) return ''
  const cleaned = path.replace(/^"|"$/g, '').replace(/\\/g, '/')
  const last = cleaned.split('/').pop() ?? ''
  return last.replace(/\.exe$/i, '')
}

function findBrandIcon(action?: string, label?: string, category?: string, target?: string): SimpleIcon | undefined {
  const text = `${action ?? ''} ${label ?? ''} ${category ?? ''} ${target ?? ''} ${pathName(target)}`.trim()
  const hinted = BRAND_ICON_HINTS.find(([regex]) => regex.test(text))
  if (hinted) return hinted[1]

  const tokens = simplify(text).split(' ').filter((token) => token.length >= 3)
  if (!tokens.length) return undefined

  for (const token of tokens) {
    const exact = ALL_BRAND_ICONS.find((icon) => simplify(icon.title) === token || icon.slug === token)
    if (exact) return exact
  }
  for (const token of tokens) {
    const partial = ALL_BRAND_ICONS.find((icon) => simplify(icon.title).split(' ').includes(token) || icon.slug.includes(token))
    if (partial) return partial
  }
  return undefined
}

const GENERIC_ICON_LABELS: Record<string, string> = {
  'auto': 'Auto',
  'app': 'Generic App',
  'audio': 'Audio / Music',
  'default': 'Sparkle / Default',
  'game': 'Game',
  'hotkey': 'Keyboard Shortcut',
  'mic': 'Microphone',
  'mute': 'Mute',
  'next': 'Next Track',
  'output': 'Output Device',
  'play-pause': 'Play/Pause',
  'previous': 'Previous Track',
  'profile': 'Switch Page',
  'settings': 'Settings',
  'video': 'Video / Streaming',
  'volume': 'Volume',
  'website': 'Website',
}

const PICKER_BRANDS = [
  siSpotify,
  siDiscord,
  siSteelseries,
  siYoutube,
  siObsstudio,
  siOrcaSlicer,
  siBambulab,
  siTwitch,
  siSteam,
  siEpicgames,
  siPlaystation,
  siNvidia,
  siGithub,
  siGooglechrome,
  siVlcmediaplayer,
  siPlex,
  siElgato,
]

export const ICON_CHOICES = [
  ...Object.entries(GENERIC_ICON_LABELS).map(([key, label]) => ({ key, label })),
  ...PICKER_BRANDS.map((icon) => ({ key: icon.slug, label: icon.title })),
]

function iconByKey(key?: string): SimpleIcon | undefined {
  if (!key) return undefined
  return ALL_BRAND_ICONS.find((icon) => icon.slug === key || simplify(icon.title) === simplify(key))
}

export function actionIconKey(action?: string, label?: string, category?: string, target?: string, icon?: string): string {
  if (icon && icon !== 'auto') return icon
  const text = `${action ?? ''} ${label ?? ''} ${category ?? ''} ${target ?? ''} ${pathName(target)}`.trim()
  const brand = findBrandIcon(action, label, category, target)
  if (brand) return brand.slug
  if (/play.?pause|pause|media\.play_pause/i.test(text)) return 'play-pause'
  if (/previous|prev|skip.?back|media\.previous/i.test(text)) return 'previous'
  if (/next|skip.?forward|media\.next/i.test(text)) return 'next'
  if (/mute|volume.?x/i.test(text)) return 'mute'
  if (/volume|windows\.volume|sonar\..*volume/i.test(text)) return 'volume'
  if (/mic|microphone/i.test(text)) return 'mic'
  if (/hotkey|keyboard|shortcut/i.test(text)) return 'hotkey'
  if (/profile|page|switch/i.test(text)) return 'profile'
  if (/website|https?:\/\//i.test(text)) return 'website'
  if (/game|gaming/i.test(text)) return 'game'
  if (/settings|hardware/i.test(text)) return 'settings'
  if (/app|\.exe|launch|open/i.test(text)) return 'app'
  return 'default'
}

export function ActionIcon({ action, label, category, target, icon, size = 30, className }: Props) {
  const overrideBrand = iconByKey(icon)
  if (overrideBrand) return <BrandIcon icon={overrideBrand} size={size} className={className} />
  const brand = findBrandIcon(action, label, category, target)
  if ((!icon || icon === 'auto') && brand) return <BrandIcon icon={brand} size={size} className={className} />

  const iconProps = { size, className }
  const key = actionIconKey(action, label, category, target, icon)
  if (key === 'play-pause') return <Activity {...iconProps} />
  if (key === 'previous') return <SkipBack {...iconProps} />
  if (key === 'next') return <SkipForward {...iconProps} />
  if (key === 'mute') return <VolumeX {...iconProps} />
  if (key === 'volume') return <Volume2 {...iconProps} />
  if (key === 'mic') return <Mic {...iconProps} />
  if (key === 'hotkey') return <Keyboard {...iconProps} />
  if (key === 'profile') return <RadioTower {...iconProps} />
  if (key === 'website') return <Globe {...iconProps} />
  if (key === 'game') return <Gamepad2 {...iconProps} />
  if (key === 'settings') return <Settings {...iconProps} />
  if (key === 'app') return <AppWindow {...iconProps} />
  if (key === 'automation') return <Bot {...iconProps} />
  if (key === 'video') return <Clapperboard {...iconProps} />
  if (key === 'audio') return <Music2 {...iconProps} />
  if (key === 'output') return <MonitorSpeaker {...iconProps} />
  return <Sparkles {...iconProps} />
}
