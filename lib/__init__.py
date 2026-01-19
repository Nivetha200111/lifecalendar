"""Vaporwave wallpaper generation library."""

from .wallpaper import generate_wallpaper, generate
from .elements import COLORS
from .effects import apply_all_effects

__all__ = ['generate_wallpaper', 'generate', 'COLORS', 'apply_all_effects']
