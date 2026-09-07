# 🎮 ConsoleDeck

ConsoleDeck is a simple graphical interface that allows you to configure up to 9 buttons to launch websites or executable files with a click.  
Ideal for creating your own customizable macro deck or personal launcher.

---

## ✅ Requirements

- A Windows PC
- Python 3.11 or higher
- Node.js LTS
- Internet connection for the first install

---

## ▶️ Install / run the modern web deck

1. Download or clone the repo.
2. Open a Command Prompt in the project folder.
3. Run:

```bat
scripts\run_modern_ui.bat
```

That launcher will:

- install the UI dependencies
- start the Python bridge
- start the web app
- open the browser on the deck UI

If you want the native desktop/Tauri version instead, use:

```bat
scripts\run_desktop_app.bat
```

---

## 📦 If you only want the PC bridge setup

You can also install the Python bridge requirements directly:

```bat
py -3 -m pip install -r bridge\requirements.txt
```

That package list is intentionally small. You do **not** need the old `pygame pyperclip pyserial` ConsoleDeck instructions for the new web deck.

---

## ⚙️ Features

- Click one of the 9 buttons to assign an action
- Choose between:
  - a website URL (e.g. `https://youtube.com`)
  - a `.exe` file on your PC
  - or no action
- Modify the fields directly inside the app
- Use the "Browse" button to select `.exe` files
- Save your changes only when you're ready
- Supports volume control, mute toggle, and media play/pause via serial

Settings are stored in a local file called `config.json`.

---

## ❓ Troubleshooting

**🟡 Nothing happens when I click a button?**  
Make sure you launched the app using: `python main.py --gui`

**🔗 Can I use YouTube or other links?**  
Yes, any valid `https://` link will work.

**🧩 Can I assign programs like `.exe` files?**  
Yes! Use the “Browse” button to pick an executable file.

**💾 It says 'pip' is not recognized**  
Restart your computer or reinstall Python and ensure "Add Python to PATH" is selected during setup.

---

## 🧼 How to uninstall

- You can delete the project folder at any time
- To uninstall Python, go to **Apps & Features** in Windows

---

## 📬 Need help?

If you get stuck or the app doesn’t behave as expected, feel free to contact the developer or open an issue on the project repository.
