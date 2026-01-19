"""
Vaporwave visual effects for wallpaper generation.
Includes scanlines, noise, chromatic aberration, and glow effects.
Uses only PIL/Pillow without numpy dependency.
"""

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageChops
import random


def add_scanlines(img: Image.Image, opacity: float = 0.15,
                  line_spacing: int = 4) -> Image.Image:
    """Add VHS-style horizontal scanlines."""
    width, height = img.size

    # Create scanline overlay
    scanline_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(scanline_layer)

    # Draw dark horizontal lines
    alpha = int(255 * opacity)
    for y in range(0, height, line_spacing):
        draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha), width=1)

    # Composite with original
    result = img.convert('RGBA')
    result = Image.alpha_composite(result, scanline_layer)

    return result.convert('RGB')


def add_noise(img: Image.Image, intensity: float = 0.05) -> Image.Image:
    """Add film grain / noise overlay using PIL."""
    width, height = img.size

    # Create noise layer
    noise_layer = Image.new('RGB', img.size)
    pixels = noise_layer.load()

    noise_range = int(255 * intensity)

    for y in range(height):
        for x in range(width):
            noise_val = random.randint(-noise_range, noise_range)
            # Apply same noise to all channels for grayscale grain
            pixels[x, y] = (128 + noise_val, 128 + noise_val, 128 + noise_val)

    # Blend noise with original using overlay-like effect
    # Convert both to same mode
    result = img.convert('RGB')

    # Blend: for each pixel, add (noise - 128) to original
    result_pixels = result.load()
    for y in range(height):
        for x in range(width):
            orig = result_pixels[x, y]
            noise = pixels[x, y][0] - 128  # Noise offset

            r = max(0, min(255, orig[0] + noise))
            g = max(0, min(255, orig[1] + noise))
            b = max(0, min(255, orig[2] + noise))
            result_pixels[x, y] = (r, g, b)

    return result


def add_chromatic_aberration(img: Image.Image, offset: int = 3) -> Image.Image:
    """Add RGB split / chromatic aberration effect using PIL."""
    # Split into channels
    r, g, b = img.split()

    # Shift red channel left by cropping and padding
    r_shifted = Image.new('L', r.size, 0)
    r_cropped = r.crop((offset, 0, r.width, r.height))
    r_shifted.paste(r_cropped, (0, 0))

    # Shift blue channel right by cropping and padding
    b_shifted = Image.new('L', b.size, 0)
    b_cropped = b.crop((0, 0, b.width - offset, b.height))
    b_shifted.paste(b_cropped, (offset, 0))

    # Merge channels back
    result = Image.merge('RGB', (r_shifted, g, b_shifted))

    return result


def add_glitch_strips(img: Image.Image, num_strips: int = 5,
                      max_offset: int = 20) -> Image.Image:
    """Add horizontal glitch strips (displaced sections) using PIL."""
    result = img.copy()
    width, height = img.size

    for _ in range(num_strips):
        # Random strip position and size
        y_start = random.randint(0, height - 30)
        strip_height = random.randint(5, 25)
        y_end = min(y_start + strip_height, height)

        # Random offset
        offset = random.randint(-max_offset, max_offset)

        # Extract the strip
        strip = img.crop((0, y_start, width, y_end))

        # Create shifted version
        shifted = Image.new('RGB', (width, y_end - y_start))

        if offset > 0:
            # Shift right
            shifted.paste(strip.crop((0, 0, width - offset, y_end - y_start)), (offset, 0))
            shifted.paste(strip.crop((width - offset, 0, width, y_end - y_start)), (0, 0))
        elif offset < 0:
            # Shift left
            offset = abs(offset)
            shifted.paste(strip.crop((offset, 0, width, y_end - y_start)), (0, 0))
            shifted.paste(strip.crop((0, 0, offset, y_end - y_start)), (width - offset, 0))
        else:
            shifted = strip

        # Paste back
        result.paste(shifted, (0, y_start))

    return result


def add_vignette(img: Image.Image, strength: float = 0.4) -> Image.Image:
    """Add a dark vignette effect around the edges."""
    width, height = img.size

    # Create vignette mask using radial gradient
    vignette = Image.new('L', img.size, 255)

    cx, cy = width // 2, height // 2
    max_dist = ((cx ** 2 + cy ** 2) ** 0.5)

    # Use a more efficient approach - draw concentric ellipses
    draw = ImageDraw.Draw(vignette)

    # Create gradient by drawing filled ellipses from outer (dark) to inner (light)
    steps = 50
    for i in range(steps):
        # From outer to inner
        progress = i / steps
        # Inverse progress for drawing (outer first)
        inv_progress = 1 - progress

        # Calculate ellipse size
        rx = int(cx * (1 + inv_progress * 0.8))
        ry = int(cy * (1 + inv_progress * 0.8))

        # Calculate brightness (darker at edges)
        brightness = int(255 * (1 - strength * (inv_progress ** 1.5)))

        draw.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=brightness)

    # Apply vignette as mask
    r, g, b = img.split()

    r = ImageChops.multiply(r, vignette)
    g = ImageChops.multiply(g, vignette)
    b = ImageChops.multiply(b, vignette)

    # Normalize back (multiply darkens, so we need to compensate)
    r = Image.eval(r, lambda x: min(255, int(x * 255 / 200)))
    g = Image.eval(g, lambda x: min(255, int(x * 255 / 200)))
    b = Image.eval(b, lambda x: min(255, int(x * 255 / 200)))

    return Image.merge('RGB', (r, g, b))


def add_glow_to_layer(layer: Image.Image, radius: int = 10,
                      intensity: float = 1.5) -> Image.Image:
    """Add a glow effect to a layer with transparency."""
    # Create glow by blurring
    glow = layer.filter(ImageFilter.GaussianBlur(radius=radius))

    # Enhance brightness
    enhancer = ImageEnhance.Brightness(glow)
    glow = enhancer.enhance(intensity)

    # Composite: glow under, original on top
    result = Image.alpha_composite(glow, layer)

    return result


def add_color_boost(img: Image.Image, saturation: float = 1.3,
                    contrast: float = 1.1) -> Image.Image:
    """Boost colors for that vibrant vaporwave look."""
    # Enhance saturation
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(saturation)

    # Enhance contrast
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(contrast)

    return img


def apply_all_effects(img: Image.Image,
                      scanlines: bool = True,
                      noise: bool = True,
                      chromatic: bool = True,
                      glitch: bool = False,
                      vignette: bool = True,
                      color_boost: bool = True) -> Image.Image:
    """Apply all vaporwave effects to an image."""

    if color_boost:
        img = add_color_boost(img, saturation=1.2, contrast=1.05)

    if chromatic:
        img = add_chromatic_aberration(img, offset=2)

    if glitch:
        img = add_glitch_strips(img, num_strips=3, max_offset=15)

    if scanlines:
        img = add_scanlines(img, opacity=0.12, line_spacing=3)

    if noise:
        img = add_noise(img, intensity=0.03)

    if vignette:
        img = add_vignette(img, strength=0.35)

    return img
