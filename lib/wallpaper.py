
import json
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

# Minimalist color palette
COLORS = {
    'background': (245, 245, 245),
    'text': (50, 50, 50),
    'primary': (0, 120, 255),  # A nice blue
    'grey': (200, 200, 200),
    'white': (255, 255, 255),
}


def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Get a modern, clean font."""
    font_paths = [
        '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf' if bold else '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
        '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf',
        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
    ]

    for font_path in font_paths:
        try:
            return ImageFont.truetype(str(font_path), size)
        except (OSError, IOError):
            continue

    return ImageFont.load_default()


def draw_title(img: Image.Image, title: str, y: int = 60) -> Image.Image:
    """Draw a minimalist title."""
    draw = ImageDraw.Draw(img)
    width = img.size[0]
    font = get_font(48, bold=True)

    # Calculate centered position
    bbox = draw.textbbox((0, 0), title, font=font)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) // 2

    # Main text
    draw.text((x, y), title, font=font, fill=COLORS['text'])

    # Underline
    underline_y = y + (bbox[3] - bbox[1]) + 10
    draw.line([(x, underline_y), (x + text_width, underline_y)], fill=COLORS['primary'], width=3)

    return img


def draw_progress_bar(img: Image.Image, x: int, y: int, width: int, height: int,
                        progress: float, bar_color: tuple) -> Image.Image:
    """Draw a minimalist progress bar."""
    draw = ImageDraw.Draw(img)
    progress_width = int(width * min(progress, 1.0))

    # Background
    draw.rectangle([x, y, x + width, y + height], fill=COLORS['grey'])

    # Progress
    if progress_width > 0:
        draw.rectangle([x, y, x + progress_width, y + height], fill=bar_color)

    return img


def draw_goal(img: Image.Image, goal: dict, x: int, y: int,
              width: int, index: int) -> Image.Image:
    """Draw a single goal with a minimalist progress bar."""
    draw = ImageDraw.Draw(img)

    # Color for this goal
    color = COLORS['primary']

    # Calculate progress
    current = goal.get('current', 0)
    target = goal.get('target', 100)
    progress = current / target if target > 0 else 0

    # Fonts
    title_font = get_font(24, bold=True)
    stats_font = get_font(16)

    # Goal name
    name = goal.get('name', 'Goal')
    draw.text((x, y), name, font=title_font, fill=COLORS['text'])

    # Progress bar
    bar_y = y + 40
    bar_height = 8
    bar_width = width - 70
    img = draw_progress_bar(img, x, bar_y, bar_width, bar_height, progress, color)

    # Percentage
    percent_text = f"{int(progress * 100)}%"
    percent_font = get_font(18, bold=True)
    percent_x = x + bar_width + 10
    draw.text((percent_x, bar_y - 8), percent_text, font=percent_font, fill=color)

    # Stats text
    stats_text = f"{current:,} / {target:,}"
    stats_y = bar_y + bar_height + 5
    draw.text((x, stats_y), stats_text, font=stats_font, fill=COLORS['text'])

    return img


def generate_wallpaper(goals_config: dict, output_path: str = None) -> Image.Image:
    """Generate a minimalist themed wallpaper."""
    resolution = goals_config.get('resolution', [1920, 1080])
    width, height = resolution

    img = Image.new('RGB', (width, height), COLORS['background'])

    # Draw title
    title = goals_config.get('title', 'MY GOALS')
    img = draw_title(img, title, y=80)

    # Draw goals
    goals = goals_config.get('goals', [])
    goal_start_y = 200
    goal_height = 100
    goal_width = min(600, width - 120)
    goal_x = (width - goal_width) // 2

    for i, goal in enumerate(goals):
        y = goal_start_y + i * goal_height
        if y + goal_height < height:
            img = draw_goal(img, goal, goal_x, y, goal_width, i)

    # Save if path provided
    if output_path:
        img.save(output_path, 'PNG', quality=95)

    return img


def generate(output_path: str = 'wallpaper_minimal.png', goals_path: str = None) -> None:
    """Generate wallpaper from goals.json."""
    if goals_path is None:
        goals_path = PROJECT_ROOT / 'goals.json'

    with open(goals_path, 'r') as f:
        goals_config = json.load(f)

    generate_wallpaper(goals_config, output_path)
    print(f"Wallpaper generated: {output_path}")


if __name__ == '__main__':
    generate()
