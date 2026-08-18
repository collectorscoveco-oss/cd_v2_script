from __future__ import annotations

import logging
import queue
import subprocess
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .actions.registry import ActionContext, ActionRegistry
from .config import load_config, save_config
from .main import handle_event, setup_logging
from .profiles import ProfileManager
from .sounds import notify_profile_switch

BUTTON_EVENTS = [f"BTN_{idx:02d}_PRESS" for idx in range(1, 10)]
ENCODER_EVENTS = ["ENC_01_CCW", "ENC_01_PRESS", "ENC_01_CW"]
EDITABLE_EVENTS = BUTTON_EVENTS + ["BTN_08_LONG"] + ENCODER_EVENTS

ACTION_LABELS = {
    "profile.next": "Switch Page",
    "windows.volume_up": "Windows Vol +",
    "windows.volume_down": "Windows Vol -",
    "windows.mute": "Windows Mute",
    "media.play_pause": "Play/Pause",
    "media.next": "Media Next",
    "media.previous": "Media Prev",
    "sonar.game.volume_up": "Game +",
    "sonar.game.volume_down": "Game -",
    "sonar.game.toggle_mute": "Game Mute",
    "sonar.chat.volume_up": "Chat +",
    "sonar.chat.volume_down": "Chat -",
    "sonar.chat.toggle_mute": "Chat Mute",
    "sonar.media.volume_up": "Media +",
    "sonar.media.volume_down": "Media -",
    "sonar.media.toggle_mute": "Media Mute",
    "sonar.aux.volume_up": "Aux +",
    "sonar.aux.volume_down": "Aux -",
    "sonar.aux.toggle_mute": "Aux Mute",
    "sonar.mic.volume_up": "Mic +",
    "sonar.mic.volume_down": "Mic -",
    "sonar.mic.toggle_mute": "Mic Mute",
    "hotkey.discord_mute": "Discord Mute",
    "hotkey.obs_scene_1": "OBS Scene 1",
    "hotkey.obs_scene_2": "OBS Scene 2",
    "hotkey.obs_record": "OBS Record",
    "hotkey.obs_stream": "OBS Stream",
    "app.launch.discord": "Open Discord",
    "app.launch.steelseries_gg": "Open GG",
    "app.launch.bambu_studio": "Open Bambu",
    "app.launch.obs": "Open OBS",
    "app.launch.spotify": "Open Spotify",
    "app.open.youtube": "Open YouTube",
}

THEMES = {
    "sonar": {"accent": "#32d3ff", "panel": "#102635"},
    "apps": {"accent": "#ff9f43", "panel": "#2d2115"},
    "gaming": {"accent": "#8b5cf6", "panel": "#211936"},
    "streaming": {"accent": "#ef4444", "panel": "#321819"},
    "music": {"accent": "#22c55e", "panel": "#143121"},
    "desktop": {"accent": "#94a3b8", "panel": "#222833"},
}

CATEGORY_COLORS = {
    "Sonar": "#32d3ff",
    "Windows": "#94a3b8",
    "Media": "#22c55e",
    "App": "#ff9f43",
    "Hotkey": "#8b5cf6",
    "Profile": "#facc15",
    "Other": "#64748b",
}

SOUND_MODES = ["off", "beep", "profile_beeps", "terminal_bell", "system", "file", "profile_files", "voice"]


def available_actions(config: dict) -> list[str]:
    actions = set(ACTION_LABELS)
    for key in config.get("actions", {}).get("app", {}).get("launch", {}):
        actions.add(f"app.launch.{key}")
    for key in config.get("actions", {}).get("app", {}).get("open", {}):
        actions.add(f"app.open.{key}")
    for key in config.get("actions", {}).get("hotkey", {}):
        actions.add(f"hotkey.{key}")
    return sorted(actions)


class TextQueueHandler(logging.Handler):
    def __init__(self, messages: queue.Queue[str]):
        super().__init__()
        self.messages = messages

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.messages.put(self.format(record))
        except Exception:
            pass


