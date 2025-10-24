# ui/main_window.py
# -*- coding: utf-8 -*-
"""
Главное окно приложения
"""
import tkinter as tk
from config.settings import WINDOW_WIDTH, WINDOW_HEIGHT, MIN_WIDTH, MIN_HEIGHT, COLORS
from core.api_manager import APIManager
from core.chat_manager import ChatManager
from ui.sidebar import Sidebar
from ui.chat_area import ChatArea
from ui.settings_panel import SettingsPanel

class MainWindow:
    """Главное окно мессенджера."""
    
    def __init__(self, root):
        self.root = root
        self.root.title("AI Messenger")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        self.root.minsize(MIN_WIDTH, MIN_HEIGHT)
        self.root.configure(bg=COLORS['bg_primary'])
        
        # Инициализация менеджеров
        self.api_manager = APIManager()
        self.chat_manager = ChatManager()
        
        # Устанавливаем первого провайдера по умолчанию
        providers = self.api_manager.get_providers()
        if providers:
            models = self.api_manager.get_models(providers[0])
            if models:
                self.api_manager.set_provider_and_model(providers[0], models[0])
        
        # Создание GUI
        self.create_gui()
    
    def create_gui(self):
        """Создает основной интерфейс."""
        main_container = tk.Frame(self.root, bg=COLORS['bg_primary'])
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Левая панель (чаты)
        self.sidebar = Sidebar(main_container, self.chat_manager, self.on_chat_select)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
        
        # Правая панель (чат или настройки)
        self.right_panel = tk.Frame(main_container, bg=COLORS['bg_primary'])
        self.right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Область чата
        self.chat_area = ChatArea(self.right_panel, self.chat_manager, self.api_manager)
        
        # Панель настроек
        self.settings_panel = SettingsPanel(self.right_panel, self.api_manager)
    
    def on_chat_select(self, chat_id):
        """Обработчик выбора чата."""
        # Скрываем все панели
        self.chat_area.pack_forget()
        self.settings_panel.pack_forget()
        
        if chat_id == "settings":
            # Показываем настройки
            self.settings_panel.pack(fill=tk.BOTH, expand=True)
        else:
            # Показываем чат
            self.chat_area.pack(fill=tk.BOTH, expand=True)
            self.chat_area.open_chat(chat_id)
