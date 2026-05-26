# ChessPair — Setup, Build & Deployment

This guide covers building ChessPair from source and deploying releases.

---

## Prerequisites

- Python 3.10 or newer
- Git
- pip (usually included with Python)

### Platform-Specific

**macOS:**
```bash
brew install python@3.11
```

**Linux (Debian/Ubuntu):**
```bash
sudo apt install python3 python3-tk python3-pip git
```

**Windows:**
- Download from [python.org](https://www.python.org/downloads/)
- Ensure "Install pip" is checked
- Ensure "Add Python to PATH" is checked

---

## Development Setup

### Clone & Install

```bash
git clone https://github.com/Aweswomedude1234/chess-pairing.git
cd chess-pairing

# Create virtual environment
python -m venv venv

# Activate it
# macOS / Linux:
source venv/bin/activate

# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Run from Source

```bash
python main.py
```

The GUI should launch immediately. No additional setup needed.

---

## Building Distributable Binaries

### Install PyInstaller

```bash
pip install pyinstaller
```

### Generate Icons (Optional but Recommended)

Icons make your app look professional. To generate simple icons:

```bash
cd assets
python generate_icons.py
cd ..
```

This creates:
- `assets/icon.ico` (Windows)
- `assets/icon.icns` (macOS, requires PIL/Pillow — created automatically in GitHub Actions)

Custom icons: Replace these files with your own 512x512+ PNG or use an icon editor to create `.ico` and `.icns` versions.

### Build

```bash
pyinstaller chesspair.spec
```

Output:
- **Windows**: `dist/ChessPair.exe` (~50 MB, single executable)
- **macOS**: `dist/ChessPair.app` (a bundle — package into .dmg below)

### Package macOS App into DMG (macOS only)

```bash
hdiutil create -volname "ChessPair" \
  -srcfolder dist/ChessPair.app \
  -ov -format UDZO \
  -imagekey zlib-level=9 \
  ChessPair.dmg
```

Result: `ChessPair.dmg` (~60 MB)

---

## Creating a Release

### 1. Tag a Version

```bash
git tag -a v1.0.0 -m "ChessPair v1.0.0 — Initial Release"
git push origin v1.0.0
```

This triggers the GitHub Actions workflow automatically.

### 2. GitHub Actions Does the Rest

The `.github/workflows/build.yml` workflow:
- ✅ Builds Windows `.exe` on Windows runner
- ✅ Builds macOS `.dmg` on macOS runner
- ✅ Generates SHA-256 checksums
- ✅ Creates a GitHub Release with all artifacts

**No manual upload needed.** Just push the tag.

### 3. Verify Release

Check [GitHub Releases](https://github.com/Aweswomedude1234/chess-pairing/releases) after 5–10 minutes:
- Both binaries should be uploaded
- SHA-256 checksums included
- Release notes auto-generated

---

## Manual Release (If GitHub Actions Fails)

If you need to build and release manually:

### 1. Build Both Binaries

**On Windows:**
```bash
pip install -r requirements.txt pyinstaller
pyinstaller chesspair.spec
# Creates: dist/ChessPair.exe
```

**On macOS:**
```bash
pip install -r requirements.txt pyinstaller
pyinstaller chesspair.spec
# Creates: dist/ChessPair.app

hdiutil create -volname "ChessPair" \
  -srcfolder dist/ChessPair.app \
  -ov -format UDZO \
  ChessPair.dmg
# Creates: ChessPair.dmg
```

### 2. Generate Checksums

**Windows:**
```powershell
certutil -hashfile dist/ChessPair.exe SHA256 | Out-File checksums-win.txt
```

**macOS/Linux:**
```bash
shasum -a 256 ChessPair.dmg > checksums-mac.txt
```

### 3. Create GitHub Release

1. Go to [Releases](https://github.com/Aweswomedude1234/chess-pairing/releases)
2. Click **Draft a new release**
3. Tag: `v1.0.0`
4. Title: `ChessPair v1.0.0`
5. Description: Copy from auto-generated release notes
6. Upload:
   - `ChessPair.exe` (Windows)
   - `ChessPair.dmg` (macOS)
   - `checksums-win.txt` (Windows hashes)
   - `checksums-mac.txt` (macOS hashes)
7. Click **Publish release**

---

## Hosting the Landing Page

The `web/index.html` landing page is served via GitHub Pages.

### Enable GitHub Pages

1. Go to **Settings** → **Pages**
2. Source: **Deploy from a branch**
3. Branch: `main`, folder: `/ (root)`
4. Click **Save**

Your landing page is now live at:
```
https://github.com/YOUR_USERNAME/chess-pairing
```

(GitHub Pages serves it at the repo's default branch.)

### Custom Domain (Optional)

1. Register a domain (e.g., `chesspair.app`)
2. Add a `CNAME` file to repo root containing your domain name
3. Update your DNS registrar's CNAME record pointing to `github.pages.io`
4. GitHub handles HTTPS automatically (takes ~24 hours)

---

## File Structure

```
chesspair/
├── main.py                          # Entry point
├── requirements.txt                 # Python deps (tkinter is built-in)
├── chesspair.spec                   # PyInstaller config
├── README.md                        # User-facing docs
├── SETUP.md                         # This file
├── SECURITY.md                      # Security & verification docs
├── LICENSE                          # MIT License
│
├── app/
│   ├── __init__.py
│   ├── models.py                    # Swiss engine, pairing, tiebreaks
│   └── gui.py                       # tkinter GUI
│
├── assets/
│   ├── icon.ico                     # Windows icon (512x512)
│   ├── icon.icns                    # macOS icon (1024x1024)
│   ├── icon-512.png                 # Icon fallback
│   └── generate_icons.py            # Icon generator script
│
├── web/
│   └── index.html                   # Landing page (GitHub Pages)
│
├── .github/
│   └── workflows/
│       └── build.yml                # CI/CD: auto-build on git tag
│
├── .gitignore                       # Exclude build artifacts
└── dist/                            # Build output (not in git)
    ├── ChessPair.exe                # Windows executable
    └── ChessPair.app                # macOS app bundle
```

---

## Troubleshooting

### PyInstaller: "module not found"

Add to `hiddenimports` in `chesspair.spec`:

```python
hiddenimports=['tkinter', 'tkinter.ttk', 'tkinter.messagebox',
               'tkinter.filedialog', 'tkinter.simpledialog']
```

### Windows: "SmartScreen warning"

Unsigned executables show this warning. It's expected. Users click "More info" → "Run anyway". This is why SHA-256 verification matters — it proves the file is authentic.

### macOS: "Cannot open because it's from an unknown developer"

Right-click the app in Applications → **Open**. Gatekeeper learns to trust it after first run. Users never see this warning again after the first launch.

### Building .dmg fails

Ensure you're on macOS and `hdiutil` is available:
```bash
which hdiutil
```

If `hdiutil` isn't found, you're not on macOS. GitHub Actions handles this automatically.

---

## Next Steps

1. ✅ **Push to GitHub**: `git push origin main`
2. ✅ **Tag a release**: `git tag v1.0.0 && git push origin v1.0.0`
3. ✅ **Wait for builds**: Check Actions tab (takes 5–10 min)
4. ✅ **Verify release**: Check [Releases](https://github.com/Aweswomedude1234/chess-pairing/releases)
5. ✅ **Share the landing page**: `https://YOUR_USERNAME.github.io/chess-pairing`

---

## Resources

- [PyInstaller Docs](https://pyinstaller.org/)
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [GitHub Pages Docs](https://docs.github.com/en/pages)
- [Security & Verification](SECURITY.md)

---

Not affiliated with USCF. MIT Licensed.
