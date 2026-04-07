<div align="center">
  <img src="frontend/public/Firecat.png" width="120" alt="Firecat Logo" />

  # Firecat Browser

  An open-source browser built with Electron, React, and Django, available for macOS.

  ![Electron](https://img.shields.io/badge/Electron-29-blue?logo=electron)
  ![React](https://img.shields.io/badge/React-18-blue?logo=react)
  ![Django](https://img.shields.io/badge/Django-5.0-green?logo=django)
  ![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
  ![Platform](https://img.shields.io/badge/Platform-macOS%20Apple%20Silicon-black?logo=apple)

  [![Download DMG](https://img.shields.io/badge/Download-DMG-blue?style=flat-square)](https://github.com/andresnalegre/Firecat/releases)
  [![GitHub](https://img.shields.io/badge/Made%20by-Andres%20Nicolas%20Alegre-brightgreen?style=flat-square)](https://github.com/andresnalegre)
</div>

---

## About

**Firecat** is a desktop browser with Deep Search powered by multi engine search tools including Bing, DuckDuckGo, Brave, Mojeek and Yahoo, using Google Hacking operators and search filters.

## Features

- Multi tab browsing with up to 15 tabs
- Bookmark bar with pinnable shortcuts
- Browsing history with deduplication
- Deep Search across 40+ operator groups
- Built in web proxy with SSL fallback
- Real-time download progress bar
- Download history page at `firecat://downloads`
- Multiple themes including dark and light modes
- Fullscreen support with native macOS traffic lights

---

## Installation (macOS Apple Silicon)

### 1. Download

Download `Firecat.dmg` from the [Releases](https://github.com/andresnalegre/Firecat/releases) page.

### 2. Install

Open the DMG and drag Firecat.app to your Applications folder.

### 3. First Launch

macOS will block the app on first launch because it's not signed. Run this once in Terminal:

```bash
xattr -cr /Applications/Firecat.app
```

Then open Firecat from Applications or Launchpad normally.

---

## Run locally

### Requirements

- Python 3.10+
- Node.js 18+

### Setup

```bash
git clone https://github.com/andresnalegre/Firecat.git
cd Firecat
python3 firecat.py
```

The launcher installs all dependencies, runs migrations, builds the frontend and starts the app automatically.

---

## Build DMG

```bash
cd frontend && npm run build
cd ../electron && npm run build-mac
```

Output: `electron/dist/Firecat.dmg`

---

## Keyboard shortcuts

| Shortcut | Action |
|----------|--------|
| `Cmd+T` | New tab |
| `Cmd+W` | Close tab |
| `Cmd+D` | Bookmark page |
| `Cmd+H` | History panel |

---

## Tech stack

| Layer | Technology |
|-------|------------|
| Shell | Electron 29 |
| Frontend | React 18 + Vite |
| Backend | Django 5 + Django REST Framework |
| Search | Bing · DuckDuckGo · Brave · Mojeek · Yahoo |
| Database | SQLite |

---

## License

This project is licensed under the [MIT License](LICENSE).

## Contributing

Contributions are welcome! Feel free to fork the repository and submit a pull request. Please ensure your code follows the existing style and structure.
