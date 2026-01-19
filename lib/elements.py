"""
Visual elements for vaporwave wallpaper generation.
Includes gradient sky, retro sun, perspective grid, palm trees, and geometric shapes.
"""

from PIL import Image, ImageDraw, ImageFilter
import math
import random


# Vaporwave color palette
COLORS = {
    'pink': (255, 113, 206),
    'cyan': (1, 205, 254),
    'purple': (185, 103, 255),
    'dark_purple': (75, 0, 130),
    'hot_pink': (255, 0, 128),
    'orange': (255, 151, 28),
    'yellow': (255, 220, 0),
    'neon_blue': (77, 238, 234),
    'black': (15, 5, 25),
    'dark_blue': (20, 0, 50),
}


def draw_gradient_sky(img: Image.Image) -> Image.Image:
    """Draw a vaporwave sunset gradient background."""
    draw = ImageDraw.Draw(img)
    width, height = img.size

    # Define gradient color stops (top to bottom)
    gradient_colors = [
        (20, 0, 50),      # Dark purple at top
        (75, 0, 130),     # Indigo
        (185, 103, 255),  # Purple
        (255, 113, 206),  # Pink
        (255, 151, 128),  # Coral
        (255, 200, 100),  # Orange/yellow near horizon
    ]

    # Calculate sections
    num_sections = len(gradient_colors) - 1
    section_height = height / num_sections

    for y in range(height):
        # Determine which section we're in
        section = min(int(y / section_height), num_sections - 1)
        section_progress = (y - section * section_height) / section_height

        # Interpolate between colors
        c1 = gradient_colors[section]
        c2 = gradient_colors[section + 1]

        r = int(c1[0] + (c2[0] - c1[0]) * section_progress)
        g = int(c1[1] + (c2[1] - c1[1]) * section_progress)
        b = int(c1[2] + (c2[2] - c1[2]) * section_progress)

        draw.line([(0, y), (width, y)], fill=(r, g, b))

    return img


def draw_sun(img: Image.Image, center_x: int = None, center_y: int = None, radius: int = None) -> Image.Image:
    """Draw a retro striped sun with gradient."""
    width, height = img.size

    if center_x is None:
        center_x = width // 2
    if center_y is None:
        center_y = int(height * 0.45)
    if radius is None:
        radius = int(min(width, height) * 0.18)

    # Create a separate layer for the sun
    sun_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    sun_draw = ImageDraw.Draw(sun_layer)

    # Draw the main sun circle with gradient
    for r in range(radius, 0, -1):
        progress = r / radius
        # Gradient from yellow center to orange/pink edge
        color = (
            255,
            int(220 * progress + 100 * (1 - progress)),
            int(50 + 150 * (1 - progress)),
            255
        )
        sun_draw.ellipse(
            [center_x - r, center_y - r, center_x + r, center_y + r],
            fill=color
        )

    # Add horizontal stripes (VHS sun effect)
    stripe_gap = radius // 8
    stripe_height = stripe_gap // 2

    for i in range(1, 8):
        y_offset = int(radius * 0.2) + i * stripe_gap
        if center_y + y_offset - stripe_height > center_y + radius:
            break

        # Create stripe mask
        y1 = center_y + y_offset - stripe_height
        y2 = center_y + y_offset

        # Draw transparent stripe (cut out from sun)
        for y in range(y1, min(y2, center_y + radius)):
            for x in range(center_x - radius, center_x + radius + 1):
                # Check if point is inside sun circle
                if (x - center_x) ** 2 + (y - center_y) ** 2 <= radius ** 2:
                    sun_layer.putpixel((x, y), (0, 0, 0, 0))

    # Add glow effect
    glow_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_layer)

    for i in range(30, 0, -1):
        alpha = int(8 * (30 - i) / 30)
        glow_color = (255, 180, 100, alpha)
        glow_draw.ellipse(
            [center_x - radius - i * 3, center_y - radius - i * 3,
             center_x + radius + i * 3, center_y + radius + i * 3],
            fill=glow_color
        )

    # Composite layers
    result = img.convert('RGBA')
    result = Image.alpha_composite(result, glow_layer)
    result = Image.alpha_composite(result, sun_layer)

    return result.convert('RGB')


