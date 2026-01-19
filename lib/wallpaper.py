"""
Core wallpaper generation logic.
Composes all visual layers and renders goals with neon progress bars.
"""

import json
import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path

from .elements import (
    draw_gradient_sky,
    draw_sun,
    draw_perspective_grid,
    draw_palm_trees,
    draw_geometric_shapes,
    COLORS
)
from .effects import apply_all_effects


# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get a font, falling back to default if custom font not found."""
    # Try to load a custom font
    font_paths = [
        PROJECT_ROOT / 'assets' / 'fonts' / 'VCR_OSD_MONO.ttf',
        PROJECT_ROOT / 'assets' / 'fonts' / 'PressStart2P.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf',
    ]

    for font_path in font_paths:
        try:
            return ImageFont.truetype(str(font_path), size)
        except (OSError, IOError):
            continue

    # Fall back to default font
    try:
        return ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', size)
    except:
        return ImageFont.load_default()


def draw_neon_text(draw: ImageDraw.Draw, text: str, position: tuple,
                   font: ImageFont.FreeTypeFont, color: tuple,
                   glow_color: tuple = None, shadow: bool = True) -> None:
    """Draw text with neon glow effect."""
    x, y = position

    if glow_color is None:
        glow_color = color

    # Draw shadow
    if shadow:
        shadow_color = (20, 10, 30)
        draw.text((x + 3, y + 3), text, font=font, fill=shadow_color)

    # Draw glow layers
    for offset in range(4, 0, -1):
        alpha = 60 - offset * 12
        glow = (*glow_color[:3], max(0, alpha)) if len(glow_color) == 3 else glow_color
        for dx in range(-offset, offset + 1):
            for dy in range(-offset, offset + 1):
                if dx * dx + dy * dy <= offset * offset:
                    draw.text((x + dx, y + dy), text, font=font, fill=glow_color)

    # Draw main text
    draw.text(position, text, font=font, fill=color)


def draw_progress_bar(img: Image.Image, x: int, y: int, width: int, height: int,
                      progress: float, bar_color: tuple, bg_color: tuple = (30, 20, 50),
                      glow: bool = True) -> Image.Image:
    """Draw a neon-style progress bar with glow effect."""
    # Create bar layer
    bar_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(bar_layer)

    # Draw background
    draw.rounded_rectangle([x, y, x + width, y + height], radius=height // 2,
                           fill=(*bg_color, 200), outline=(*bar_color, 100), width=2)

    # Draw progress fill
    progress_width = int(width * min(progress, 1.0))
    if progress_width > 0:
        # Gradient fill for progress bar
        for i in range(progress_width):
            ratio = i / max(progress_width, 1)
            # Subtle gradient from left to right
            r = int(bar_color[0] * (0.8 + 0.2 * ratio))
            g = int(bar_color[1] * (0.8 + 0.2 * ratio))
            b = int(bar_color[2] * (0.8 + 0.2 * ratio))

            draw.line([(x + i + 2, y + 2), (x + i + 2, y + height - 2)],
                      fill=(r, g, b, 255))

        # Draw glow on filled portion
        if glow:
            glow_rect = [x, y, x + progress_width, y + height]
            glow_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
            glow_draw = ImageDraw.Draw(glow_layer)
            glow_draw.rounded_rectangle(glow_rect, radius=height // 2,
                                        fill=(*bar_color, 60))
            glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(radius=8))
            bar_layer = Image.alpha_composite(glow_layer, bar_layer)

    # Composite
    result = img.convert('RGBA')
    result = Image.alpha_composite(result, bar_layer)

    return result.convert('RGB')


