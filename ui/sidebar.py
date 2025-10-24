# ui/sidebar.py
# -*- coding: utf-8 -*-
"""
Боковая панель со списком чатов
"""
import tkinter as tk
from tkinter import ttk
from config.settings import COLORS, SIDEBAR_WIDTH, AVATAR_SIZE_SMALL
from ui.components import generate_placeholder_avatar

class Sidebar(tk.Frame):
    """Боковая панель с чатами."""
    
    def __init__(self, parent, chat_manager, on_chat_select):
        super().__init__(parent, bg=COLORS['bg_secondary'], width=SIDEBAR_WIDTH)
        self.chat_manager = chat_manager
        self.on_chat_select = on_chat_select
        self.pack_propagate(False)
        
        self.create_widgets()
        self.populate_chats()
    
    def create_widgets(self):
        """Создает виджеты sidebar."""
        # Заголовок
        header = tk.Label(
            self,
            text="Чаты",
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            font=('Arial', 16, 'bold'),
            pady=15
        )
        header.pack(fill=tk.X)
        
        # Поиск (заглушка)
        search_frame = tk.Frame(self, bg=COLORS['bg_secondary'])
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
        
        # Контейнер для списка чатов
        chats_frame = tk.Frame(self, bg=COLORS['bg_secondary'])
        chats_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
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
        
        # Кнопка создания группы
        create_group_btn = tk.Button(
            self,
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
    
    def populate_chats(self):
        """Заполняет список чатов."""
        for widget in self.chats_container.winfo_children():
            widget.destroy()
        
        # Добавляем настройки
        self.create_chat_item("settings", "⚙️ Настройки", "system")
        
        # Личные чаты
        for char_id, char in self.chat_manager.characters.items():
            self.create_chat_item(char_id, char.name, 'private')
        
        # Групповые чаты
        for group_id, group in self.chat_manager.groups.items():
            self.create_chat_item(group_id, group.name, 'group')
    
    def create_chat_item(self, chat_id, name, chat_type):
        """Создает элемент чата в списке."""
        item_frame = tk.Frame(self.chats_container, bg=COLORS['bg_secondary'], cursor='hand2')
        item_frame.pack(fill=tk.X, pady=2)
        item_frame.bind('<Button-1>', lambda e: self.on_chat_select(chat_id))
        
        content_frame = tk.Frame(item_frame, bg=COLORS['bg_secondary'])
        content_frame.pack(fill=tk.X, padx=10, pady=8)
        
        # Аватарка
        if chat_type != 'system':
            avatar = generate_placeholder_avatar(name, AVATAR_SIZE_SMALL)
            avatar_label = tk.Label(content_frame, image=avatar, bg=COLORS['bg_secondary'])
            avatar_label.image = avatar
            avatar_label.pack(side=tk.LEFT, padx=(0, 10))
        
        # Текст
        text_frame = tk.Frame(content_frame, bg=COLORS['bg_secondary'])
        text_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        name_label = tk.Label(
            text_frame,
            text=name,
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_primary'],
            font=('Arial', 11, 'bold'),
            anchor='w'
        )
        name_label.pack(fill=tk.X)
        
        # Hover эффект
        def on_enter(e):
            item_frame.config(bg=COLORS['hover'])
            content_frame.config(bg=COLORS['hover'])
            text_frame.config(bg=COLORS['hover'])
            name_label.config(bg=COLORS['hover'])
            if chat_type != 'system':
                avatar_label.config(bg=COLORS['hover'])
        
        def on_leave(e):
            item_frame.config(bg=COLORS['bg_secondary'])
            content_frame.config(bg=COLORS['bg_secondary'])
            text_frame.config(bg=COLORS['bg_secondary'])
            name_label.config(bg=COLORS['bg_secondary'])
            if chat_type != 'system':
                avatar_label.config(bg=COLORS['bg_secondary'])
        
        item_frame.bind('<Enter>', on_enter)
        item_frame.bind('<Leave>', on_leave)
    
    def create_group_dialog(self):
        """Открывает диалог создания группы."""
        from tkinter import messagebox, simpledialog
        
        dialog = tk.Toplevel(self)
        dialog.title("Создать группу")
        dialog.geometry("400x500")
        dialog.configure(bg=COLORS['bg_primary'])
        dialog.transient(self)
        dialog.grab_set()
        
        title_label = tk.Label(
            dialog,
            text="Создание группы",
            bg=COLORS['bg_primary'],
            fg=COLORS['text_primary'],
            font=('Arial', 16, 'bold'),
            pady=15
        )
        title_label.pack()
        
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
        
        members_label = tk.Label(
            dialog,
            text="Выберите участников:",
            bg=COLORS['bg_primary'],
            fg=COLORS['text_primary'],
            font=('Arial', 11),
            pady=10
        )
        members_label.pack(anchor='w', padx=20)
        
        members_frame = tk.Frame(dialog, bg=COLORS['bg_primary'])
        members_frame.pack(fill=tk.BOTH, expand=True, padx=20)
        
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
        
        checkboxes = {}
        for char_id, char in self.chat_manager.characters.items():
            var = tk.BooleanVar()
            cb = tk.Checkbutton(
                scrollable_frame,
                text=char.name,
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
        
        buttons_frame = tk.Frame(dialog, bg=COLORS['bg_primary'])
        buttons_frame.pack(fill=tk.X, padx=20, pady=20)
        
        def create_group():
            group_name = name_entry.get().strip()
            if not group_name:
                messagebox.showwarning("Ошибка", "Введите название группы")
                return
            
            selected = [char_id for char_id, var in checkboxes.items() if var.get()]
            if len(selected) < 2:
                messagebox.showwarning("Ошибка", "Выберите минимум 2 участников")
                return
            
            group_id = self.chat_manager.create_group(group_name, selected)
            dialog.destroy()
            self.populate_chats()
            self.on_chat_select(group_id)
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
