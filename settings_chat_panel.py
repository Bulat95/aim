# settings_chat_panel.py

import tkinter as tk
from tkinter import ttk, messagebox
from settings_manager import SettingsManager

class SettingsChatPanel(tk.Frame):
    """Панель для редактирования настроек провайдеров."""

    def __init__(self, master, settings_manager: SettingsManager, current_provider=""):
        super().__init__(master, bg="#232323")
        self.settings_manager = settings_manager

        # Получить всех провайдеров
        providers = self.settings_manager.get_providers()
        provider = current_provider if current_provider in providers else (providers[0] if providers else "")
        self.provider_var = tk.StringVar(value=provider)
        self.model_var = tk.StringVar()
        self.api_key_var = tk.StringVar()

        # При выборе провайдера обновить модели и ключ
        def on_provider_selected(*_):
            models = self.settings_manager.get_models_for_provider(self.provider_var.get())
            self.model_combo["values"] = models
            if models:
                self.model_var.set(models[0])
            self.api_key_var.set(self.settings_manager.get_api_key(self.provider_var.get()))

        # Секция GUI
        tk.Label(self, text="Провайдер:", fg="#fff", bg="#232323").pack(anchor="w", pady=(10,0))
        self.provider_combo = ttk.Combobox(self, values=providers, state="readonly", textvariable=self.provider_var)
        self.provider_combo.pack(anchor="w", pady=(0, 8))
        self.provider_combo.bind("<<ComboboxSelected>>", on_provider_selected)

        tk.Label(self, text="Модель:", fg="#fff", bg="#232323").pack(anchor="w")
        self.model_combo = ttk.Combobox(self, values=[], state="readonly", textvariable=self.model_var)
        self.model_combo.pack(anchor="w", pady=(0, 8))

        tk.Label(self, text="API-ключ:", fg="#fff", bg="#232323").pack(anchor="w")
        tk.Entry(self, textvariable=self.api_key_var, width=64).pack(anchor="w", pady=(0, 10))

        def save_settings():
            provider = self.provider_var.get()
            model = self.model_var.get()
            key = self.api_key_var.get()
            self.settings_manager.save_settings(provider, model, key)
            messagebox.showinfo("Настройки", "Параметры успешно сохранены!")

        tk.Button(self, text="Сохранить", command=save_settings, bg="#3a86ff", fg="#fff").pack(anchor="w", pady=(5,15))

        # Инициализировать значения при запуске
        on_provider_selected()
