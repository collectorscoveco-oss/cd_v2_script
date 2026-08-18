from __future__ import annotations

import logging
import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime

from .actions.registry import ActionContext, ActionRegistry
from .config import load_config
from .main import handle_event, setup_logging
from .profiles import ProfileManager

BUTTON_EVENTS = [f"BTN_{idx:02d}_PRESS" for idx in range(1, 10)]
ENCODER_EVENTS = ["ENC_01_CCW", "ENC_01_PRESS", "ENC_01_CW"]

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
    "sonar.chat.volume_up": "Chat +",
    "sonar.chat.volume_down": "Chat -",
    "sonar.media.volume_up": "Media +",
    "sonar.media.volume_down": "Media -",
    "sonar.aux.volume_up": "Aux +",
    "sonar.aux.volume_down": "Aux -",
    "sonar.mic.toggle_mute": "Mic Mute",
    "hotkey.discord_mute": "Discord Mute",
    "app.launch.discord": "Open Discord",
    "app.launch.steelseries_gg": "Open GG",
    "app.launch.bambu_studio": "Open Bambu",
    "app.open.youtube": "Open YouTube",
}


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
        self.root.title("SonarDeck Virtual Controller")
        self.root.geometry("760x720")
        self.root.minsize(680, 640)

        self.messages: queue.Queue[str] = queue.Queue()
        self.config = load_config(config_path)
        setup_logging(self.config)
        self._install_log_handler()

        self.profiles = ProfileManager(self.config["profiles"])
        self.registry = ActionRegistry(ActionContext(config=self.config, profile_manager=self.profiles))

        self.profile_var = tk.StringVar(value=f"Current profile: {self.profiles.current_name}")
        self.sonar_status_var = tk.StringVar(value="Sonar status: not checked")
        self.deck_buttons: dict[str, ttk.Button] = {}
        self.encoder_buttons: dict[str, ttk.Button] = {}
        self.mode_var = tk.StringVar(value="Mode: ?")
        self.volume_var = tk.StringVar(value="Volumes: ?")

        self._build_ui()
        self._log("Virtual SonarDeck ready. You can test mapped actions without Arduino hardware.")
        self.root.after(150, self._poll_logs)
        self.refresh_sonar_status()

    def _install_log_handler(self) -> None:
        handler = TextQueueHandler(self.messages)
        handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
        logging.getLogger().addHandler(handler)

    def _build_ui(self) -> None:
        self.root.configure(bg="#141922")
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background="#141922")
        style.configure("Title.TLabel", background="#141922", foreground="#f5f7fb", font=("Segoe UI", 20, "bold"))
        style.configure("Sub.TLabel", background="#141922", foreground="#b9c0cc", font=("Segoe UI", 10))
        style.configure("Status.TLabel", background="#1d2430", foreground="#d8dee9", padding=8, font=("Segoe UI", 10))
        style.configure("Deck.TButton", font=("Segoe UI", 11, "bold"), padding=12)
        style.configure("Small.TButton", font=("Segoe UI", 10), padding=8)

        outer = ttk.Frame(self.root, padding=18)
        outer.pack(fill="both", expand=True)

        ttk.Label(outer, text="SonarDeck Virtual Controller", style="Title.TLabel").pack(anchor="w")
        ttk.Label(
            outer,
            text="Use this now as a mouse-click Stream Deck. When the Arduino arrives, run the bridge and the same event mappings will be used by the hardware.",
            style="Sub.TLabel",
            wraplength=700,
        ).pack(anchor="w", pady=(4, 16))

        status_frame = ttk.Frame(outer)
        status_frame.pack(fill="x", pady=(0, 12))
        ttk.Label(status_frame, textvariable=self.profile_var, style="Status.TLabel").pack(side="left", fill="x", expand=True, padx=(0, 8))
        ttk.Button(status_frame, text="Refresh Sonar", style="Small.TButton", command=self.refresh_sonar_status).pack(side="right")

        sonar_frame = ttk.Frame(outer)
        sonar_frame.pack(fill="x", pady=(0, 14))
        ttk.Label(sonar_frame, textvariable=self.sonar_status_var, style="Status.TLabel").pack(fill="x", pady=(0, 4))
        ttk.Label(sonar_frame, textvariable=self.mode_var, style="Status.TLabel").pack(fill="x", pady=(0, 4))
        ttk.Label(sonar_frame, textvariable=self.volume_var, style="Status.TLabel").pack(fill="x")

        grid_frame = ttk.Frame(outer)
        grid_frame.pack(pady=(4, 14))
        for i, event in enumerate(BUTTON_EVENTS):
            btn = ttk.Button(
                grid_frame,
                text="",
                style="Deck.TButton",
                command=lambda e=event: self.fire_event(e),
            )
            btn.grid(row=i // 3, column=i % 3, padx=8, pady=8, sticky="nsew", ipadx=28, ipady=18)
            self.deck_buttons[event] = btn
        for col in range(3):
            grid_frame.columnconfigure(col, weight=1)

        encoder_frame = ttk.LabelFrame(outer, text="Encoder / profile controls")
        encoder_frame.pack(fill="x", pady=(0, 14))
        for i, event in enumerate(ENCODER_EVENTS):
            btn = ttk.Button(encoder_frame, text="", style="Small.TButton", command=lambda e=event: self.fire_event(e))
            btn.grid(row=0, column=i, padx=6, pady=8, sticky="ew")
            self.encoder_buttons[event] = btn
            encoder_frame.columnconfigure(i, weight=1)
        self.profile_switch_button = ttk.Button(encoder_frame, text="", style="Small.TButton", command=lambda: self.fire_event("BTN_08_LONG"))
        self.profile_switch_button.grid(row=1, column=0, columnspan=3, padx=6, pady=(0, 8), sticky="ew")
        self.update_profile_ui()

        log_frame = ttk.LabelFrame(outer, text="Status log")
        log_frame.pack(fill="both", expand=True)
        self.log_text = tk.Text(log_frame, height=10, bg="#0d1117", fg="#d8dee9", insertbackground="#d8dee9", relief="flat", wrap="word")
        self.log_text.pack(side="left", fill="both", expand=True)
        scroll = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scroll.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scroll.set)

    def action_label(self, action: str | None) -> str:
        if not action:
            return "Unmapped"
        if action in ACTION_LABELS:
            return ACTION_LABELS[action]
        if action.startswith("app.launch."):
            return "Open " + action.rsplit(".", 1)[-1].replace("_", " ").title()
        if action.startswith("app.open."):
            return "Open " + action.rsplit(".", 1)[-1].replace("_", " ").title()
        return action.replace(".", " ")

    def update_profile_ui(self) -> None:
        self.profile_var.set(f"Current profile: {self.profiles.current_name}")
        for idx, event in enumerate(BUTTON_EVENTS, start=1):
            action = self.profiles.action_for_event(event)
            label = self.action_label(action)
            self.deck_buttons[event].configure(text=f"{idx}\n{label}")
        for event, btn in self.encoder_buttons.items():
            action = self.profiles.action_for_event(event)
            btn.configure(text=self.action_label(action))
        long_action = self.profiles.action_for_event("BTN_08_LONG")
        self.profile_switch_button.configure(text=f"Long Press B8: {self.action_label(long_action)}")

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
        # Refresh quickly for the virtual deck, then again after SteelSeries has had
        # a moment to persist the new value. This keeps our status strip honest even
        # when the GG app's own sliders lag until its view is refreshed.
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
            for label in ("game", "chat", "media", "mic"):
                channel_id = channels.get(label, label)
                volume = client._extract_volume(settings, channel_id)
                muted = client._extract_muted(settings, channel_id)
                vol_text = "?" if volume is None else f"{round(volume * 100)}%"
                mute_text = " muted" if muted else ""
                parts.append(f"{label}: {vol_text}{mute_text}")
            self.root.after(0, lambda: self._set_sonar_ok(client.api_base, mode, parts, silent))
        except Exception as exc:
            self.root.after(0, lambda: self._set_sonar_error(exc, silent))

    def _set_sonar_ok(self, api_base: str | None, mode: str, parts: list[str], silent: bool) -> None:
        self.sonar_status_var.set(f"Sonar connected: {api_base}")
        self.mode_var.set(f"Mode: {mode}")
        self.volume_var.set("Volumes: " + "   |   ".join(parts))
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
    app = VirtualDeckApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
