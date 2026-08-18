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

type ActionLike = {
  action?: string
  label?: string
  category?: string
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

function BrandIcon({ icon, size = 30, className }: { icon: SimpleIcon; size?: number; className?: string }) {
  return (
    <svg className={className} width={size} height={size} viewBox="0 0 24 24" role="img" aria-label={icon.title}>
      <path fill="currentColor" d={icon.path} />
    </svg>
  )
}

export function actionIconKey(action?: string, label?: string, category?: string): string {
  const text = `${action ?? ''} ${label ?? ''} ${category ?? ''}`.trim()
  const brand = BRAND_ICON_HINTS.find(([regex]) => regex.test(text))
  if (brand) return brand[1].slug
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

export function ActionIcon({ action, label, category, size = 30, className }: Props) {
  const text = `${action ?? ''} ${label ?? ''} ${category ?? ''}`.trim()
  const brand = BRAND_ICON_HINTS.find(([regex]) => regex.test(text))
  if (brand) return <BrandIcon icon={brand[1]} size={size} className={className} />

  const iconProps = { size, className }
  const key = actionIconKey(action, label, category)
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
