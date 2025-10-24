# ui/settings_panel.py
# -*- coding: utf-8 -*-
"""
Панель настроек с выбором провайдера и модели
"""
import tkinter as tk
from tkinter import ttk, messagebox
from config.settings import COLORS

class SettingsPanel(tk.Frame):
    """Панель настроек провайдера и модели."""
    
    def __init__(self, parent, api_manager):
        super().__init__(parent, bg=COLORS['bg_primary'])
        self.api_manager = api_manager
        self.provider_var = tk.StringVar()
        self.model_var = tk.StringVar()
        
        self.create_widgets()
        self.load_current_settings()
    
    def create_widgets(self):
        """Создает виджеты панели настроек."""
        # Заголовок
        title = tk.Label(
            self,
            text="⚙️ Настройки",
            bg=COLORS['bg_primary'],
            fg=COLORS['text_primary'],
            font=('Arial', 18, 'bold'),
            pady=20
        )
        title.pack(anchor='w', padx=20)
        
        # Секция выбора провайдера
        provider_frame = tk.Frame(self, bg=COLORS['bg_primary'])
        provider_frame.pack(fill=tk.X, padx=20, pady=10)
        
        provider_label = tk.Label(
            provider_frame,
            text="Провайдер:",
            bg=COLORS['bg_primary'],
            fg=COLORS['text_primary'],
            font=('Arial', 12, 'bold')
        )
        provider_label.pack(anchor='w', pady=(0, 5))
        
        providers = self.api_manager.get_providers()
        self.provider_combo = ttk.Combobox(
            provider_frame,
            textvariable=self.provider_var,
            values=providers,
            state='readonly',
            font=('Arial', 11),
            width=40
        )
        self.provider_combo.pack(anchor='w', pady=(0, 10))
        self.provider_combo.bind('<<ComboboxSelected>>', self.on_provider_changed)
        
        # Секция выбора модели
        model_frame = tk.Frame(self, bg=COLORS['bg_primary'])
        model_frame.pack(fill=tk.X, padx=20, pady=10)
        
        model_label = tk.Label(
            model_frame,
            text="Модель:",
            bg=COLORS['bg_primary'],
            fg=COLORS['text_primary'],
            font=('Arial', 12, 'bold')
        )
        model_label.pack(anchor='w', pady=(0, 5))
        
        self.model_combo = ttk.Combobox(
            model_frame,
            textvariable=self.model_var,
            state='readonly',
            font=('Arial', 11),
            width=40
        )
        self.model_combo.pack(anchor='w', pady=(0, 10))
        
        # Информация
        info_text = tk.Label(
            self,
            text="Выбранные настройки будут применены ко всем чатам.\n"
                 "Настройки провайдера хранятся в config/providers.yml",
            bg=COLORS['bg_primary'],
            fg=COLORS['text_secondary'],
            font=('Arial', 9),
            justify=tk.LEFT,
            wraplength=500
        )
        info_text.pack(anchor='w', padx=20, pady=20)
        
        # Кнопка применить
        apply_btn = tk.Button(
            self,
            text="Применить настройки",
            bg=COLORS['accent'],
            fg=COLORS['text_primary'],
            font=('Arial', 12, 'bold'),
            relief=tk.FLAT,
            cursor='hand2',
            command=self.apply_settings,
            padx=20,
            pady=10
        )
        apply_btn.pack(anchor='w', padx=20, pady=10)
    
    def load_current_settings(self):
        """Загружает текущие настройки."""
        providers = self.api_manager.get_providers()
        if providers:
            current_provider = self.api_manager.current_provider or providers[0]
            self.provider_var.set(current_provider)
            self.update_models(current_provider)
            
            current_model = self.api_manager.current_model
            if current_model:
                self.model_var.set(current_model)
    
    def on_provider_changed(self, event=None):
        """Обработчик изменения провайдера."""
        provider = self.provider_var.get()
        self.update_models(provider)
    
    def update_models(self, provider):
        """Обновляет список моделей для выбранного провайдера."""
        models = self.api_manager.get_models(provider)
        self.model_combo['values'] = models
        if models:
            self.model_var.set(models[0])
    
    def apply_settings(self):
        """Применяет выбранные настройки."""
        provider = self.provider_var.get()
        model = self.model_var.get()
        
        if not provider or not model:
            messagebox.showwarning("Ошибка", "Выберите провайдера и модель")
            return
        
        self.api_manager.set_provider_and_model(provider, model)
        messagebox.showinfo("Успех", f"Настройки применены:\n{provider} / {model}")
