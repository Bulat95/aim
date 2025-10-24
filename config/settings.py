# config/settings.py
# -*- coding: utf-8 -*-
"""
Глобальные настройки приложения
"""

# Цветовая палитра (темная тема)
COLORS = {
    'bg_primary': '#1e1e1e',
    'bg_secondary': '#2d2d2d',
    'bg_chat_user': '#2e5c8a',
    'bg_chat_character': '#3d3d3d',
    'text_primary': '#ffffff',
    'text_secondary': '#b0b0b0',
    'accent': '#3a86ff',
    'online': '#2ecc71',
    'hover': '#404040'
}

# Размеры окна
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
MIN_WIDTH = 1000
MIN_HEIGHT = 600

# Размеры компонентов
SIDEBAR_WIDTH = 280
AVATAR_SIZE = 40
AVATAR_SIZE_SMALL = 30

# Пути к директориям
CHARACTERS_DIR = "characters"
GROUPS_DIR = "groups"
CHATS_DIR = "chats"
PROVIDERS_PATH = "config/providers.yml"

# Настройки истории
MAX_MESSAGES_IN_HISTORY = 100
MAX_MESSAGES_FOR_API = 15
