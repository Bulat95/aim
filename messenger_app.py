# messenger_app.py
# -*- coding: utf-8 -*-
"""
Desktop-мессенджер для общения с NPC-персонажами через API нейросетей
Автор: Проект на основе proxy5.py
Дата: 2025-10-23
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from tkinter import font as tkfont
import json
import os
import yaml
from datetime import datetime
from threading import Thread
import time
from PIL import Image, ImageTk, ImageDraw
from api_handler import MessengerAPI

# ==================== КОНСТАНТЫ ====================

# Цветовая палитра (темная тема)
COLORS = {
    'bg_primary': '#1e1e1e',        # Основной фон
    'bg_secondary': '#2d2d2d',      # Вторичный фон
    'bg_chat_user': '#2e5c8a',      # Сообщения пользователя
    'bg_chat_character': '#3d3d3d', # Сообщения персонажа
    'text_primary': '#ffffff',      # Основной текст
    'text_secondary': '#b0b0b0',    # Вторичный текст
    'accent': '#3a86ff',            # Акцентный цвет (кнопки)
    'online': '#2ecc71',            # Статус онлайн
    'hover': '#404040'              # Цвет при наведении
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
CHATS_DIR = "chats_1"

# Настройки
MAX_MESSAGES_IN_HISTORY = 100  # Максимальное количество сообщений в истории
MAX_MESSAGES_FOR_API = 15      # Количество сообщений для отправки в API


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def ensure_directories():
    """Создает необходимые директории если их нет."""
    for directory in [CHARACTERS_DIR, GROUPS_DIR, CHATS_DIR]:
        os.makedirs(directory, exist_ok=True)


def generate_placeholder_avatar(name, size=AVATAR_SIZE):
    """
    Генерирует заглушку аватарки: круг с первой буквой имени.

    Args:
        name: Имя персонажа
        size: Размер аватарки в пикселях

    Returns:
        ImageTk.PhotoImage объект
    """
    # Генерируем цвет на основе хеша имени
    color_hash = hash(name) % 360
    from colorsys import hsv_to_rgb
    r, g, b = hsv_to_rgb(color_hash / 360, 0.6, 0.9)
    bg_color = (int(r * 255), int(g * 255), int(b * 255))

    # Создаем изображение
    image = Image.new('RGB', (size, size), bg_color)
    draw = ImageDraw.Draw(image)

    # Рисуем круг
    draw.ellipse([0, 0, size, size], fill=bg_color)

    # Добавляем первую букву
    try:
        from PIL import ImageFont
        font_size = int(size * 0.5)
        # Пытаемся использовать системный шрифт
        try:
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()
    except:
        font = None

    letter = name[0].upper() if name else '?'

    # Вычисляем позицию для центрирования текста
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


def format_timestamp(iso_timestamp):
    """
    Форматирует ISO timestamp в читаемый формат (ЧЧ:ММ).

    Args:
        iso_timestamp: Строка в ISO формате

    Returns:
        Строка в формате "14:30"
    """
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime("%H:%M")
    except:
        return ""


# ==================== КЛАСС МЕССЕНДЖЕРА ====================

class MessengerApp:
    """Основной класс приложения мессенджера."""

    def __init__(self, root):
        """
        Инициализация приложения.

        Args:
            root: Корневое окно Tkinter
        """
        self.root = root
        self.root.title("AI Messenger")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.root.configure(bg=COLORS['bg_primary'])

        # Загрузка данных
        self.characters = {}       # {character_id: character_data}
        self.groups = {}           # {group_id: group_data}
        self.chats = {}            # {chat_id: messages_list}
        self.current_chat_id = None
        self.typing_indicators = {}  # {chat_id: is_typing}

        # API handler
        self.api = MessengerAPI()

        # Инициализация
        ensure_directories()
        self.load_characters()
        self.load_groups()
        self.load_all_chats()

        # Создание GUI
        self.create_gui()

        # Если есть чаты, открыть первый
        if self.chats:
            first_chat_id = list(self.chats.keys())[0]
            self.open_chat(first_chat_id)

    # ---------- ЗАГРУЗКА ДАННЫХ ----------

    def load_characters(self):
        """Загружает всех персонажей из папки characters/."""
        if not os.path.exists(CHARACTERS_DIR):
            return

        for character_folder in os.listdir(CHARACTERS_DIR):
            char_path = os.path.join(CHARACTERS_DIR, character_folder)
            if not os.path.isdir(char_path):
                continue

            config_path = os.path.join(char_path, "character.yml")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    char_data = yaml.safe_load(f)
                    self.characters[char_data['id']] = char_data

        print(f"Загружено персонажей: {len(self.characters)}")

    def load_groups(self):
        """Загружает все группы из папки groups/."""
        if not os.path.exists(GROUPS_DIR):
            return

        for group_file in os.listdir(GROUPS_DIR):
            if group_file.endswith('.yml'):
                with open(os.path.join(GROUPS_DIR, group_file), 'r', encoding='utf-8') as f:
                    group_data = yaml.safe_load(f)
                    self.groups[group_data['id']] = group_data

        print(f"Загружено групп: {len(self.groups)}")

    def load_all_chats(self):
        """Загружает все истории чатов из папки chats_1/."""
        if not os.path.exists(CHATS_DIR):
            print(f"Папка {CHATS_DIR} не найдена, создаем...")
            os.makedirs(CHATS_DIR, exist_ok=True)
            return

        for chat_file in os.listdir(CHATS_DIR):
            if chat_file.endswith('.json'):
                chat_id = chat_file.replace('.json', '')
                try:
                    history = self.load_chat_history(chat_id)
                    self.chats[chat_id] = history
                    print(f"Загружен чат: {chat_id} ({len(history)} сообщений)")
                except Exception as e:
                    print(f"Не удалось загрузить чат {chat_id}: {e}")
                    self.chats[chat_id] = []

    def load_chat_history(self, chat_id):
        """
        Загружает историю конкретного чата.

        Args:
            chat_id: ID чата

        Returns:
            Список сообщений или пустой список
        """
        chat_path = os.path.join(CHATS_DIR, f"{chat_id}.json")
        if os.path.exists(chat_path):
            try:
                with open(chat_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    # Проверяем, не пустой ли файл
                    if not content:
                        print(f"Предупреждение: Файл {chat_path} пустой, создаем новую историю")
                        return []

                    data = json.loads(content)
                    return data.get('messages', [])
            except json.JSONDecodeError as e:
                print(f"Ошибка чтения JSON из {chat_path}: {e}")
                print(f"Файл будет пересоздан при следующем сохранении")
                return []
            except Exception as e:
                print(f"Неожиданная ошибка при загрузке {chat_path}: {e}")
                return []
        return []

    def save_chat_history(self, chat_id):
        """
        Сохраняет историю чата в JSON файл.

        Args:
            chat_id: ID чата
        """
        # Определяем тип чата
        if chat_id in self.groups:
            chat_type = 'group'
            character_id = None
        else:
            chat_type = 'private'
            character_id = chat_id

        chat_data = {
            'chat_id': chat_id,
            'chat_type': chat_type,
            'character_id': character_id,
            'messages': self.chats.get(chat_id, [])[-MAX_MESSAGES_IN_HISTORY:]
        }

        chat_path = os.path.join(CHATS_DIR, f"{chat_id}.json")
        with open(chat_path, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, ensure_ascii=False, indent=2)

    # ---------- СОЗДАНИЕ GUI ----------

    def create_gui(self):
        """Создает основной графический интерфейс."""
        # Главный контейнер
        main_container = tk.Frame(self.root, bg=COLORS['bg_primary'])
        main_container.pack(fill=tk.BOTH, expand=True)

        # Левая панель (список чатов)
        self.create_sidebar(main_container)

        # Основная область чата
        self.create_chat_area(main_container)

    def create_sidebar(self, parent):
        """
        Создает левую панель со списком чатов.

        Args:
            parent: Родительский виджет
        """
        sidebar = tk.Frame(parent, bg=COLORS['bg_secondary'], width=SIDEBAR_WIDTH)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        sidebar.pack_propagate(False)

        # Заголовок
        header = tk.Label(
            sidebar,
            text="Чаты",
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            font=('Arial', 16, 'bold'),
            pady=15
        )
        header.pack(fill=tk.X)

        # Поле поиска (заглушка)
        search_frame = tk.Frame(sidebar, bg=COLORS['bg_secondary'])
        search_frame.pack(fill=tk.X, padx=10, pady=5)

        search_entry = tk.Entry(
            search_frame,
            bg=COLORS['bg_primary'],
            fg=COLORS['text_secondary'],
            insertbackground=COLORS['text_primary'],
            relief=tk.FLAT,
            font=('Arial', 10)
        )
        search_entry.insert(0, "🔍 Поиск...")
        search_entry.pack(fill=tk.X, ipady=5)

        # Список чатов
        chats_frame = tk.Frame(sidebar, bg=COLORS['bg_secondary'])
        chats_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Canvas для скролла
        canvas = tk.Canvas(chats_frame, bg=COLORS['bg_secondary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(chats_frame, orient="vertical", command=canvas.yview)
        self.chats_container = tk.Frame(canvas, bg=COLORS['bg_secondary'])

        self.chats_container.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.chats_container, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Заполняем список чатов
        self.populate_chats_list()

        # Кнопка "Создать группу"
        create_group_btn = tk.Button(
            sidebar,
            text="➕ Создать группу",
            bg=COLORS['accent'],
            fg=COLORS['text_primary'],
            relief=tk.FLAT,
            font=('Arial', 10, 'bold'),
            pady=10,
            cursor='hand2',
            command=self.create_group_dialog
        )
        create_group_btn.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)

    def populate_chats_list(self):
        """Заполняет список чатов в sidebar."""
        # Очищаем текущий список
        for widget in self.chats_container.winfo_children():
            widget.destroy()

        # Добавляем личные чаты
        for char_id, char_data in self.characters.items():
            self.create_chat_item(char_id, char_data['name'], 'private')

        # Добавляем групповые чаты
        for group_id, group_data in self.groups.items():
            self.create_chat_item(group_id, group_data['name'], 'group')

    def create_chat_item(self, chat_id, name, chat_type):
        """
        Создает элемент чата в списке.

        Args:
            chat_id: ID чата
            name: Имя чата
            chat_type: Тип чата ('private' или 'group')
        """
        item_frame = tk.Frame(
            self.chats_container,
            bg=COLORS['bg_secondary'],
            cursor='hand2'
        )
        item_frame.pack(fill=tk.X, pady=2)
        item_frame.bind('<Button-1>', lambda e: self.open_chat(chat_id))

        # Контейнер для аватарки и текста
        content_frame = tk.Frame(item_frame, bg=COLORS['bg_secondary'])
        content_frame.pack(fill=tk.X, padx=10, pady=8)

        # Аватарка
        avatar = generate_placeholder_avatar(name, AVATAR_SIZE_SMALL)
        avatar_label = tk.Label(content_frame, image=avatar, bg=COLORS['bg_secondary'])
        avatar_label.image = avatar  # Сохраняем ссылку
        avatar_label.pack(side=tk.LEFT, padx=(0, 10))

        # Текстовая информация
        text_frame = tk.Frame(content_frame, bg=COLORS['bg_secondary'])
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Имя
        name_label = tk.Label(
            text_frame,
            text=name,
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            font=('Arial', 11, 'bold'),
            anchor='w'
        )
        name_label.pack(fill=tk.X)

        # Последнее сообщение (превью)
        last_msg = self.get_last_message_preview(chat_id)
        preview_label = tk.Label(
            text_frame,
            text=last_msg,
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary'],
            font=('Arial', 9),
            anchor='w'
        )
        preview_label.pack(fill=tk.X)

        # Hover эффект
        def on_enter(e):
            item_frame.config(bg=COLORS['hover'])
            content_frame.config(bg=COLORS['hover'])
            text_frame.config(bg=COLORS['hover'])
            name_label.config(bg=COLORS['hover'])
            preview_label.config(bg=COLORS['hover'])
            avatar_label.config(bg=COLORS['hover'])

        def on_leave(e):
            item_frame.config(bg=COLORS['bg_secondary'])
            content_frame.config(bg=COLORS['bg_secondary'])
            text_frame.config(bg=COLORS['bg_secondary'])
            name_label.config(bg=COLORS['bg_secondary'])
            preview_label.config(bg=COLORS['bg_secondary'])
            avatar_label.config(bg=COLORS['bg_secondary'])

        item_frame.bind('<Enter>', on_enter)
        item_frame.bind('<Leave>', on_leave)

    def get_last_message_preview(self, chat_id):
        """
        Получает превью последнего сообщения в чате.

        Args:
            chat_id: ID чата

        Returns:
            Строка с превью сообщения
        """
        messages = self.chats.get(chat_id, [])
        if not messages:
            return "Нет сообщений"

        last_msg = messages[-1]
        if last_msg['type'] == 'text':
            text = last_msg['text']
            return text[:40] + '...' if len(text) > 40 else text
        elif last_msg['type'] == 'photo':
            return "📷 Фото"
        return ""

    # Продолжение в следующей части...

    def create_chat_area(self, parent):
        """
        Создает основную область чата.

        Args:
            parent: Родительский виджет
        """
        chat_area = tk.Frame(parent, bg=COLORS['bg_primary'])
        chat_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Заголовок чата
        self.chat_header = tk.Frame(chat_area, bg=COLORS['bg_secondary'], height=70)
        self.chat_header.pack(fill=tk.X)
        self.chat_header.pack_propagate(False)

        # Контент заголовка
        header_content = tk.Frame(self.chat_header, bg=COLORS['bg_secondary'])
        header_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

        # Аватарка в заголовке
        self.header_avatar_label = tk.Label(
            header_content,
            bg=COLORS['bg_secondary']
        )
        self.header_avatar_label.pack(side=tk.LEFT, padx=(0, 15))

        # Информация о чате
        info_frame = tk.Frame(header_content, bg=COLORS['bg_secondary'])
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.header_name_label = tk.Label(
            info_frame,
            text="",
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            font=('Arial', 14, 'bold'),
            anchor='w'
        )
        self.header_name_label.pack(fill=tk.X)

        self.header_status_label = tk.Label(
            info_frame,
            text="● онлайн",
            bg=COLORS['bg_secondary'],
            fg=COLORS['online'],
            font=('Arial', 10),
            anchor='w'
        )
        self.header_status_label.pack(fill=tk.X)

        # Область сообщений
        messages_frame = tk.Frame(chat_area, bg=COLORS['bg_primary'])
        messages_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Canvas для скролла
        self.messages_canvas = tk.Canvas(
            messages_frame,
            bg=COLORS['bg_primary'],
            highlightthickness=0
        )
        messages_scrollbar = ttk.Scrollbar(
            messages_frame,
            orient="vertical",
            command=self.messages_canvas.yview
        )
        self.messages_container = tk.Frame(self.messages_canvas, bg=COLORS['bg_primary'])

        self.messages_container.bind(
            "<Configure>",
            lambda e: self.messages_canvas.configure(scrollregion=self.messages_canvas.bbox("all"))
        )

        self.messages_canvas.create_window((0, 0), window=self.messages_container, anchor="nw")
        self.messages_canvas.configure(yscrollcommand=messages_scrollbar.set)

        self.messages_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        messages_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Поле ввода
        input_frame = tk.Frame(chat_area, bg=COLORS['bg_secondary'])
        input_frame.pack(fill=tk.X, padx=10, pady=10)

        # Кнопки-заглушки
        buttons_frame = tk.Frame(input_frame, bg=COLORS['bg_secondary'])
        buttons_frame.pack(side=tk.LEFT, padx=(10, 5))

        attach_btn = tk.Button(
            buttons_frame,
            text="📎",
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary'],
            relief=tk.FLAT,
            font=('Arial', 14),
            cursor='hand2',
            command=lambda: messagebox.showinfo("В разработке", "Функция в разработке")
        )
        attach_btn.pack(side=tk.LEFT, padx=2)

        emoji_btn = tk.Button(
            buttons_frame,
            text="😊",
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary'],
            relief=tk.FLAT,
            font=('Arial', 14),
            cursor='hand2',
            command=lambda: messagebox.showinfo("В разработке", "Функция в разработке")
        )
        emoji_btn.pack(side=tk.LEFT, padx=2)

        # Текстовое поле
        self.message_text = tk.Text(
            input_frame,
            bg=COLORS['bg_primary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            relief=tk.FLAT,
            font=('Arial', 11),
            height=3,
            wrap=tk.WORD
        )
        self.message_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)

        # Биндинг клавиш
        self.message_text.bind('<Return>', self.on_enter_press)
        self.message_text.bind('<Shift-Return>', lambda e: None)  # Новая строка

        # Кнопка отправки
        send_btn = tk.Button(
            input_frame,
            text="📤",
            bg=COLORS['accent'],
            fg=COLORS['text_primary'],
            relief=tk.FLAT,
            font=('Arial', 16),
            cursor='hand2',
            width=3,
            command=self.send_message
        )
        send_btn.pack(side=tk.RIGHT, padx=10)

    def on_enter_press(self, event):
        """Обработка нажатия Enter."""
        # Если нажат Shift+Enter - новая строка, иначе - отправка
        if not event.state & 0x1:  # Без Shift
            self.send_message()
            return 'break'  # Предотвращаем добавление новой строки

    # ---------- ОТОБРАЖЕНИЕ ЧАТА ----------

    def open_chat(self, chat_id):
        """
        Открывает чат и отображает историю сообщений.

        Args:
            chat_id: ID чата
        """
        self.current_chat_id = chat_id

        # Обновляем заголовок
        if chat_id in self.characters:
            char_data = self.characters[chat_id]
            name = char_data['name']
        elif chat_id in self.groups:
            name = self.groups[chat_id]['name']
        else:
            name = chat_id

        # Обновляем аватарку и имя
        avatar = generate_placeholder_avatar(name, AVATAR_SIZE)
        self.header_avatar_label.config(image=avatar)
        self.header_avatar_label.image = avatar
        self.header_name_label.config(text=name)

        # Отображаем сообщения
        self.display_messages()

    def display_messages(self):
        """Отображает все сообщения текущего чата."""
        # Очищаем контейнер
        for widget in self.messages_container.winfo_children():
            widget.destroy()

        messages = self.chats.get(self.current_chat_id, [])

        for msg in messages:
            self.add_message_to_display(msg)

        # Прокручиваем вниз
        self.messages_canvas.update_idletasks()
        self.messages_canvas.yview_moveto(1.0)

    def add_message_to_display(self, message):
        """
        Добавляет одно сообщение в область отображения.

        Args:
            message: Словарь с данными сообщения
        """
        sender = message['sender']
        msg_type = message['type']
        timestamp = format_timestamp(message['timestamp'])

        # Определяем выравнивание и цвет
        if sender == 'user':
            anchor = 'e'  # Справа
            bg_color = COLORS['bg_chat_user']
        else:
            anchor = 'w'  # Слева
            bg_color = COLORS['bg_chat_character']

        # Контейнер сообщения
        msg_container = tk.Frame(self.messages_container, bg=COLORS['bg_primary'])
        msg_container.pack(fill=tk.X, pady=5, padx=20)

        # Фрейм сообщения
        msg_frame = tk.Frame(msg_container, bg=bg_color)

        if anchor == 'e':
            msg_frame.pack(side=tk.RIGHT)
        else:
            # Для группового чата добавляем имя отправителя
            if self.current_chat_id in self.groups and sender != 'user':
                char_name = self.characters.get(sender, {}).get('name', sender)
                name_label = tk.Label(
                    msg_container,
                    text=char_name,
                    bg=COLORS['bg_primary'],
                    fg=COLORS['text_secondary'],
                    font=('Arial', 9, 'bold')
                )
                name_label.pack(anchor='w')

            msg_frame.pack(side=tk.LEFT)

        # Содержимое сообщения
        if msg_type == 'text':
            text_label = tk.Label(
                msg_frame,
                text=message['text'],
                bg=bg_color,
                fg=COLORS['text_primary'],
                font=('Arial', 11),
                wraplength=400,
                justify=tk.LEFT,
                padx=12,
                pady=8
            )
            text_label.pack()

        elif msg_type == 'photo':
            # Отображаем фото
            photo_path = message.get('photo_path', '')
            if os.path.exists(photo_path):
                try:
                    img = Image.open(photo_path)
                    img.thumbnail((300, 300))
                    photo = ImageTk.PhotoImage(img)
                    photo_label = tk.Label(msg_frame, image=photo, bg=bg_color)
                    photo_label.image = photo
                    photo_label.pack(padx=5, pady=5)
                except Exception as e:
                    error_label = tk.Label(
                        msg_frame,
                        text=f"[Ошибка загрузки фото: {e}]",
                        bg=bg_color,
                        fg=COLORS['text_secondary'],
                        font=('Arial', 9, 'italic'),
                        padx=12,
                        pady=8
                    )
                    error_label.pack()
            else:
                error_label = tk.Label(
                    msg_frame,
                    text="[Фото не найдено]",
                    bg=bg_color,
                    fg=COLORS['text_secondary'],
                    font=('Arial', 9, 'italic'),
                    padx=12,
                    pady=8
                )
                error_label.pack()

        # Временная метка
        time_label = tk.Label(
            msg_container,
            text=timestamp,
            bg=COLORS['bg_primary'],
            fg=COLORS['text_secondary'],
            font=('Arial', 8)
        )

        if anchor == 'e':
            time_label.pack(side=tk.RIGHT, padx=(0, 5))
        else:
            time_label.pack(side=tk.LEFT, padx=(5, 0))

    # ---------- ОТПРАВКА СООБЩЕНИЙ ----------

    def send_message(self):
        """Отправляет сообщение пользователя и получает ответ от персонажа."""
        if not self.current_chat_id:
            messagebox.showwarning("Предупреждение", "Выберите чат")
            return

        # Получаем текст
        text = self.message_text.get("1.0", tk.END).strip()
        if not text:
            return

        # Очищаем поле ввода
        self.message_text.delete("1.0", tk.END)

        # Создаем сообщение пользователя
        user_message = {
            'id': f"msg_{int(time.time() * 1000)}",
            'sender': 'user',
            'text': text,
            'timestamp': datetime.now().isoformat(),
            'type': 'text'
        }

        # Добавляем в историю
        if self.current_chat_id not in self.chats:
            self.chats[self.current_chat_id] = []

        self.chats[self.current_chat_id].append(user_message)

        # Отображаем сообщение
        self.add_message_to_display(user_message)
        self.messages_canvas.yview_moveto(1.0)

        # Сохраняем историю
        self.save_chat_history(self.current_chat_id)

        # Получаем ответ от персонажа(ей) в отдельном потоке
        Thread(target=self.get_character_response, args=(text,), daemon=True).start()

    def get_character_response(self, user_text):
        """
        Получает ответ от персонажа через API (в отдельном потоке).

        Args:
            user_text: Текст сообщения пользователя
        """
        # Показываем индикатор печатает
        self.show_typing_indicator()

        if self.current_chat_id in self.groups:
            # Групповой чат - опрашиваем каждого участника
            self.handle_group_response(user_text)
        else:
            # Личный чат
            self.handle_private_response(user_text)

        # Скрываем индикатор
        self.hide_typing_indicator()

    def handle_private_response(self, user_text):
        """
        Обрабатывает ответ персонажа в личном чате.

        Args:
            user_text: Текст сообщения пользователя
        """
        character_id = self.current_chat_id
        character = self.characters.get(character_id)

        if not character:
            return

        # Формируем промпт
        prompt = self.build_prompt(character, 'private')

        # Отправляем запрос к API
        try:
            response_text = self.api.send_message(prompt, character)

            # Обрабатываем ответ
            self.process_character_response(response_text, character, character_id)

        except Exception as e:
            print(f"Ошибка при получении ответа: {e}")
            # Добавляем сообщение об ошибке
            error_msg = {
                'id': f"msg_{int(time.time() * 1000)}",
                'sender': character_id,
                'text': f"[Ошибка API: {str(e)}]",
                'timestamp': datetime.now().isoformat(),
                'type': 'text'
            }
            self.chats[self.current_chat_id].append(error_msg)
            self.root.after(0, lambda: self.add_message_to_display(error_msg))

    def handle_group_response(self, user_text):
        """
        Обрабатывает ответы персонажей в групповом чате.

        Args:
            user_text: Текст сообщения пользователя
        """
        group_id = self.current_chat_id
        group = self.groups.get(group_id)

        if not group:
            return

        members = group.get('members', [])

        # Опрашиваем каждого участника
        for member_id in members:
            character = self.characters.get(member_id)
            if not character:
                continue

            # Формируем промпт для группового чата
            prompt = self.build_prompt(character, 'group', group)

            # Отправляем запрос
            try:
                response_text = self.api.send_message(prompt, character)

                # Проверяем на [IGNORE]
                if '[IGNORE]' in response_text:
                    continue

                # Задержка для реализма
                time.sleep(1)

                # Обрабатываем ответ
                self.process_character_response(response_text, character, member_id)

            except Exception as e:
                print(f"Ошибка при получении ответа от {member_id}: {e}")

    def process_character_response(self, response_text, character, sender_id):
        """
        Обрабатывает текст ответа персонажа (проверка на [PHOTO:] и т.д.).

        Args:
            response_text: Текст ответа от API
            character: Данные персонажа
            sender_id: ID отправителя
        """
        # Проверяем на команду отправки фото
        if '[PHOTO:' in response_text:
            # Извлекаем имя файла
            import re
            match = re.search(r'\[PHOTO:(\w+)\]', response_text)
            if match:
                photo_filename = match.group(1)
                # Отправляем фото
                self.send_character_photo(character, photo_filename, sender_id)
                return

        # Обычное текстовое сообщение
        char_message = {
            'id': f"msg_{int(time.time() * 1000)}",
            'sender': sender_id,
            'text': response_text,
            'timestamp': datetime.now().isoformat(),
            'type': 'text'
        }

        self.chats[self.current_chat_id].append(char_message)

        # Отображаем в GUI (из главного потока)
        self.root.after(0, lambda: self.add_message_to_display(char_message))
        self.root.after(0, lambda: self.messages_canvas.yview_moveto(1.0))

        # Сохраняем историю
        self.save_chat_history(self.current_chat_id)

    def send_character_photo(self, character, photo_filename, sender_id):
        """
        Отправляет фото от персонажа.

        Args:
            character: Данные персонажа
            photo_filename: Имя файла фото (без расширения)
            sender_id: ID отправителя
        """
        # Ищем фото в списке доступных
        photos = character.get('photos', [])
        photo_path = None

        for photo in photos:
            if photo_filename in photo['filename']:
                photo_path = os.path.join(
                    CHARACTERS_DIR,
                    character['id'],
                    'photos',
                    photo['filename']
                )
                break

        if not photo_path or not os.path.exists(photo_path):
            print(f"Фото {photo_filename} не найдено")
            return

        # Создаем сообщение с фото
        photo_message = {
            'id': f"msg_{int(time.time() * 1000)}",
            'sender': sender_id,
            'timestamp': datetime.now().isoformat(),
            'type': 'photo',
            'photo_path': photo_path
        }

        self.chats[self.current_chat_id].append(photo_message)

        # Отображаем
        self.root.after(0, lambda: self.add_message_to_display(photo_message))
        self.root.after(0, lambda: self.messages_canvas.yview_moveto(1.0))

        # Сохраняем
        self.save_chat_history(self.current_chat_id)

    # Продолжение в следующей части...

    # ---------- ФОРМИРОВАНИЕ ПРОМПТОВ ----------

    def build_prompt(self, character, chat_type='private', group_context=None):
        """
        Формирует промпт для отправки в API.

        Args:
            character: Данные персонажа
            chat_type: Тип чата ('private' или 'group')
            group_context: Контекст группы (если групповой чат)

        Returns:
            Строка с промптом
        """
        # Получаем базовый промпт
        if chat_type == 'private':
            system_prompt = character.get('private_prompt', '')
        else:
            system_prompt = character.get('group_prompt', '')

            # Подставляем данные группы
            if group_context:
                group_name = group_context.get('name', '')
                members = ', '.join([
                    self.characters.get(m, {}).get('name', m) 
                    for m in group_context.get('members', [])
                ])
                system_prompt = system_prompt.format(
                    group_name=group_name,
                    members=members
                )

        # Получаем историю последних N сообщений
        messages = self.chats.get(self.current_chat_id, [])
        recent_messages = messages[-MAX_MESSAGES_FOR_API:]

        # Форматируем историю
        history_text = ""
        for msg in recent_messages:
            if msg['type'] == 'text':
                sender_name = "Пользователь" if msg['sender'] == 'user' else self.characters.get(msg['sender'], {}).get('name', msg['sender'])
                history_text += f"{sender_name}: {msg['text']}\n"
            elif msg['type'] == 'photo':
                sender_name = "Пользователь" if msg['sender'] == 'user' else self.characters.get(msg['sender'], {}).get('name', msg['sender'])
                history_text += f"{sender_name}: [отправил(а) фото]\n"

        # Собираем финальный промпт
        final_prompt = f"""{system_prompt}