def draw_goal(img: Image.Image, goal: dict, x: int, y: int,
              width: int, index: int) -> Image.Image:
    """Draw a single goal with progress bar and stats."""
    draw = ImageDraw.Draw(img)

    # Colors for different goals
    bar_colors = [
        COLORS['pink'],
        COLORS['cyan'],
        COLORS['purple'],
        COLORS['neon_blue'],
        COLORS['hot_pink'],
    ]
    color = bar_colors[index % len(bar_colors)]

    # Calculate progress
    current = goal.get('current', 0)
    target = goal.get('target', 100)
    progress = current / target if target > 0 else 0

    # Get fonts
    title_font = get_font(24)
    stats_font = get_font(18)
    percent_font = get_font(28, bold=True)

    # Draw goal name
    name = goal.get('name', 'Goal').upper()
    draw_neon_text(draw, name, (x, y), title_font, color, glow_color=color)

    # Draw progress bar
    bar_y = y + 40
    bar_height = 20
    img = draw_progress_bar(img, x, bar_y, width - 120, bar_height, progress, color)

    # Draw percentage on the right
    draw = ImageDraw.Draw(img)
    percent_text = f"{int(progress * 100)}%"
    percent_x = x + width - 100
    draw_neon_text(draw, percent_text, (percent_x, bar_y - 5), percent_font, color)

    # Draw current/target stats
    stats_text = f"{current:,} / {target:,}"
    stats_y = bar_y + bar_height + 8
    draw.text((x, stats_y), stats_text, font=stats_font, fill=(180, 170, 200))

    return img


def draw_title(img: Image.Image, title: str, y: int = 50) -> Image.Image:
    """Draw the main title with chrome/metallic gradient effect."""
    draw = ImageDraw.Draw(img)
    width = img.size[0]

    # Get a large font for the title
    font = get_font(56)

    # Calculate text position (centered)
    bbox = draw.textbbox((0, 0), title, font=font)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) // 2

    # Draw shadow
    shadow_offset = 4
    draw.text((x + shadow_offset, y + shadow_offset), title, font=font,
              fill=(20, 10, 30))

    # Draw chrome/gradient text effect using multiple layers
    # Outer glow
    for offset in range(6, 0, -1):
        glow_alpha = 100 - offset * 15
        glow_color = (255, 113, 206)  # Pink glow
        for dx in range(-offset, offset + 1):
            for dy in range(-offset, offset + 1):
                if dx * dx + dy * dy <= offset * offset:
                    draw.text((x + dx, y + dy), title, font=font, fill=glow_color)

    # Main text with gradient effect (simulate with multiple colors)
    # Top highlight
    draw.text((x, y - 1), title, font=font, fill=(255, 255, 255))
    # Main text
    draw.text((x, y), title, font=font, fill=(255, 200, 230))
    # Bottom shadow
    draw.text((x, y + 1), title, font=font, fill=(200, 150, 200))

    return img


def generate_wallpaper(goals_config: dict, output_path: str = None) -> Image.Image:
    """Generate a complete vaporwave wallpaper with goals."""

    # Get resolution from config
    resolution = goals_config.get('resolution', [1920, 1080])
    width, height = resolution

    # Create base image
    img = Image.new('RGB', (width, height), (0, 0, 0))

    # Layer 1: Gradient sky
    img = draw_gradient_sky(img)

    # Layer 2: Sun
    img = draw_sun(img)

    # Layer 3: Geometric shapes (in the sky)
    img = draw_geometric_shapes(img)

    # Layer 4: Palm trees
    img = draw_palm_trees(img, num_trees=4)

    # Layer 5: Perspective grid
    img = draw_perspective_grid(img)

    # Layer 6: Title
    title = goals_config.get('title', 'GOALS')
    img = draw_title(img, title, y=40)

    # Layer 7: Goals
    goals = goals_config.get('goals', [])
    goal_start_y = 130
    goal_height = 100
    goal_margin = 50
    goal_width = min(600, width - 200)
    goal_x = 100

    for i, goal in enumerate(goals):
        y = goal_start_y + i * goal_height
        if y + goal_height < height * 0.5:  # Keep goals above horizon
            img = draw_goal(img, goal, goal_x, y, goal_width, i)

    # Layer 8: Apply effects
    img = apply_all_effects(
        img,
        scanlines=True,
        noise=True,
        chromatic=True,
        glitch=False,  # Set to True for occasional glitch strips
        vignette=True,
        color_boost=True
    )

    # Save if path provided
    if output_path:
        img.save(output_path, 'PNG', quality=95)

    return img


def generate(output_path: str = 'wallpaper.png', goals_path: str = None) -> None:
    """Convenience function to generate wallpaper from goals.json."""
    if goals_path is None:
        goals_path = PROJECT_ROOT / 'goals.json'

    with open(goals_path, 'r') as f:
        goals_config = json.load(f)

    generate_wallpaper(goals_config, output_path)
    print(f"Wallpaper generated: {output_path}")


if __name__ == '__main__':
    generate()