def draw_perspective_grid(img: Image.Image, horizon_y: int = None,
                          grid_color: tuple = None, line_width: int = 2) -> Image.Image:
    """Draw a neon perspective grid on the lower portion of the image."""
    width, height = img.size

    if horizon_y is None:
        horizon_y = int(height * 0.55)
    if grid_color is None:
        grid_color = COLORS['cyan']

    # Create grid layer with alpha
    grid_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(grid_layer)

    # Vanishing point
    vp_x = width // 2
    vp_y = horizon_y

    # Draw vertical lines from vanishing point
    num_lines = 20
    spread = width * 1.5

    for i in range(num_lines + 1):
        x_bottom = int(-spread / 2 + (spread / num_lines) * i + width / 2)

        # Calculate line alpha based on distance from center
        dist_from_center = abs(i - num_lines / 2) / (num_lines / 2)
        alpha = int(255 * (1 - dist_from_center * 0.5))

        color_with_alpha = (*grid_color, alpha)

        draw.line([(vp_x, vp_y), (x_bottom, height)], fill=color_with_alpha, width=line_width)

    # Draw horizontal lines with perspective
    num_horizontal = 15
    for i in range(1, num_horizontal + 1):
        # Use exponential spacing for perspective effect
        progress = (i / num_horizontal) ** 1.8
        y = int(vp_y + (height - vp_y) * progress)

        # Calculate x extent at this y level
        if y <= vp_y:
            continue

        t = (y - vp_y) / (height - vp_y)
        x_left = int(vp_x - spread / 2 * t)
        x_right = int(vp_x + spread / 2 * t)

        # Fade lines that are closer to horizon
        alpha = int(100 + 155 * progress)
        color_with_alpha = (*grid_color, alpha)

        draw.line([(x_left, y), (x_right, y)], fill=color_with_alpha, width=line_width)

    # Add glow effect to grid
    glow = grid_layer.filter(ImageFilter.GaussianBlur(radius=3))

    # Composite
    result = img.convert('RGBA')
    result = Image.alpha_composite(result, glow)
    result = Image.alpha_composite(result, grid_layer)

    return result.convert('RGB')


def draw_palm_tree(draw: ImageDraw.Draw, x: int, y: int, height: int,
                   color: tuple = (0, 0, 0), flip: bool = False):
    """Draw a palm tree silhouette."""
    # Trunk
    trunk_width = height // 15
    trunk_height = height * 2 // 3

    # Draw curved trunk
    points = []
    curve = 20 if not flip else -20
    for i in range(trunk_height):
        progress = i / trunk_height
        offset = int(math.sin(progress * math.pi * 0.5) * curve)
        points.append((x + offset, y - i))

    for i, point in enumerate(points[:-1]):
        width = trunk_width * (1 - i / len(points) * 0.5)
        draw.ellipse([point[0] - width/2, point[1] - 2,
                      point[0] + width/2, point[1] + 2], fill=color)

    # Palm fronds
    frond_start = points[-1]
    num_fronds = 7

    for i in range(num_fronds):
        angle = math.pi * 0.3 + (math.pi * 0.4 / num_fronds) * i
        if flip:
            angle = math.pi - angle

        frond_length = height // 2 + random.randint(-20, 20)

        # Draw curved frond
        prev_point = frond_start
        segments = 15
        for j in range(1, segments + 1):
            t = j / segments
            # Frond curves downward
            droop = t ** 2 * frond_length * 0.4

            fx = frond_start[0] + math.cos(angle) * frond_length * t
            fy = frond_start[1] - math.sin(angle) * frond_length * t + droop

            width = 3 * (1 - t)
            draw.line([prev_point, (fx, fy)], fill=color, width=max(1, int(width)))
            prev_point = (fx, fy)