История переписки:
{history_text}

Ответь на последнее сообщение пользователя естественно и по характеру персонажа."""

        return final_prompt

    # ---------- ИНДИКАЦИЯ "ПЕЧАТАЕТ" ----------

    def show_typing_indicator(self):
        """Показывает индикатор 'печатает...'."""
        # В реальной реализации можно добавить анимацию в списке чатов
        # Здесь просто помечаем в словаре
        self.typing_indicators[self.current_chat_id] = True
        print(f"[{self.current_chat_id}] печатает...")

    def hide_typing_indicator(self):
        """Скрывает индикатор 'печатает...'."""
        self.typing_indicators[self.current_chat_id] = False
        print(f"[{self.current_chat_id}] закончил печатать")

    # ---------- СОЗДАНИЕ ГРУППЫ ----------

    def create_group_dialog(self):
        """Открывает диалог создания новой группы."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Создать группу")
        dialog.geometry("400x500")
        dialog.configure(bg=COLORS['bg_primary'])
        dialog.transient(self.root)
        dialog.grab_set()

        # Заголовок
        title_label = tk.Label(
            dialog,
            text="Создание группы",
            bg=COLORS['bg_primary'],
            fg=COLORS['text_primary'],
            font=('Arial', 16, 'bold'),
            pady=15
        )
        title_label.pack()

        # Название группы
        name_frame = tk.Frame(dialog, bg=COLORS['bg_primary'])
        name_frame.pack(fill=tk.X, padx=20, pady=10)

        name_label = tk.Label(
            name_frame,
            text="Название группы:",
            bg=COLORS['bg_primary'],
            fg=COLORS['text_primary'],
            font=('Arial', 11)
        )
        name_label.pack(anchor='w')

        name_entry = tk.Entry(
            name_frame,
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['text_primary'],
            relief=tk.FLAT,
            font=('Arial', 11)
        )
        name_entry.pack(fill=tk.X, ipady=5)

        # Выбор участников
        members_label = tk.Label(
            dialog,
            text="Выберите участников:",
            bg=COLORS['bg_primary'],
            fg=COLORS['text_primary'],
            font=('Arial', 11),
            pady=10
        )
        members_label.pack(anchor='w', padx=20)

        # Список чекбоксов
        members_frame = tk.Frame(dialog, bg=COLORS['bg_primary'])
        members_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        # Canvas для скролла
        canvas = tk.Canvas(members_frame, bg=COLORS['bg_primary'], highlightthickness=0)
        scrollbar = ttk.Scrollbar(members_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=COLORS['bg_primary'])

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Создаем чекбоксы для каждого персонажа
        checkboxes = {}
        for char_id, char_data in self.characters.items():
            var = tk.BooleanVar()
            cb = tk.Checkbutton(
                scrollable_frame,
                text=char_data['name'],
                variable=var,
                bg=COLORS['bg_primary'],
                fg=COLORS['text_primary'],
                selectcolor=COLORS['bg_secondary'],
                activebackground=COLORS['bg_primary'],
                activeforeground=COLORS['text_primary'],
                font=('Arial', 11),
                cursor='hand2'
            )
            cb.pack(anchor='w', pady=5)
            checkboxes[char_id] = var

        # Кнопки
        buttons_frame = tk.Frame(dialog, bg=COLORS['bg_primary'])
        buttons_frame.pack(fill=tk.X, padx=20, pady=20)

        def create_group():
            group_name = name_entry.get().strip()
            if not group_name:
                messagebox.showwarning("Ошибка", "Введите название группы")
                return

            # Получаем выбранных участников
            selected_members = [char_id for char_id, var in checkboxes.items() if var.get()]

            if len(selected_members) < 2:
                messagebox.showwarning("Ошибка", "Выберите минимум 2 участников")
                return

            # Создаем ID группы
            group_id = f"group_{int(time.time())}"

            # Создаем данные группы
            group_data = {
                'id': group_id,
                'name': group_name,
                'members': selected_members,
                'group_context': f"Это групповой чат '{group_name}'. Здесь общаются коллеги.",
                'api_settings': {
                    'temperature': 0.7,
                    'max_tokens': 250
                }
            }

            # Сохраняем в файл
            group_path = os.path.join(GROUPS_DIR, f"{group_id}.yml")
            with open(group_path, 'w', encoding='utf-8') as f:
                yaml.dump(group_data, f, allow_unicode=True, default_flow_style=False)

            # Добавляем в словарь групп
            self.groups[group_id] = group_data

            # Создаем пустую историю чата
            self.chats[group_id] = []

            # Обновляем список чатов
            self.populate_chats_list()

            # Закрываем диалог
            dialog.destroy()

            # Открываем новую группу
            self.open_chat(group_id)

            messagebox.showinfo("Успех", f"Группа '{group_name}' создана!")

        create_btn = tk.Button(
            buttons_frame,
            text="Создать",
            bg=COLORS['accent'],
            fg=COLORS['text_primary'],
            relief=tk.FLAT,
            font=('Arial', 11, 'bold'),
            cursor='hand2',
            command=create_group
        )
        create_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        cancel_btn = tk.Button(
            buttons_frame,
            text="Отмена",
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            relief=tk.FLAT,
            font=('Arial', 11),
            cursor='hand2',
            command=dialog.destroy
        )
        cancel_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))


# ==================== ГЛАВНАЯ ФУНКЦИЯ ====================

def main():
    """Главная функция запуска приложения."""
    root = tk.Tk()
    app = MessengerApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
