import math
from PIL import Image, ImageDraw, ImageFont

def generate_wallpaper(filename="/home/abz/abzos/scripts/abzos-dark.png", width=1920, height=1080):
    img = Image.new("RGBA", (width, height), (10, 14, 23, 255))
    draw = ImageDraw.Draw(img)

    # 1. Background gradient
    cx, cy = width // 2, height // 2
    max_radius = math.hypot(cx, cy)
    for y in range(0, height, 4):
        for x in range(0, width, 4):
            dist = math.hypot(x - cx, y - cy) / max_radius
            r = int(14 * (1 - dist * 0.7) + 6 * dist)
            g = int(22 * (1 - dist * 0.7) + 8 * dist)
            b = int(38 * (1 - dist * 0.6) + 14 * dist)
            draw.rectangle([x, y, x + 4, y + 4], fill=(r, g, b, 255))

    # 2. Cyber grid
    grid_color = (25, 45, 75, 40)
    for x in range(0, width, 60):
        draw.line([(x, 0), (x, height)], fill=grid_color, width=1)
    for y in range(0, height, 60):
        draw.line([(0, y), (width, y)], fill=grid_color, width=1)

    # 3. Geometric hex accents & circuit traces
    accent_cyan = (0, 240, 255, 120)
    accent_purple = (168, 85, 247, 90)

    for rad in range(300, 100, -20):
        alpha = int(25 * (1 - rad / 300))
        draw.ellipse([cx - rad, cy - rad, cx + rad, cy + rad], outline=(0, 240, 255, alpha), width=3)

    traces = [
        [(cx - 400, cy - 200), (cx - 250, cy - 200), (cx - 180, cy - 130), (cx - 150, cy - 130)],
        [(cx + 400, cy - 200), (cx + 250, cy - 200), (cx + 180, cy - 130), (cx + 150, cy - 130)],
        [(cx - 450, cy + 180), (cx - 280, cy + 180), (cx - 200, cy + 100), (cx - 150, cy + 100)],
        [(cx + 450, cy + 180), (cx + 280, cy + 180), (cx + 200, cy + 100), (cx + 150, cy + 100)],
        [(cx - 600, cy), (cx - 300, cy), (cx - 250, cy - 50)],
        [(cx + 600, cy), (cx + 300, cy), (cx + 250, cy - 50)],
    ]
    for trace in traces:
        draw.line(trace, fill=accent_cyan, width=2)
        x_end, y_end = trace[0]
        draw.ellipse([x_end - 4, y_end - 4, x_end + 4, y_end + 4], fill=(0, 240, 255, 200))
        x_end2, y_end2 = trace[-1]
        draw.ellipse([x_end2 - 4, y_end2 - 4, x_end2 + 4, y_end2 + 4], fill=(168, 85, 247, 220))

    # 4. Central Shield / Hexagon
    hex_size = 110
    points = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        px = cx + hex_size * math.cos(angle)
        py = cy - 35 + hex_size * math.sin(angle)
        points.append((px, py))

    draw.polygon(points, outline=(0, 240, 255, 200), width=3)
    inner_points = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        px = cx + (hex_size - 14) * math.cos(angle)
        py = cy - 35 + (hex_size - 14) * math.sin(angle)
        inner_points.append((px, py))
    draw.polygon(inner_points, fill=(15, 28, 50, 180), outline=(168, 85, 247, 180), width=2)

    # Terminal glyph >_
    draw.line([(cx - 45, cy - 60), (cx - 15, cy - 35), (cx - 45, cy - 10)], fill=(0, 240, 255, 240), width=5)
    draw.line([(cx - 5, cy - 10), (cx + 35, cy - 10)], fill=(0, 240, 255, 240), width=5)
    draw.arc([cx - 15, cy - 65, cx + 15, cy - 40], start=180, end=0, fill=(168, 85, 247, 220), width=3)

    # 5. Text
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 46)
        font_sub = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 15)
        font_ver = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 13)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub = ImageFont.load_default()
        font_ver = ImageFont.load_default()

    title_text = "abzOS"
    bbox = draw.textbbox((0, 0), title_text, font=font_title)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - tw // 2, cy + 95), title_text, fill=(240, 246, 252, 240), font=font_title)

    ver_text = "v1.0 ROLLING"
    bbox_v = draw.textbbox((0, 0), ver_text, font=font_ver)
    vw = bbox_v[2] - bbox_v[0]
    draw.rectangle([cx - vw // 2 - 10, cy + 150, cx + vw // 2 + 10, cy + 170], fill=(0, 240, 255, 40), outline=(0, 240, 255, 120))
    draw.text((cx - vw // 2, cy + 152), ver_text, fill=(0, 240, 255, 240), font=font_ver)

    sub_text = "DEVELOPER  &  CYBERSECURITY  EDITION"
    bbox2 = draw.textbbox((0, 0), sub_text, font=font_sub)
    sw = bbox2[2] - bbox2[0]
    draw.text((cx - sw // 2, cy + 185), sub_text, fill=(140, 160, 185, 220), font=font_sub)

    # Bottom status bar line
    draw.line([(width // 4, height - 60), (width * 3 // 4, height - 60)], fill=(0, 240, 255, 60), width=1)
    foot_text = "DEBIAN 12 BOOKWORM  |  XFCE DESKTOP  |  SECURITY TOOLKIT"
    bbox3 = draw.textbbox((0, 0), foot_text, font=font_ver)
    fw = bbox3[2] - bbox3[0]
    draw.text((cx - fw // 2, height - 50), foot_text, fill=(90, 110, 135, 180), font=font_ver)

    rgb_img = img.convert("RGB")
    rgb_img.save(filename, "PNG", quality=95)
    print(f"Generated wallpaper: {filename}")

def generate_logo(filename="/home/abz/abzos/scripts/abzos-logo.png", size=128):
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy = size // 2, size // 2
    r = size // 2 - 6

    points = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        px = cx + r * math.cos(angle)
        py = cy + r * math.sin(angle)
        points.append((px, py))
    draw.polygon(points, fill=(15, 23, 42, 240), outline=(0, 240, 255, 255), width=3)

    inner_points = []
    for i in range(6):
        angle = math.radians(60 * i - 30)
        px = cx + (r - 8) * math.cos(angle)
        py = cy + (r - 8) * math.sin(angle)
        inner_points.append((px, py))
    draw.polygon(inner_points, outline=(168, 85, 247, 180), width=1)

    draw.line([(cx - 24, cy - 18), (cx - 6, cy), (cx - 24, cy + 18)], fill=(0, 240, 255, 255), width=4)
    draw.line([(cx + 2, cy + 18), (cx + 24, cy + 18)], fill=(0, 240, 255, 255), width=4)

    img.save(filename, "PNG")
    print(f"Generated logo: {filename}")

if __name__ == "__main__":
    generate_wallpaper()
    generate_logo()
