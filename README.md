<div align="center">
  <img src="frontend/public/Firecat.png" width="120" alt="Firecat Logo" />
  
  # Firecat Browser

  A open-source browser built with Electron, React, and Django.

  ![Electron](https://img.shields.io/badge/Electron-29-blue?logo=electron)
  ![React](https://img.shields.io/badge/React-18-blue?logo=react)
  ![Django](https://img.shields.io/badge/Django-5.0-green?logo=django)
  ![Python](https://img.shields.io/badge/Python-3.12-blue?logo=python)
  ![Platform](https://img.shields.io/badge/Platform-macOS%20Apple%20Silicon-black?logo=apple)
</div>

---

## Installation (macOS Apple Silicon)

### 1. Download

Download `Firecat.dmg` from the [Releases](https://github.com/andresnalegre/Firecat/releases) page.

### 2. Install

Open the DMG and drag Firecat.app to your Applications folder.

### 3. First Launch

macOS will block the app on first time becaude because it's not signed.
Just run this once in Terminal and you're good to go:
```bash
xattr -cr /Applications/Firecat.app
```

Then open Firecat from Applications or Launchpad normally.

---

## To the Community

### Requirements

- Node.js 18+
- Python 3.12

### Setup
```bash
git clone https://github.com/andresnalegre/Firecat.git
cd Firecat

cd backend
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cd ..

cd frontend
npm install
npm run build
cd ..

cd electron
npm install
npm start
```

---

## Build DMG
```bash
cd frontend && npm run build
cd ../electron && npm run build-mac
```

Output: `electron/dist/Firecat.dmg`

---

## Tech Stack

| Layer    | Technology                              |
|----------|-----------------------------------------|
| Shell    | Electron 29                             |
| Frontend | React 18 + Vite                         |
| Backend  | Django 5 + Django REST Framework        |
| Search   | Bing · DuckDuckGo · Brave · Mojeek · Yahoo |

---

## Author

Developed by [Andres Nicolas](https://andresnicolas.com)
