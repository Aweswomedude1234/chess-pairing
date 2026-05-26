#!/usr/bin/env python3
"""
Generate ChessPair application icons for Windows and macOS.
Requires: pip install pillow

Run from the assets/ directory:
  python generate_icons.py
"""

import os
from PIL import Image, ImageDraw, ImageFont

def create_icon_image(size=512, bg_color='#2563eb', text='♟'):
    """Create a simple chess pawn icon on a blue background."""
    img = Image.new('RGB', (size, size), color=bg_color)
    draw = ImageDraw.Draw(img)

    # Add white chess pawn symbol in the center
    text_color = (255, 255, 255)
    try:
        # Try to use a larger font
        font_size = int(size * 0.6)
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        # Fallback to default font
        font = ImageFont.load_default()

    # Draw pawn in center
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2
    y = (size - text_height) // 2
    draw.text((x, y), text, fill=text_color, font=font)

    return img

def create_ico_file():
    """Create Windows .ico file (512x512)."""
    img = create_icon_image(512)
    # Save with multiple sizes for .ico
    img.save('icon.ico', sizes=[(16, 16), (32, 32), (64, 64), (128, 128), (256, 256), (512, 512)])
    print("[+] Created icon.ico (512x512)")

def create_icns_file():
    """Create macOS .icns file."""
    try:
        from PIL import features
        if not features.check('icns'):
            print("[!] PIL icns support not available on this system")
            print("    For proper .icns support on macOS, run: pip install pillow-icns")
            # Still create a 512x512 PNG that can be converted manually
            img = create_icon_image(512)
            img.save('icon-512.png')
            print("    Created icon-512.png as fallback (convert manually on macOS)")
            return
    except:
        pass

    # Create high-res icon for macOS
    img = create_icon_image(1024)
    img.save('icon.icns')
    print("[+] Created icon.icns (1024x1024)")

def main():
    """Generate both icon files."""
    print("Generating ChessPair icons...")
    print()

    try:
        create_ico_file()
        create_icns_file()
        print()
        print("[*] Icon generation complete!")
        print("    Place icon.ico and icon.icns in the assets/ directory")
    except ImportError:
        print("[!] PIL/Pillow not installed")
        print("    Install with: pip install pillow")
        print()
        print("Alternatively, use any icon editor to create:")
        print("  - icon.ico (512x512, Windows)")
        print("  - icon.icns (1024x1024, macOS)")

if __name__ == '__main__':
    main()