def draw_palm_trees(img: Image.Image, num_trees: int = 4) -> Image.Image:
    """Add palm tree silhouettes to the image."""
    width, height = img.size
    draw = ImageDraw.Draw(img)

    # Define tree positions and sizes
    trees = [
        {'x': int(width * 0.08), 'height': int(height * 0.5), 'flip': False},
        {'x': int(width * 0.92), 'height': int(height * 0.45), 'flip': True},
        {'x': int(width * 0.15), 'height': int(height * 0.35), 'flip': False},
        {'x': int(width * 0.85), 'height': int(height * 0.38), 'flip': True},
    ]

    for i, tree in enumerate(trees[:num_trees]):
        base_y = int(height * 0.65)
        draw_palm_tree(draw, tree['x'], base_y, tree['height'],
                       color=(10, 5, 20), flip=tree['flip'])

    return img


def draw_geometric_shapes(img: Image.Image) -> Image.Image:
    """Add floating geometric shapes (triangles, circles) with neon effect."""
    width, height = img.size

    # Create shapes layer
    shapes_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(shapes_layer)

    shapes = [
        # Triangles
        {'type': 'triangle', 'x': int(width * 0.2), 'y': int(height * 0.25),
         'size': 40, 'color': COLORS['pink'], 'rotation': 0},
        {'type': 'triangle', 'x': int(width * 0.8), 'y': int(height * 0.3),
         'size': 35, 'color': COLORS['cyan'], 'rotation': 30},
        {'type': 'triangle', 'x': int(width * 0.75), 'y': int(height * 0.15),
         'size': 25, 'color': COLORS['purple'], 'rotation': 15},
        # Circles
        {'type': 'circle', 'x': int(width * 0.25), 'y': int(height * 0.35),
         'size': 20, 'color': COLORS['neon_blue']},
        {'type': 'circle', 'x': int(width * 0.7), 'y': int(height * 0.2),
         'size': 15, 'color': COLORS['hot_pink']},
    ]

    for shape in shapes:
        color = (*shape['color'], 200)

        if shape['type'] == 'triangle':
            size = shape['size']
            cx, cy = shape['x'], shape['y']
            rotation = math.radians(shape.get('rotation', 0))

            # Calculate triangle vertices
            points = []
            for i in range(3):
                angle = rotation + i * 2 * math.pi / 3 - math.pi / 2
                px = cx + size * math.cos(angle)
                py = cy + size * math.sin(angle)
                points.append((px, py))

            # Draw outline with glow
            draw.polygon(points, outline=color, width=2)

        elif shape['type'] == 'circle':
            r = shape['size']
            cx, cy = shape['x'], shape['y']

            # Draw outline circle
            draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=color, width=2)

    # Add glow
    glow = shapes_layer.filter(ImageFilter.GaussianBlur(radius=5))

    result = img.convert('RGBA')
    result = Image.alpha_composite(result, glow)
    result = Image.alpha_composite(result, shapes_layer)

    return result.convert('RGB')


def draw_greek_bust(img: Image.Image, x: int = None, y: int = None,
                    scale: float = 1.0) -> Image.Image:
    """Draw a simplified Greek bust/statue silhouette."""
    width, height = img.size

    if x is None:
        x = int(width * 0.5)
    if y is None:
        y = int(height * 0.4)

    bust_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(bust_layer)

    # Scale factor
    s = scale * (height / 1080)

    # Draw simplified bust outline with marble-like color
    color = (200, 180, 220, 150)  # Light purple/marble

    # Head (oval)
    head_h = int(80 * s)
    head_w = int(55 * s)
    draw.ellipse([x - head_w, y - head_h, x + head_w, y + head_h // 2],
                 outline=color, width=3)

    # Neck
    neck_w = int(25 * s)
    neck_h = int(40 * s)
    draw.rectangle([x - neck_w, y + head_h // 2 - 10, x + neck_w, y + head_h // 2 + neck_h],
                   outline=color, width=3)

    # Shoulders
    shoulder_w = int(100 * s)
    draw.arc([x - shoulder_w, y + head_h // 2 + neck_h - 30,
              x + shoulder_w, y + head_h // 2 + neck_h + int(80 * s)],
             0, 180, fill=color, width=3)

    # Add subtle glow
    glow = bust_layer.filter(ImageFilter.GaussianBlur(radius=4))

    result = img.convert('RGBA')
    result = Image.alpha_composite(result, glow)
    result = Image.alpha_composite(result, bust_layer)

    return result.convert('RGB')
