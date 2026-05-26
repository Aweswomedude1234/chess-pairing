# ChessPair — Setup & Deployment Guide

This document covers everything from creating the GitHub repository to
building distributable binaries for Windows and macOS.

---

## Repository Structure

You will have **two** repositories:

| Repo | Purpose |
|------|---------|
| `chesspair-web` | The React web app (your existing repo) |
| `chesspair` | The Python desktop app + landing page |

This guide sets up the **new `chesspair` repository**.

---

## 1. Create the GitHub Repository

1. Go to https://github.com/new
2. Repository name: `chesspair`
3. Description: `Free, open-source USCF Swiss tournament pairing software`
4. Set to **Public**
5. ✅ Add a README
6. License: **MIT**
7. Click **Create repository**

---

## 2. Initial Local Setup

```bash
# Clone your new repo
git clone https://github.com/YOUR_USERNAME/chesspair.git
cd chesspair

# Copy in all the files from this delivery:
#   main.py
#   requirements.txt
#   chesspair.spec
#   app/__init__.py
#   app/models.py
#   app/gui.py
#   index.html         ← landing page
#   docs/              ← optional extended docs

# Commit everything
git add .
git commit -m "feat: initial release - full Swiss pairing engine + GUI"
git push origin main
```

---

## 3. Python Environment Setup (Development)

Requires Python 3.10 or newer. tkinter is included in standard Python
distributions on Windows and macOS. On Linux: `sudo apt install python3-tk`.

```bash
# Create and activate virtual environment
python -m venv venv

# Windows:
venv\Scripts\activate

# macOS / Linux:
source venv/bin/activate

# Install build dependencies
pip install -r requirements.txt

# Run from source
python main.py
```

---

## 4. Building Distributable Binaries

### 4a. Windows (.exe)

Run this on a Windows machine (or Windows VM / GitHub Actions runner):

```bash
# Inside the activated venv:
pyinstaller chesspair.spec

# Output: dist/ChessPair.exe
# That single file is your Windows release artifact.
```

