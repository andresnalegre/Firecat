<div align="center">
  <img src="frontend/public/Firecat.png" width="120" alt="Firecat Logo" />

  # Firecat Browser

  A new way to browse the web.

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

**Firecat** is a desktop browser available for macOS that combines multi-engine search, operators, and filters to deliver better search results. This open-source browser is built with Electron, React, and Django.

## Features

- Multi tab browsing
- Bookmark bar with pinnable shortcuts
- Browsing history
- Deep Search
- Built in web proxy with SSL fallback
- Real-time download progress bar
- Download history page at `firecat://downloads`
- Multiple themes including dark and light modes

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

## License

This project is licensed under the [MIT License](LICENSE).

## Contributing

Contributions are welcome! Feel free to fork the repository and submit a pull request. Please ensure your code follows the existing style and structure.
