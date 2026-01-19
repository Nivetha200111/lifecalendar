#!/usr/bin/env python3
"""
Local client script to fetch wallpaper from Vercel API (or generate locally)
and set it as the desktop wallpaper.

Usage:
    python update_wallpaper.py [--local] [--api URL]

Options:
    --local     Generate wallpaper locally instead of fetching from API
    --api URL   Custom API URL (default: uses local generation)
"""

import argparse
import os
import platform
import subprocess
import sys
import tempfile
from pathlib import Path

# Default paths
DEFAULT_WALLPAPER_PATH = Path.home() / '.local' / 'share' / 'wallpapers' / 'goals_wallpaper.png'
PROJECT_ROOT = Path(__file__).parent.parent


def fetch_from_api(api_url: str, output_path: Path) -> bool:
    """Fetch wallpaper from Vercel API."""
    try:
        import urllib.request
        print(f"Fetching wallpaper from {api_url}...")

        # Create directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Fetch image
        urllib.request.urlretrieve(api_url, output_path)
        print(f"Wallpaper saved to {output_path}")
        return True

    except Exception as e:
        print(f"Error fetching from API: {e}")
        return False


def generate_locally(output_path: Path) -> bool:
    """Generate wallpaper locally using the lib modules."""
    try:
        # Add project root to path
        sys.path.insert(0, str(PROJECT_ROOT))

        from lib.wallpaper import generate

        # Create directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        print("Generating wallpaper locally...")
        generate(str(output_path))
        return True

    except Exception as e:
        print(f"Error generating locally: {e}")
        import traceback
        traceback.print_exc()
        return False


def set_wallpaper_linux(image_path: Path) -> bool:
    """Set wallpaper on Linux (supports GNOME, KDE, XFCE, Hyprland, Sway)."""
    image_path = str(image_path.absolute())

    # Detect desktop environment
    desktop = os.environ.get('XDG_CURRENT_DESKTOP', '').lower()
    session = os.environ.get('XDG_SESSION_TYPE', '').lower()

    commands = []

    # GNOME
    if 'gnome' in desktop or 'unity' in desktop:
        commands.append([
            'gsettings', 'set', 'org.gnome.desktop.background',
            'picture-uri', f'file://{image_path}'
        ])
        commands.append([
            'gsettings', 'set', 'org.gnome.desktop.background',
            'picture-uri-dark', f'file://{image_path}'
        ])

    # KDE Plasma 6+
    elif 'kde' in desktop or 'plasma' in desktop:
        # Plasma 6 uses plasma-apply-wallpaperimage
        commands.append(['plasma-apply-wallpaperimage', image_path])

    # XFCE
    elif 'xfce' in desktop:
        commands.append([
            'xfconf-query', '-c', 'xfce4-desktop',
            '-p', '/backdrop/screen0/monitor0/workspace0/last-image',
            '-s', image_path
        ])

    # Hyprland
    elif 'hyprland' in desktop or session == 'wayland':
        # Try hyprpaper first
        hyprpaper_conf = Path.home() / '.config' / 'hypr' / 'hyprpaper.conf'
        if hyprpaper_conf.exists() or 'hyprland' in desktop:
            # Update hyprpaper config
            config_content = f'''preload = {image_path}
wallpaper = ,{image_path}
'''
            try:
                hyprpaper_conf.parent.mkdir(parents=True, exist_ok=True)
                hyprpaper_conf.write_text(config_content)
                commands.append(['hyprctl', 'hyprpaper', 'reload'])
            except:
                pass

        # Try swaybg as fallback
        commands.append(['pkill', 'swaybg'])
        commands.append(['swaybg', '-i', image_path, '-m', 'fill'])

    # Sway
    elif 'sway' in desktop:
        commands.append(['swaymsg', f'output * bg {image_path} fill'])

    # Fallback: try feh or nitrogen
    if not commands:
        commands.append(['feh', '--bg-fill', image_path])
        commands.append(['nitrogen', '--set-zoom-fill', image_path])

    # Try each command
    for cmd in commands:
        try:
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            if result.returncode == 0:
                print(f"Wallpaper set successfully using: {cmd[0]}")
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            continue

    print("Warning: Could not detect method to set wallpaper. "
          f"Please set {image_path} manually.")
    return False


def set_wallpaper_macos(image_path: Path) -> bool:
    """Set wallpaper on macOS."""
    image_path = str(image_path.absolute())

    script = f'''
    tell application "Finder"
        set desktop picture to POSIX file "{image_path}"
    end tell
    '''

    try:
        subprocess.run(['osascript', '-e', script], check=True)
        print("Wallpaper set successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error setting wallpaper: {e}")
        return False


def set_wallpaper_windows(image_path: Path) -> bool:
    """Set wallpaper on Windows."""
    import ctypes

    image_path = str(image_path.absolute())

    # Convert PNG to BMP if needed (Windows sometimes prefers BMP)
    try:
        from PIL import Image
        img = Image.open(image_path)
        bmp_path = image_path.replace('.png', '.bmp')
        img.save(bmp_path, 'BMP')
        image_path = bmp_path
    except:
        pass

    SPI_SETDESKWALLPAPER = 20
    SPIF_UPDATEINIFILE = 1
    SPIF_SENDCHANGE = 2

    try:
        ctypes.windll.user32.SystemParametersInfoW(
            SPI_SETDESKWALLPAPER, 0, image_path,
            SPIF_UPDATEINIFILE | SPIF_SENDCHANGE
        )
        print("Wallpaper set successfully")
        return True
    except Exception as e:
        print(f"Error setting wallpaper: {e}")
        return False


def set_wallpaper(image_path: Path) -> bool:
    """Set wallpaper based on current platform."""
    system = platform.system()

    if system == 'Linux':
        return set_wallpaper_linux(image_path)
    elif system == 'Darwin':
        return set_wallpaper_macos(image_path)
    elif system == 'Windows':
        return set_wallpaper_windows(image_path)
    else:
        print(f"Unsupported platform: {system}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='Update desktop wallpaper with vaporwave goal tracker'
    )
    parser.add_argument(
        '--local', action='store_true',
        help='Generate wallpaper locally instead of fetching from API'
    )
    parser.add_argument(
        '--api', type=str, default=None,
        help='Vercel API URL (e.g., https://your-app.vercel.app/api/generate)'
    )
    parser.add_argument(
        '--output', type=str, default=None,
        help='Output path for wallpaper image'
    )
    parser.add_argument(
        '--no-set', action='store_true',
        help='Generate/fetch wallpaper but do not set it'
    )

    args = parser.parse_args()

    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = DEFAULT_WALLPAPER_PATH

    # Generate or fetch wallpaper
    success = False

    if args.local or args.api is None:
        # Generate locally
        success = generate_locally(output_path)
    else:
        # Fetch from API
        success = fetch_from_api(args.api, output_path)
        if not success:
            print("API fetch failed, falling back to local generation...")
            success = generate_locally(output_path)

    if not success:
        print("Failed to generate wallpaper")
        sys.exit(1)

    # Set wallpaper
    if not args.no_set:
        if not set_wallpaper(output_path):
            print("Warning: Wallpaper generated but could not be set automatically")
            print(f"Wallpaper saved to: {output_path}")
            sys.exit(1)

    print("Done!")


if __name__ == '__main__':
    main()
