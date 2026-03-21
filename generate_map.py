import math
from PIL import Image, ImageDraw

def generate_cyber_map(width=2048, height=1024, output_path="build/web/public/assets/images/cyber_earth_map.jpg"):
    img = Image.new('RGB', (width, height), '#0A0E17')
    draw = ImageDraw.Draw(img)

    # Let's create a cool grid/matrix pattern that looks vaguely geographical or at least sci-fi
    # A simple glowing grid on a dark background
    grid_size = 32
    for x in range(0, width, grid_size):
        draw.line([(x, 0), (x, height)], fill='#001122', width=1)
    for y in range(0, height, grid_size):
        draw.line([(0, y), (width, y)], fill='#001122', width=1)

    # Add some random digital "continents" using simple noise or patterns
    import random
    random.seed(42)

    # Very simple generative continents
    for _ in range(2000):
        cx = random.randint(0, width)
        cy = random.randint(0, height)

        # Keep away from poles mostly for equirectangular map
        lat = (cy / height) * math.pi - (math.pi / 2)
        if abs(math.sin(lat)) > 0.8:
            continue

        size = random.randint(1, 4) * grid_size

        # Determine color (glowing green/blue)
        color = random.choice(['#00FF88', '#004433', '#002233', '#00AAFF'])

        # Make a blocky continent piece
        x1 = (cx // grid_size) * grid_size
        y1 = (cy // grid_size) * grid_size
        x2 = x1 + size
        y2 = y1 + size

        # Only draw if probability matches to make it scattered
        if random.random() > 0.5:
            # draw a filled block, but make it dark inside with a glowing border
            # Since Pillow doesn't do "glow", we just use specific colors
            draw.rectangle([x1, y1, x2, y2], outline=color, fill='#0d1a22')

    # Add some horizontal scanlines
    for y in range(0, height, 4):
        draw.line([(0, y), (width, y)], fill='#000000', width=1)

    img.save(output_path, quality=90)
    print(f"Saved {output_path}")

if __name__ == "__main__":
    generate_cyber_map()