class VirtualDeckApp:
    def __init__(self, root: tk.Tk, config_path: str | None = None):
        self.root = root
        self.config_path = config_path
        self.root.title("SonarDeck Virtual Controller")
        self.root.geometry("980x820")
        self.root.minsize(820, 720)

        self.messages: queue.Queue[str] = queue.Queue()
        self.config = load_config(config_path)
        setup_logging(self.config)
        self._install_log_handler()

        self.profiles = ProfileManager(self.config["profiles"])
        self.registry = ActionRegistry(ActionContext(config=self.config, profile_manager=self.profiles))

        self.profile_var = tk.StringVar(value=f"Current profile: {self.profiles.current_name}")
        self.sonar_status_var = tk.StringVar(value="Sonar status: not checked")
        self.mode_var = tk.StringVar(value="Mode: ?")
        self.volume_var = tk.StringVar(value="Volumes: ?")
        self.sound_mode_var = tk.StringVar(value=self.config.get("profiles", {}).get("switch_sound", {}).get("mode", "beep"))
        self.selected_profile_var = tk.StringVar(value=self.profiles.current_key)
        self.selected_event_var = tk.StringVar(value="BTN_01_PRESS")
        self.selected_action_var = tk.StringVar(value="")
        self.edit_mode_var = tk.BooleanVar(value=False)
        self.selected_card_event = "BTN_01_PRESS"

        self.deck_buttons: dict[str, dict[str, tk.Widget]] = {}
        self.encoder_buttons: dict[str, ttk.Button] = {}
        self.mixer_bars: dict[str, ttk.Progressbar] = {}
        self.mixer_labels: dict[str, tk.StringVar] = {}

        self._build_ui()
        self._bind_shortcuts()
        self._log("Virtual SonarDeck ready. F1-F9 trigger buttons. Ctrl+Alt+1..9 also work while focused.")
        self.root.after(150, self._poll_logs)
        self.refresh_sonar_status()

    def _install_log_handler(self) -> None:
        handler = TextQueueHandler(self.messages)
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logging.getLogger().addHandler(handler)

    def _build_ui(self) -> None:
        self.root.configure(bg="#141922")
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass
        self.style.configure("TFrame", background="#141922")
        self.style.configure("TLabelframe", background="#141922", foreground="#d8dee9")
        self.style.configure("TLabelframe.Label", background="#141922", foreground="#d8dee9")
        self.style.configure("Title.TLabel", background="#141922", foreground="#f5f7fb", font=("Segoe UI", 20, "bold"))
        self.style.configure("Sub.TLabel", background="#141922", foreground="#b9c0cc", font=("Segoe UI", 10))
        self.style.configure("Status.TLabel", background="#1d2430", foreground="#d8dee9", padding=8, font=("Segoe UI", 10))
        self.style.configure("Deck.TButton", font=("Segoe UI", 11, "bold"), padding=12)
        self.style.configure("Small.TButton", font=("Segoe UI", 10), padding=8)
        self.style.configure("Accent.Horizontal.TProgressbar", troughcolor="#0d1117", background="#32d3ff")

        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="SonarDeck Virtual Controller", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            outer,
            text="Software playground now; same event mappings later when the Arduino is plugged in.",
            style="Sub.TLabel",
            wraplength=900,
        ).pack(anchor="w", pady=(4, 10))

        self._build_toolbar(outer)

        top = ttk.Frame(outer)
        top.pack(fill="x", pady=(0, 12))
        ttk.Label(top, textvariable=self.profile_var, style="Status.TLabel").pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(top, text="Refresh Sonar", style="Small.TButton", command=self.refresh_sonar_status).pack(side="right")

        sonar_frame = ttk.LabelFrame(outer, text="Live Sonar mixer")
        sonar_frame.pack(fill="x", pady=(0, 14))
        ttk.Label(sonar_frame, textvariable=self.sonar_status_var, style="Status.TLabel").pack(fill="x", pady=(6, 4), padx=8)
        ttk.Label(sonar_frame, textvariable=self.mode_var, style="Status.TLabel").pack(fill="x", pady=(0, 4), padx=8)
        for channel in ("game", "chat", "media", "mic"):
            row = ttk.Frame(sonar_frame)
            row.pack(fill="x", padx=8, pady=3)
            var = tk.StringVar(value=f"{channel}: ?")
            self.mixer_labels[channel] = var
            ttk.Label(row, textvariable=var, width=16).pack(side="left")
            bar = ttk.Progressbar(row, orient="horizontal", mode="determinate", maximum=100, style="Accent.Horizontal.TProgressbar")
            bar.pack(side="left", fill="x", expand=True, padx=(8, 0))
            self.mixer_bars[channel] = bar
        ttk.Label(sonar_frame, textvariable=self.volume_var, style="Status.TLabel").pack(fill="x", pady=(4, 8), padx=8)

        middle = ttk.Frame(outer)
        middle.pack(fill="both", expand=True)

        deck_col = ttk.Frame(middle)
        deck_col.pack(side="left", fill="both", expand=True, padx=(0, 12))
        grid_frame = ttk.LabelFrame(deck_col, text="Virtual deck buttons")
        grid_frame.pack(fill="x", pady=(0, 14))
        for i, event in enumerate(BUTTON_EVENTS):
            self._create_deck_card(grid_frame, event, i)
        for col in range(3):
            grid_frame.columnconfigure(col, weight=1)

        encoder_frame = ttk.LabelFrame(deck_col, text="Encoder / profile controls")
        encoder_frame.pack(fill="x", pady=(0, 14))
        for i, event in enumerate(ENCODER_EVENTS):
            btn = ttk.Button(encoder_frame, text="", style="Small.TButton", command=lambda e=event: self.fire_event(e))
            btn.grid(row=0, column=i, padx=6, pady=8, sticky="ew")
            self.encoder_buttons[event] = btn
            encoder_frame.columnconfigure(i, weight=1)
        self.profile_switch_button = ttk.Button(encoder_frame, text="", style="Small.TButton", command=lambda: self.fire_event("BTN_08_LONG"))
        self.profile_switch_button.grid(row=1, column=0, columnspan=3, padx=6, pady=(0, 8), sticky="ew")

        side_col = ttk.Frame(middle)
        side_col.pack(side="right", fill="both", expand=True)
        self._build_sound_panel(side_col)
        self._build_editor_panel(side_col)

        log_frame = ttk.LabelFrame(outer, text="Status log")
        log_frame.pack(fill="both", expand=True, pady=(12, 0))
        self.log_text = tk.Text(log_frame, height=8, bg="#0d1117", fg="#d8dee9", insertbackground="#d8dee9", relief="flat", wrap="word")
        self.log_text.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scroll.set)

        self.update_profile_ui()

    def _build_toolbar(self, parent: ttk.Frame) -> None:
        bar = tk.Frame(parent, bg="#0d1117", highlightthickness=1, highlightbackground="#243041")
        bar.pack(fill="x", pady=(0, 12))
        inner = tk.Frame(bar, bg="#0d1117")
        inner.pack(fill="x", padx=8, pady=6)
        tk.Label(inner, text="Toolbar", bg="#0d1117", fg="#94a3b8", font=("Segoe UI", 9, "bold")).pack(side="left", padx=(0, 10))
        ttk.Button(inner, text="Check for Updates", style="Small.TButton", command=self.check_for_updates).pack(side="left", padx=4)
        ttk.Button(inner, text="Refresh Sonar", style="Small.TButton", command=self.refresh_sonar_status).pack(side="left", padx=4)
        ttk.Button(inner, text="Test Profile Sound", style="Small.TButton", command=self.test_profile_sound).pack(side="left", padx=4)
        ttk.Button(inner, text="Open Config Folder", style="Small.TButton", command=self.open_config_folder).pack(side="left", padx=4)
        ttk.Checkbutton(inner, text="Edit Mapping Mode", variable=self.edit_mode_var, command=self.update_profile_ui).pack(side="right", padx=4)

    def repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def check_for_updates(self) -> None:
        self._log("Checking GitHub for SonarDeck updates...")
        threading.Thread(target=self._check_for_updates_worker, daemon=True).start()

    def _check_for_updates_worker(self) -> None:
        repo = self.repo_root()
        try:
            subprocess.run(["git", "fetch", "--quiet"], cwd=repo, check=True, capture_output=True, text=True, timeout=45)
            upstream = subprocess.run(["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{u}"], cwd=repo, check=False, capture_output=True, text=True, timeout=10)
            if upstream.returncode != 0:
                message = "Could not check updates because this branch has no upstream tracking branch."
            else:
                counts = subprocess.run(["git", "rev-list", "--left-right", "--count", "HEAD...@{u}"], cwd=repo, check=True, capture_output=True, text=True, timeout=10)
                ahead, behind = [int(x) for x in counts.stdout.strip().split()]
                branch = upstream.stdout.strip()
                if behind > 0:
                    message = f"Update available: your copy is {behind} commit(s) behind {branch}. Close SonarDeck, then run git pull."
                elif ahead > 0:
                    message = f"You are up to date with {branch}. You also have {ahead} local commit(s) not on GitHub."
                else:
                    message = f"You are up to date with {branch}."
        except Exception as exc:
            message = f"Update check failed: {exc}"
        self.root.after(0, lambda: self._show_update_result(message))

    def _show_update_result(self, message: str) -> None:
        self._log(message)
        messagebox.showinfo("SonarDeck Updates", message)

    def open_config_folder(self) -> None:
        folder = self.repo_root() / "bridge"
        try:
            if sys.platform.startswith("win"):
                subprocess.Popen(["explorer", str(folder)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(folder)])
            else:
                subprocess.Popen(["xdg-open", str(folder)])
            self._log(f"Opened config folder: {folder}")
        except Exception as exc:
            self._log(f"Could not open config folder: {exc}")
            messagebox.showwarning("SonarDeck", f"Could not open config folder.\n\n{folder}\n\n{exc}")

    def _create_deck_card(self, parent: ttk.LabelFrame, event: str, index: int) -> None:
        outer = tk.Frame(parent, bg="#0b0f17", highlightthickness=1, highlightbackground="#2d3748", bd=0)
        outer.grid(row=index // 3, column=index % 3, padx=8, pady=8, sticky="nsew", ipadx=0, ipady=0)
        outer.configure(width=150, height=118)
        outer.grid_propagate(False)

        stripe = tk.Frame(outer, bg="#32d3ff", width=5)
        stripe.pack(side="left", fill="y")
        body = tk.Frame(outer, bg="#111827")
        body.pack(side="left", fill="both", expand=True)

        top = tk.Frame(body, bg="#111827")
        top.pack(fill="x", padx=10, pady=(8, 0))
        number = tk.Label(top, text=str(index + 1), bg="#111827", fg="#94a3b8", font=("Segoe UI", 9, "bold"))
        number.pack(side="left")
        category = tk.Label(top, text="", bg="#1f2937", fg="#e5e7eb", font=("Segoe UI", 7, "bold"), padx=6, pady=1)
        category.pack(side="right")

        label = tk.Label(body, text="", bg="#111827", fg="#f8fafc", font=("Segoe UI", 13, "bold"), wraplength=118, justify="center")
        label.pack(fill="both", expand=True, padx=8, pady=(4, 0))
        hint = tk.Label(body, text="", bg="#111827", fg="#64748b", font=("Segoe UI", 8))
        hint.pack(fill="x", padx=8, pady=(0, 8))

        widgets = {"outer": outer, "stripe": stripe, "body": body, "top": top, "number": number, "category": category, "label": label, "hint": hint}
        self.deck_buttons[event] = widgets
        for widget in widgets.values():
            widget.bind("<Button-1>", lambda _e, ev=event: self.handle_deck_card_click(ev))
            widget.bind("<Enter>", lambda _e, ev=event: self.set_deck_card_hover(ev, True))
            widget.bind("<Leave>", lambda _e, ev=event: self.set_deck_card_hover(ev, False))

    def action_category(self, action: str | None) -> str:
        if not action:
            return "Other"
        if action.startswith("sonar."):
            return "Sonar"
        if action.startswith("windows."):
            return "Windows"
        if action.startswith("media."):
            return "Media"
        if action.startswith("app."):
            return "App"
        if action.startswith("hotkey."):
            return "Hotkey"
        if action.startswith("profile."):
            return "Profile"
        return "Other"

    def handle_deck_card_click(self, event: str) -> None:
        if self.edit_mode_var.get():
            self.selected_card_event = event
            self.selected_profile_var.set(str(self.profiles.current_key))
            self.selected_event_var.set(event)
            self.load_editor_action()
            self.update_profile_ui()
            self._log(f"Editing {self.profiles.current_name} / {event}")
            return
        self.fire_event(event)

    def set_deck_card_hover(self, event: str, hover: bool) -> None:
        # Keep hover deliberately subtle. Earlier versions changed several nested
        # widget colors on every enter/leave event, which looked flickery/weird
        # when moving across text inside the same card. Now hover only changes
        # the pointer and leaves the card visual stable.
        if event not in self.deck_buttons:
            return
        cursor = "hand2" if hover else ""
        for widget in self.deck_buttons[event].values():
            try:
                widget.configure(cursor=cursor)
            except tk.TclError:
                pass

    def update_deck_card(self, event: str, index: int, action: str | None) -> None:
        widgets = self.deck_buttons[event]
        label = self.action_label(action)
        category = self.action_category(action)
        accent = CATEGORY_COLORS.get(category, CATEGORY_COLORS["Other"])
        selected = self.edit_mode_var.get() and event == self.selected_card_event
        bg = "#1e293b" if selected else "#111827"
        border = accent if selected else "#334155"
        hint = "✎ Click to edit" if self.edit_mode_var.get() else event.replace("_PRESS", "")
        if selected:
            hint = "Selected for edit"
        widgets["stripe"].configure(bg=accent)
        widgets["outer"].configure(highlightbackground=border, highlightthickness=2 if selected else 1)
        widgets["body"].configure(bg=bg)
        widgets["top"].configure(bg=bg)
        widgets["number"].configure(text=str(index), bg=bg, fg=accent)
        widgets["category"].configure(text=category.upper(), bg=accent, fg="#0b0f17")
        widgets["label"].configure(text=label, bg=bg)
        widgets["hint"].configure(text=hint, bg=bg, fg="#facc15" if selected else "#64748b")

    def _build_sound_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Profile switch audio")
        frame.pack(fill="x", pady=(0, 12))
        ttk.Label(frame, text="Mode:").grid(row=0, column=0, sticky="w", padx=8, pady=8)
        combo = ttk.Combobox(frame, values=SOUND_MODES, textvariable=self.sound_mode_var, state="readonly")
        combo.grid(row=0, column=1, sticky="ew", padx=8, pady=8)
        combo.bind("<<ComboboxSelected>>", lambda _e: self.save_sound_mode())
        ttk.Button(frame, text="Test Current", command=self.test_profile_sound).grid(row=1, column=0, padx=8, pady=(0, 8), sticky="ew")
        ttk.Button(frame, text="Choose WAV", command=self.choose_sound_file).grid(row=1, column=1, padx=8, pady=(0, 8), sticky="ew")
        ttk.Label(frame, text="Modes: profile_beeps = different beep per page; voice = says page name on Windows.", style="Sub.TLabel", wraplength=360).grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
        frame.columnconfigure(1, weight=1)

    def _build_editor_panel(self, parent: ttk.Frame) -> None:
        frame = ttk.LabelFrame(parent, text="Button/profile editor")
        frame.pack(fill="x")
        ttk.Label(frame, text="Profile").grid(row=0, column=0, sticky="w", padx=8, pady=6)
        profile_values = list(self.config["profiles"]["items"].keys())
        profile_combo = ttk.Combobox(frame, values=profile_values, textvariable=self.selected_profile_var, state="readonly")
        profile_combo.grid(row=0, column=1, sticky="ew", padx=8, pady=6)
        profile_combo.bind("<<ComboboxSelected>>", lambda _e: self.load_editor_action())

        ttk.Label(frame, text="Control").grid(row=1, column=0, sticky="w", padx=8, pady=6)
        event_combo = ttk.Combobox(frame, values=EDITABLE_EVENTS, textvariable=self.selected_event_var, state="readonly")
        event_combo.grid(row=1, column=1, sticky="ew", padx=8, pady=6)
        event_combo.bind("<<ComboboxSelected>>", lambda _e: self.load_editor_action())

        ttk.Label(frame, text="Action").grid(row=2, column=0, sticky="w", padx=8, pady=6)
        self.action_combo = ttk.Combobox(frame, values=available_actions(self.config), textvariable=self.selected_action_var)
        self.action_combo.grid(row=2, column=1, sticky="ew", padx=8, pady=6)

        ttk.Checkbutton(frame, text="Edit Mapping Mode", variable=self.edit_mode_var, command=self.update_profile_ui).grid(row=3, column=0, columnspan=2, padx=8, pady=8, sticky="ew")
        ttk.Button(frame, text="Save Mapping", command=self.save_mapping).grid(row=4, column=0, padx=8, pady=6, sticky="ew")
        ttk.Button(frame, text="Test Selected Action", command=self.test_selected_mapping).grid(row=4, column=1, padx=8, pady=6, sticky="ew")
        ttk.Button(frame, text="Switch To Selected Profile", command=self.switch_to_selected_profile).grid(row=5, column=0, columnspan=2, padx=8, pady=6, sticky="ew")
        ttk.Label(frame, text="Normal: deck buttons run actions. Edit Mapping Mode: clicking a deck button selects it for editing. F1-F9 still trigger buttons while focused.", style="Sub.TLabel", wraplength=360).grid(row=6, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
        frame.columnconfigure(1, weight=1)
        self.load_editor_action()

    def _bind_shortcuts(self) -> None:
        for idx, event in enumerate(BUTTON_EVENTS, start=1):
            self.root.bind_all(f"<F{idx}>", lambda _e, ev=event: self.fire_event(ev))
            self.root.bind_all(f"<Control-Alt-Key-{idx}>", lambda _e, ev=event: self.fire_event(ev))
        self.root.bind_all("<Control-Alt-Key-0>", lambda _e: self.fire_event("BTN_08_LONG"))
        self.root.bind_all("<Control-Alt-Right>", lambda _e: self.fire_event("ENC_01_CW"))
        self.root.bind_all("<Control-Alt-Left>", lambda _e: self.fire_event("ENC_01_CCW"))

    def action_label(self, action: str | None) -> str:
        if not action:
            return "Unmapped"
        if action in ACTION_LABELS:
            return ACTION_LABELS[action]
        if action.startswith("app.launch."):
            return "Open " + action.rsplit(".", 1)[-1].replace("_", " ").title()
        if action.startswith("app.open."):
            return "Open " + action.rsplit(".", 1)[-1].replace("_", " ").title()
        if action.startswith("hotkey."):
            return "Hotkey " + action.rsplit(".", 1)[-1].replace("_", " ").title()
        return action.replace(".", " ")

    def update_profile_ui(self) -> None:
        current_key = str(self.profiles.current_key)
        theme = THEMES.get(current_key, THEMES["desktop"])
        self.style.configure("Accent.Horizontal.TProgressbar", background=theme["accent"])
        self.style.configure("Status.TLabel", background=theme["panel"], foreground="#f5f7fb", padding=8, font=("Segoe UI", 10))
        self.profile_var.set(f"Current profile: {self.profiles.current_name}")
        self.selected_profile_var.set(current_key)
        for idx, event in enumerate(BUTTON_EVENTS, start=1):
            action = self.profiles.action_for_event(event)
            self.update_deck_card(event, idx, action)
        for event, btn in self.encoder_buttons.items():
            btn.configure(text=self.action_label(self.profiles.action_for_event(event)))
        self.profile_switch_button.configure(text=f"Long Press B8: {self.action_label(self.profiles.action_for_event('BTN_08_LONG'))}")
        self.load_editor_action()

    def load_editor_action(self) -> None:
        profile = self.selected_profile_var.get()
        event = self.selected_event_var.get()
        action = self.config["profiles"]["items"].get(profile, {}).get("events", {}).get(event, "")
        self.selected_action_var.set(action)

    def save_mapping(self) -> None:
        profile = self.selected_profile_var.get()
        event = self.selected_event_var.get()
        action = self.selected_action_var.get().strip()
        if not profile or not event or not action:
            messagebox.showwarning("SonarDeck", "Choose a profile, control, and action first.")
            return
        self.config["profiles"]["items"][profile].setdefault("events", {})[event] = action
        self.profiles.items[profile]["events"][event] = action
        save_config(self.config, self.config_path)
        self.update_profile_ui()
        self._log(f"Saved mapping: {profile} {event} -> {action}")

    def test_selected_mapping(self) -> None:
        profile = self.selected_profile_var.get()
        event = self.selected_event_var.get()
        action = self.config["profiles"]["items"].get(profile, {}).get("events", {}).get(event)
        if not action:
            messagebox.showwarning("SonarDeck", "Selected control has no mapped action to test.")
            return
        self._log(f"Testing selected mapping: {profile} / {event} -> {action}")
        threading.Thread(target=self._test_action_worker, args=(action,), daemon=True).start()

    def _test_action_worker(self, action: str) -> None:
        try:
            self.registry.execute(action)
        except Exception as exc:
            self._log(f"Test action failed: {exc}")
        self.root.after(0, self._after_action)

    def switch_to_selected_profile(self) -> None:
        profile = self.selected_profile_var.get()
        if profile in self.profiles.items:
            self.profiles.current_key = profile
            notify_profile_switch(self.config.get("profiles", {}).get("switch_sound", {}), self.profiles.current_name, self.profiles.current_key)
            self.update_profile_ui()
            self.refresh_sonar_status(silent=True)

    def save_sound_mode(self) -> None:
        sound_cfg = self.config.setdefault("profiles", {}).setdefault("switch_sound", {})
        sound_cfg["enabled"] = self.sound_mode_var.get() != "off"
        sound_cfg["mode"] = self.sound_mode_var.get()
        save_config(self.config, self.config_path)
        self._log(f"Profile switch sound mode set to {self.sound_mode_var.get()}")

    def choose_sound_file(self) -> None:
        path = filedialog.askopenfilename(title="Choose profile switch WAV", filetypes=[("WAV files", "*.wav"), ("All files", "*.*")])
        if not path:
            return
        sound_cfg = self.config.setdefault("profiles", {}).setdefault("switch_sound", {})
        sound_cfg["file"] = path
        if self.sound_mode_var.get() not in {"file", "profile_files"}:
            self.sound_mode_var.set("file")
            sound_cfg["mode"] = "file"
            sound_cfg["enabled"] = True
        save_config(self.config, self.config_path)
        self._log(f"Profile switch sound file set: {path}")
        self.test_profile_sound()

    def test_profile_sound(self) -> None:
        self.save_sound_mode()
        notify_profile_switch(self.config.get("profiles", {}).get("switch_sound", {}), self.profiles.current_name, self.profiles.current_key)

    def _log(self, message: str) -> None:
        stamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert("end", f"[{stamp}] {message}\n")
        self.log_text.see("end")

    def _poll_logs(self) -> None:
        while True:
            try:
                msg = self.messages.get_nowait()
            except queue.Empty:
                break
            self._log(msg)
        self.root.after(150, self._poll_logs)

    def fire_event(self, event: str) -> None:
        action = self.profiles.action_for_event(event)
        self._log(f"{event} -> {action or 'unmapped'}")
        threading.Thread(target=self._fire_event_worker, args=(event,), daemon=True).start()

    def _fire_event_worker(self, event: str) -> None:
        handle_event(event, self.profiles, self.registry)
        self.root.after(0, self._after_action)

    def _after_action(self) -> None:
        self.update_profile_ui()
        self.refresh_sonar_status(silent=True)
        self.root.after(750, lambda: self.refresh_sonar_status(silent=True))

    def refresh_sonar_status(self, silent: bool = False) -> None:
        threading.Thread(target=self._refresh_sonar_worker, args=(silent,), daemon=True).start()

    def _refresh_sonar_worker(self, silent: bool) -> None:
        try:
            client = self.registry.ctx.sonar_client
            if client is None:
                raise RuntimeError("Sonar client is not initialized")
            mode = client.get_mode()
            settings = client.get_volume_settings()
            channels = client.channels
            parts = []
            ui_rows = []
            for label in ("game", "chat", "media", "mic"):
                channel_id = channels.get(label, label)
                volume = client._extract_volume(settings, channel_id)
                muted = client._extract_muted(settings, channel_id)
                percent = None if volume is None else int(round(volume * 100))
                vol_text = "?" if percent is None else f"{percent}%"
                mute_text = " muted" if muted else ""
                parts.append(f"{label}: {vol_text}{mute_text}")
                ui_rows.append((label, percent, muted))
            self.root.after(0, lambda: self._set_sonar_ok(client.api_base, mode, parts, ui_rows, silent))
        except Exception as exc:
            self.root.after(0, lambda: self._set_sonar_error(exc, silent))

    def _set_sonar_ok(self, api_base: str | None, mode: str, parts: list[str], ui_rows: list[tuple[str, int | None, bool | None]], silent: bool) -> None:
        self.sonar_status_var.set(f"Sonar connected: {api_base}")
        self.mode_var.set(f"Mode: {mode}")
        self.volume_var.set("Volumes: " + "   |   ".join(parts))
        for label, percent, muted in ui_rows:
            self.mixer_bars[label]["value"] = 0 if percent is None else percent
            suffix = " muted" if muted else ""
            self.mixer_labels[label].set(f"{label.title()}: {'?' if percent is None else str(percent) + '%'}{suffix}")
        if not silent:
            self._log("Sonar connection OK")

    def _set_sonar_error(self, exc: Exception, silent: bool) -> None:
        self.sonar_status_var.set("Sonar status: not connected")
        self.mode_var.set("Mode: ?")
        self.volume_var.set("Volumes: ?")
        if not silent:
            self._log(f"Sonar check failed: {exc}")
            messagebox.showwarning("SonarDeck", f"Could not read Sonar yet. Make sure SteelSeries GG/Sonar is open.\n\n{exc}")


def main() -> None:
    root = tk.Tk()
    VirtualDeckApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
