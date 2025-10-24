# ui/chat_area.py
# -*- coding: utf-8 -*-
"""
Область отображения сообщений чата
"""
import tkinter as tk
from tkinter import ttk
from threading import Thread
from PIL import Image, ImageTk
import os
from config.settings import COLORS, AVATAR_SIZE
from ui.components import generate_placeholder_avatar, format_timestamp

class ChatArea(tk.Frame):
    """Область отображения чата."""
    
    def __init__(self, parent, chat_manager, api_manager):
        super().__init__(parent, bg=COLORS['bg_primary'])
        self.chat_manager = chat_manager
        self.api_manager = api_manager
        self.current_chat_id = None
        
        self.create_widgets()
    
    def create_widgets(self):
        """Создает виджеты области чата."""
        # Заголовок
        self.chat_header = tk.Frame(self, bg=COLORS['bg_secondary'], height=70)
        self.chat_header.pack(fill=tk.X)
        self.chat_header.pack_propagate(False)
        
        header_content = tk.Frame(self.chat_header, bg=COLORS['bg_secondary'])
        header_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        self.header_avatar_label = tk.Label(header_content, bg=COLORS['bg_secondary'])
        self.header_avatar_label.pack(side=tk.LEFT, padx=(0, 15))
        
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
        messages_frame = tk.Frame(self, bg=COLORS['bg_primary'])
        messages_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.messages_canvas = tk.Canvas(messages_frame, bg=COLORS['bg_primary'], highlightthickness=0)
        messages_scrollbar = ttk.Scrollbar(messages_frame, orient="vertical", command=self.messages_canvas.yview)
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
        input_frame = tk.Frame(self, bg=COLORS['bg_secondary'])
        input_frame.pack(fill=tk.X, padx=10, pady=10)
        
        buttons_frame = tk.Frame(input_frame, bg=COLORS['bg_secondary'])
        buttons_frame.pack(side=tk.LEFT, padx=(10, 5))
        
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
        self.message_text.bind('<Return>', self.on_enter_press)
        self.message_text.bind('<Shift-Return>', lambda e: None)
        
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
        """Обработка Enter."""
        if not event.state & 0x1:
            self.send_message()
            return 'break'
    
    def open_chat(self, chat_id):
        """Открывает чат."""
        self.current_chat_id = chat_id
        
        # Обновляем заголовок
        if chat_id in self.chat_manager.characters:
            name = self.chat_manager.characters[chat_id].name
        elif chat_id in self.chat_manager.groups:
            name = self.chat_manager.groups[chat_id].name
        else:
            name = chat_id
        
        avatar = generate_placeholder_avatar(name, AVATAR_SIZE)
        self.header_avatar_label.config(image=avatar)
        self.header_avatar_label.image = avatar
        self.header_name_label.config(text=name)
        
        # Отображаем сообщения
        self.display_messages()
    
    def display_messages(self):
        """Отображает сообщения чата."""
        for widget in self.messages_container.winfo_children():
            widget.destroy()
        
        messages = self.chat_manager.get_chat_messages(self.current_chat_id)
        for msg in messages:
            self.add_message_to_display(msg)
        
        self.messages_canvas.update_idletasks()
        self.messages_canvas.yview_moveto(1.0)
    
    def add_message_to_display(self, message):
        """Добавляет сообщение в отображение."""
        sender = message.sender
        is_user = sender == 'user'
        
        # Контейнер сообщения
        msg_container = tk.Frame(self.messages_container, bg=COLORS['bg_primary'])
        msg_container.pack(fill=tk.X, pady=5, padx=20)
        
        # ВАЖНО: для групповых чатов не показываем имя собеседника справа
        if not is_user and self.current_chat_id in self.chat_manager.groups:
            char_name = self.chat_manager.characters.get(sender).name if sender in self.chat_manager.characters else sender
            name_label = tk.Label(
                msg_container,
                text=char_name,
                bg=COLORS['bg_primary'],
                fg=COLORS['text_secondary'],
                font=('Arial', 9, 'bold')
            )
            name_label.pack(anchor='w')
        
        # Фрейм сообщения
        bg_color = COLORS['bg_chat_user'] if is_user else COLORS['bg_chat_character']
        msg_frame = tk.Frame(msg_container, bg=bg_color)
        
        if is_user:
            msg_frame.pack(side=tk.RIGHT)
        else:
            msg_frame.pack(side=tk.LEFT)
        
        # Содержимое
        if message.msg_type == 'text':
            text_label = tk.Label(
                msg_frame,
                text=message.text,
                bg=bg_color,
                fg=COLORS['text_primary'],
                font=('Arial', 11),
                wraplength=400,
                justify=tk.LEFT,
                padx=12,
                pady=8
            )
            text_label.pack()
        elif message.msg_type == 'photo' and message.photo_path:
            if os.path.exists(message.photo_path):
                try:
                    img = Image.open(message.photo_path)
                    img.thumbnail((300, 300))
                    photo = ImageTk.PhotoImage(img)
                    photo_label = tk.Label(msg_frame, image=photo, bg=bg_color)
                    photo_label.image = photo
                    photo_label.pack(padx=5, pady=5)
                except:
                    pass
        
        # Временная метка
        timestamp = format_timestamp(message.timestamp)
        time_label = tk.Label(
            msg_container,
            text=timestamp,
            bg=COLORS['bg_primary'],
            fg=COLORS['text_secondary'],
            font=('Arial', 8)
        )
        if is_user:
            time_label.pack(side=tk.RIGHT, padx=(0, 5))
        else:
            time_label.pack(side=tk.LEFT, padx=(5, 0))
    
    def send_message(self):
        """Отправляет сообщение."""
        if not self.current_chat_id:
            return
        
        text = self.message_text.get("1.0", tk.END).strip()
        if not text:
            return
        
        self.message_text.delete("1.0", tk.END)
        
        # Добавляем сообщение пользователя
        msg = self.chat_manager.add_message(self.current_chat_id, 'user', text)
        self.add_message_to_display(msg)
        self.messages_canvas.yview_moveto(1.0)
        
        # Получаем ответ в потоке
        Thread(target=self.get_character_response, args=(text,), daemon=True).start()
    
    def get_character_response(self, user_text):
        """Получает ответ от персонажа."""
        is_group = self.current_chat_id in self.chat_manager.groups
        
        if is_group:
            group = self.chat_manager.groups[self.current_chat_id]
            for member_id in group.members:
                if member_id not in self.chat_manager.characters:
                    continue
                character = self.chat_manager.characters[member_id]
                prompt = self.chat_manager.build_prompt(self.current_chat_id, character, True)
                
                try:
                    response = self.api_manager.send_message(prompt)
                    if '[IGNORE]' in response:
                        continue
                    
                    msg = self.chat_manager.add_message(self.current_chat_id, member_id, response)
                    self.after(0, lambda m=msg: self.add_message_to_display(m))
                    self.after(0, lambda: self.messages_canvas.yview_moveto(1.0))
                except Exception as e:
                    print(f"Ошибка: {e}")
        else:
            character = self.chat_manager.characters.get(self.current_chat_id)
            if character:
                prompt = self.chat_manager.build_prompt(self.current_chat_id, character, False)
                try:
                    response = self.api_manager.send_message(prompt)
                    msg = self.chat_manager.add_message(self.current_chat_id, self.current_chat_id, response)
                    self.after(0, lambda: self.add_message_to_display(msg))
                    self.after(0, lambda: self.messages_canvas.yview_moveto(1.0))
                except Exception as e:
                    print(f"Ошибка: {e}")
