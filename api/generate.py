"""
Vercel serverless function for generating minimalist wallpapers.
Returns a PNG image based on goals.json configuration.
"""

import json
import sys
from io import BytesIO
from pathlib import Path
from http.server import BaseHTTPRequestHandler

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.wallpaper import generate_wallpaper


# Load goals configuration
GOALS_PATH = Path(__file__).parent.parent / 'goals.json'


def load_goals():
    """Load goals from configuration file."""
    try:
        with open(GOALS_PATH, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        # Return default goals if file not found
        return {
            "title": "2026 GOALS",
            "resolution": [1920, 1080],
            "goals": [
                {"name": "Goal 1", "current": 50, "target": 100},
                {"name": "Goal 2", "current": 30, "target": 100},
                {"name": "Goal 3", "current": 75, "target": 100},
            ]
        }


class handler(BaseHTTPRequestHandler):
    """Vercel serverless function handler."""

    def do_GET(self):
        """Handle GET requests - generate and return wallpaper image."""
        try:
            # Parse query parameters for optional overrides
            from urllib.parse import urlparse, parse_qs
            query = parse_qs(urlparse(self.path).query)

            # Load base goals config
            goals_config = load_goals()

            # Allow resolution override via query params
            if 'width' in query and 'height' in query:
                try:
                    width = int(query['width'][0])
                    height = int(query['height'][0])
                    goals_config['resolution'] = [width, height]
                except (ValueError, IndexError):
                    pass

            # Generate wallpaper
            img = generate_wallpaper(goals_config)

            # Convert to bytes
            buffer = BytesIO()
            img.save(buffer, format='PNG', quality=95)
            buffer.seek(0)
            image_data = buffer.getvalue()

            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.send_header('Content-Length', len(image_data))
            self.send_header('Cache-Control', 'public, max-age=300')  # Cache for 5 minutes
            self.end_headers()
            self.wfile.write(image_data)

        except Exception as e:
            # Return error as JSON
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_response = json.dumps({'error': str(e)})
            self.wfile.write(error_response.encode())

    def do_POST(self):
        """Handle POST requests - generate wallpaper with custom goals."""
        try:
            # Read request body
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            # Parse JSON body as goals config
            goals_config = json.loads(body.decode('utf-8'))

            # Ensure required fields
            if 'resolution' not in goals_config:
                goals_config['resolution'] = [1920, 1080]
            if 'goals' not in goals_config:
                goals_config['goals'] = []
            if 'title' not in goals_config:
                goals_config['title'] = 'GOALS'

            # Generate wallpaper
            img = generate_wallpaper(goals_config)

            # Convert to bytes
            buffer = BytesIO()
            img.save(buffer, format='PNG', quality=95)
            buffer.seek(0)
            image_data = buffer.getvalue()

            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'image/png')
            self.send_header('Content-Length', len(image_data))
            self.end_headers()
            self.wfile.write(image_data)

        except json.JSONDecodeError:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Invalid JSON'}).encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'error': str(e)}).encode())
