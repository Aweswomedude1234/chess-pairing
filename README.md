# ♟ ChessPair

Free, open-source USCF Swiss tournament pairing software for Windows and macOS.

[![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![GitHub Issues](https://img.shields.io/github/issues/Aweswomedude1234/chess-pairing)](https://github.com/Aweswomedude1234/chess-pairing/issues)

## Download

| Platform | Download | Size |
|----------|----------|------|
| **Windows** | [ChessPair.exe](https://github.com/Aweswomedude1234/chess-pairing/releases/download/v1.0.0/ChessPair.exe) | ~50 MB |
| **macOS** | [ChessPair.dmg](https://github.com/Aweswomedude1234/chess-pairing/releases/download/v1.0.0/ChessPair.dmg) | ~60 MB |
| **Linux** | [Run from source](#run-from-source) | — |

[All releases →](https://github.com/Aweswomedude1234/chess-pairing/releases)

## Features

- ✓ **Swiss pairing with backtracking engine** — finds valid pairings in complex score groups
- ✓ **Unlimited sections** — Open, U1800, U1600, Scholastic, etc. with independent pairings
- ✓ **USCF tiebreaks** — Modified Median, Solkoff, Cumulative, Opposition, Sonneborn-Berger
- ✓ **Color balancing** — tracks white/black balance, prevents triple-color streaks
- ✓ **Bye management** — automatically awards byes to eligible players
- ✓ **CSV export** — rosters, pairings, standings for printing or USCF submission
- ✓ **Fully offline** — no account, cloud, or internet required
- ✓ **MIT Licensed** — free and open source forever

## Quick Start

### Windows

1. Download [ChessPair.exe](https://github.com/Aweswomedude1234/chess-pairing/releases/download/v1.0.0/ChessPair.exe)
2. Run it (may see SmartScreen warning → click **More info** → **Run anyway**)
3. Start entering your tournament

### macOS

1. Download [ChessPair.dmg](https://github.com/Aweswomedude1234/chess-pairing/releases/download/v1.0.0/ChessPair.dmg)
2. Open the DMG file
3. Drag **ChessPair** to Applications folder
4. On first run, right-click ChessPair → **Open** (to bypass Gatekeeper)
5. After first launch, you can open normally

### Linux (Run from Source)

```bash
git clone https://github.com/Aweswomedude1234/chess-pairing.git
cd chess-pairing
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python3 main.py
```

Requires: Python 3.10+, tkinter

```bash
# Debian / Ubuntu
sudo apt install python3 python3-tk python3-pip

# Fedora
sudo dnf install python3 python3-tkinter python3-pip

# macOS (Homebrew)
brew install python@3.11
```

## Verification

Verify download integrity using SHA-256:

**Windows:**
```powershell
certutil -hashfile ChessPair.exe SHA256
```

**macOS/Linux:**
```bash
shasum -a 256 ChessPair.dmg
```

Compare with hashes in [GitHub Releases](https://github.com/Aweswomedude1234/chess-pairing/releases).

See [SECURITY.md](SECURITY.md) for full verification documentation.

## Documentation

- [Installation Guide](SETUP.md#installation)
- [Quick Start Tutorial](SETUP.md#quick-start)
- [Pairing Rules Reference](SETUP.md#pairing-rules)
- [Security & Verification](SECURITY.md)
- [Developer Setup](SETUP.md#developer-setup)

## Development

### Prerequisites
- Python 3.10 or newer
- tkinter (included with Python)
- pip

### Build from Source

```bash
git clone https://github.com/Aweswomedude1234/chess-pairing.git
cd chess-pairing

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run from source
python main.py

# Build distributable binaries
pip install pyinstaller
pyinstaller chesspair.spec
# Output: dist/ChessPair.exe (Windows) or dist/ChessPair.app (macOS)
```

### Project Structure

```
chesspair/
├── main.py                  # Entry point
├── requirements.txt         # Python dependencies
├── chesspair.spec          # PyInstaller configuration
├── app/
│   ├── __init__.py
│   ├── models.py           # Swiss engine, pairing logic, tiebreaks
│   └── gui.py              # tkinter GUI
├── assets/
│   ├── icon.ico            # Windows icon
│   └── icon.icns           # macOS icon
├── web/
│   └── index.html          # Landing page
├── .github/workflows/
│   └── build.yml           # CI/CD for auto-building releases
├── SETUP.md                # Setup & deployment guide
└── SECURITY.md             # Security & verification docs
```

### Contributing

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to your branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## Issues & Feature Requests

Found a bug? Have a feature idea? [Open an issue →](https://github.com/Aweswomedude1234/chess-pairing/issues)

## License

MIT License — See [LICENSE](LICENSE) for details.

Not affiliated with USCF. ChessPair is a community project.

---

**Questions?** Check [SETUP.md](SETUP.md) or [open an issue](https://github.com/Aweswomedude1234/chess-pairing/issues).

**Security concern?** See [SECURITY.md](SECURITY.md) for responsible disclosure.
