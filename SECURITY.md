# Security & Verification

## Overview

ChessPair is distributed as standalone, unsigned executables hosted on GitHub Releases. This document explains how ChessPair is built, signed, and how you can verify the integrity of your download.

## Verification: SHA-256 Checksums

All releases include SHA-256 checksums for integrity verification.

### Windows

```powershell
# Download ChessPair.exe and its SHA-256 hash file
# Then verify:
certutil -hashfile ChessPair.exe SHA256
```

Compare the output with the hash in `ChessPair-Windows-SHA256.txt`.

### macOS / Linux

```bash
shasum -a 256 ChessPair.dmg
# or
sha256sum ChessPair.dmg
```

Compare with the hash in `ChessPair-macOS-SHA256.txt`.

## Code Signing Status

### Windows
- **Status**: Unsigned
- **What you'll see**: SmartScreen warning on first run
- **Why**: Code signing certificates cost $300+/year; as an open-source project, we prioritize accessibility
- **What to do**: Click "More info" → "Run anyway"
- **Safety**: The executable is built from open-source code on GitHub Actions. Verify the SHA-256 hash to confirm you have the official build

### macOS
- **Status**: Unsigned, not notarized
- **What you'll see**: Gatekeeper warning on first run
- **Why**: Apple Developer account costs $99/year; open-source, we prioritize accessibility
- **What to do**: Right-click ChessPair in Applications → "Open" (only needed first time)
- **Safety**: The app is built from open-source code on GitHub Actions. Verify the SHA-256 hash to confirm you have the official build

## Build Transparency

Every release binary is built automatically by GitHub Actions from the public source code:

1. **Reproducibility**: [View the build workflow](.github/workflows/build.yml)
2. **Source**: Every release is built from a git tag in the [public repository](https://github.com/Aweswomedude1234/chess-pairing)
3. **No secrets**: No API keys, credentials, or external dependencies are embedded
4. **Open process**: Build logs are public and auditable

To verify a specific release was built from source:
```bash
git log --oneline --decorate | grep v1.0.0
git show v1.0.0  # View the exact commit that was tagged
```

## Dependency Security

ChessPair has minimal dependencies:

- **Runtime**: Python standard library only (tkinter)
- **Build-time**: PyInstaller (open-source, dependency-checked)
- **No network**: The app runs entirely offline once built

### Keeping Dependencies Current

We regularly update build dependencies to patch security issues:

```bash
pip list --outdated
```

## Reporting Security Issues

If you discover a security vulnerability in ChessPair:

1. **Do not** open a public GitHub issue
2. Email: [Report via GitHub Security Advisory](https://github.com/Aweswomedude1234/chess-pairing/security/advisories)
3. Include: version number, description, reproduction steps
4. We'll respond within 48 hours

## Open Source Accountability

ChessPair is MIT Licensed and open source. You can:

- **Inspect the source code** before running
- **Audit the build process** in `.github/workflows/build.yml`
- **Verify releases** with SHA-256 checksums
- **Fork and rebuild** from source if desired
- **Report issues** without any NDA

---

## FAQ

**Q: Is it safe to run an unsigned .exe?**  
A: Yes, if you've verified the SHA-256 hash matches our release. The warning is a Windows security feature, not an indication the file is malicious. SmartScreen is very conservative with all unsigned software.

**Q: Can I build ChessPair myself?**  
A: Absolutely! The entire build process is documented in SETUP.md. Clone the repo, follow the build steps, and compare SHA-256 hashes with our official release.

**Q: Why not just buy code signing certificates?**  
A: We want ChessPair to remain 100% free forever. Code signing costs scale with the team; we'd rather spend that money on development than certificates.

**Q: How do I know the .dmg on GitHub is authentic?**  
A: Check the SHA-256 hash. If it matches, you have the exact binary built from the source code at that git tag. GitHub's infrastructure is audited and trusted by millions of developers.
