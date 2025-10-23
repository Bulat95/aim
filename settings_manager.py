# settings_manager.py

import yaml
import os

PROVIDERS_PATH = "providers/providers.yml"

class SettingsManager:
    """Работает с провайдерами и настройками."""

    def __init__(self, config_path=PROVIDERS_PATH):
        self.config_path = config_path
        self.load_config()

    def load_config(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                self.providers = yaml.safe_load(f)
        else:
            self.providers = {}

    def get_providers(self):
        return list(self.providers.keys())

    def get_models_for_provider(self, provider):
        if provider in self.providers:
            return self.providers[provider].get("models", [])
        return []

    def get_api_key(self, provider):
        if provider in self.providers:
            return self.providers[provider].get("key", "")
        return ""

    def save_settings(self, provider, model, key):
        if provider not in self.providers:
            self.providers[provider] = {}
        self.providers[provider]["key"] = key
        # Можно хранить выбранную модель, если это нужно во всей системе
        self.providers[provider]["selected_model"] = model
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(self.providers, f, allow_unicode=True)
        # После сохранения обновить внутреннее состояние
        self.load_config()