To create an installer (optional, recommended):
- Download and install [NSIS](https://nsis.sourceforge.io/)
- Create a simple `installer.nsi` script pointing to `dist/ChessPair.exe`
- Run `makensis installer.nsi` → produces `ChessPair-Setup.exe`

### 4b. macOS (.dmg)

Run this on a Mac:

```bash
pyinstaller chesspair.spec

# Output: dist/ChessPair.app

# Package into a .dmg:
hdiutil create -volname "ChessPair" \
  -srcfolder dist/ChessPair.app \
  -ov -format UDZO \
  ChessPair.dmg
```

> **Apple Silicon note:** PyInstaller on an M1/M2 Mac builds an arm64 binary.
> For universal (Intel + Apple Silicon) builds, use `--target-arch universal2`
> and ensure you have a universal Python installation.

### 4c. Linux (run from source)

Linux users run from source. Document this in your README:

```bash
sudo apt install python3 python3-tk python3-pip
pip3 install -r requirements.txt
python3 main.py
```

---

## 5. Creating a GitHub Release

After building your binaries:

1. Go to your repo → **Releases** → **Draft a new release**
2. Tag: `v1.0.0`
3. Title: `ChessPair v1.0.0 — Initial Release`
4. Write release notes in the description box
5. Upload artifacts:
   - `ChessPair.exe` (or `ChessPair-Setup.exe`)
   - `ChessPair.dmg`
   - Source zip is included automatically
6. Click **Publish release**

GitHub auto-generates a URL for each asset:
```
https://github.com/YOUR_USERNAME/chesspair/releases/download/v1.0.0/ChessPair.exe
https://github.com/YOUR_USERNAME/chesspair/releases/download/v1.0.0/ChessPair.dmg
```

**Update `index.html`** — replace the `#` href values with these URLs:
```html
<!-- In the releases section of index.html: -->
<a href="https://github.com/YOUR_USERNAME/chesspair/releases/download/v1.0.0/ChessPair.exe"
   class="release-dl-link win-link">🪟 Windows .exe</a>

<a href="https://github.com/YOUR_USERNAME/chesspair/releases/download/v1.0.0/ChessPair.dmg"
   class="release-dl-link mac-link">🍎 macOS .dmg</a>
```

Also update the primary download button script at the bottom of `index.html`:
```js
// Windows:
btn.href = 'https://github.com/YOUR_USERNAME/chesspair/releases/download/v1.0.0/ChessPair.exe';
// macOS:
btn.href = 'https://github.com/YOUR_USERNAME/chesspair/releases/download/v1.0.0/ChessPair.dmg';
```

---

## 6. Hosting the Landing Page (GitHub Pages)

The `index.html` file can be served directly from GitHub Pages at no cost.

1. Go to your repo → **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: `main`, folder: `/ (root)`
4. Click **Save**

Your landing page will be live at:
`https://YOUR_USERNAME.github.io/chesspair/`

> For a custom domain (e.g. `chesspair.app`), add a `CNAME` file containing
> your domain name to the repo root, then configure your DNS registrar.

---

## 7. Automated Builds with GitHub Actions (Optional but Recommended)

Create `.github/workflows/build.yml` to auto-build on every release tag:

```yaml
name: Build Release Binaries

on:
  push:
    tags:
      - 'v*'

jobs:
  build-windows:
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install pyinstaller
      - run: pyinstaller chesspair.spec
      - uses: actions/upload-artifact@v4
        with:
          name: ChessPair-Windows
          path: dist/ChessPair.exe

  build-macos:
    runs-on: macos-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install pyinstaller
      - run: pyinstaller chesspair.spec
      - run: |
          hdiutil create -volname "ChessPair" \
            -srcfolder dist/ChessPair.app \
            -ov -format UDZO ChessPair.dmg
      - uses: actions/upload-artifact@v4
        with:
          name: ChessPair-macOS
          path: ChessPair.dmg
```

With this workflow, pushing a tag like `git tag v1.1.0 && git push --tags`
automatically builds both binaries which you can then attach to your release.

---

## 8. Replacing YOUR_USERNAME

Do a find-and-replace in all files before pushing:

- `index.html` — replace all instances of `YOUR_USERNAME`
- `app/gui.py` — the About dialog URL
- `SETUP.md` — this file

---

## 9. Recommended README.md

Replace the auto-generated README with something like:

```markdown
# ♟ ChessPair

Free, open-source USCF Swiss tournament pairing software for Windows and macOS.

## Download

| Platform | Link |
|----------|------|
| 🪟 Windows | [ChessPair.exe](https://github.com/YOUR_USERNAME/chesspair/releases/latest) |
| 🍎 macOS | [ChessPair.dmg](https://github.com/YOUR_USERNAME/chesspair/releases/latest) |
| 🐧 Linux | Run from source (see below) |

## Features
- Swiss pairing with backtracking engine
- Unlimited sections (Open, U1800, U1600, Scholastic, etc.)
- USCF tiebreaks: Modified Median, Solkoff, Cumulative, Opp. Cumulative, S-B
- Color balancing, bye management, withdrawal handling
- CSV export for players, pairings, and standings
- Fully offline — no account or internet required

## Run from Source
\`\`\`bash
git clone https://github.com/YOUR_USERNAME/chesspair.git
cd chesspair
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main.py
\`\`\`

## License
MIT — not affiliated with USCF.
```

---

## File Structure Reference

```
chesspair/
├── main.py                  ← Entry point
├── requirements.txt         ← Build deps
├── chesspair.spec           ← PyInstaller config
├── index.html               ← Landing page (served via GitHub Pages)
├── SETUP.md                 ← This file
├── README.md                ← GitHub readme
├── app/
│   ├── __init__.py
│   ├── models.py            ← Pairing engine + data models
│   └── gui.py               ← tkinter GUI
├── assets/
│   ├── icon.ico             ← Add your Windows icon here
│   └── icon.icns            ← Add your macOS icon here
└── .github/
    └── workflows/
        └── build.yml        ← Optional auto-build CI
```
