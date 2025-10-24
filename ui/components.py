# ui/components.py
# -*- coding: utf-8 -*-
"""
UI компоненты (генерация аватарок, утилиты)
"""
from PIL import Image, ImageTk, ImageDraw
from colorsys import hsv_to_rgb
from datetime import datetime
from config.settings import AVATAR_SIZE

def generate_placeholder_avatar(name: str, size: int = AVATAR_SIZE):
    """Генерирует заглушку аватарки с первой буквой имени."""
    color_hash = hash(name) % 360
    r, g, b = hsv_to_rgb(color_hash / 360, 0.6, 0.9)
    bg_color = (int(r * 255), int(g * 255), int(b * 255))
    
    image = Image.new('RGB', (size, size), bg_color)
    draw = ImageDraw.Draw(image)
    draw.ellipse([0, 0, size, size], fill=bg_color)
    
    try:
        from PIL import ImageFont
        font_size = int(size * 0.5)
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
    except:
        font = None
    
    letter = name[0].upper() if name else '?'
    
    if font:
        bbox = draw.textbbox((0, 0), letter, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    else:
        text_width = size // 3
        text_height = size // 3
    
    text_x = (size - text_width) // 2
    text_y = (size - text_height) // 2
    draw.text((text_x, text_y), letter, fill='white', font=font)
    
    return ImageTk.PhotoImage(image)

def format_timestamp(iso_timestamp: str) -> str:
    """Форматирует ISO timestamp в читаемый формат."""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime("%H:%M")
    except:
        return ""
