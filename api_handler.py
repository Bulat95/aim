# api_handler.py
# -*- coding: utf-8 -*-
"""
Модуль для работы с API нейросетей.
Адаптация функций из proxy5.py для использования в мессенджере.
"""

import yaml
import os
import requests
from typing import Dict, Any, Optional


class MessengerAPI:
    """Класс для работы с различными API провайдерами."""

    def __init__(self, providers_config_path="providers/providers.yml"):
        """
        Инициализация API handler.

        Args:
            providers_config_path: Путь к файлу конфигурации провайдеров
        """
        self.config_path = providers_config_path
        self.config = {}
        self.load_config()

    def load_config(self):
        """Загружает конфигурацию провайдеров из YAML файла."""
        if not os.path.exists(self.config_path):
            print(f"ПРЕДУПРЕЖДЕНИЕ: Файл конфигурации '{self.config_path}' не найден!")
            print("API запросы не будут работать без конфигурации.")
            return

        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)

        print(f"Загружена конфигурация API из {self.config_path}")

    def send_message(self, prompt: str, character_config: Dict[str, Any]) -> str:
        """
        Отправляет запрос к API используя настройки персонажа.

        Args:
            prompt: Текст промпта
            character_config: Конфигурация персонажа с api_settings

        Returns:
            Ответ от нейросети
        """
        # Получаем настройки API из конфига персонажа
        api_settings = character_config.get('api_settings', {})
        provider = api_settings.get('provider', 'claude')
        model = api_settings.get('model', '')
        temperature = api_settings.get('temperature', 0.7)
        max_tokens = api_settings.get('max_tokens', 300)

        # Проверяем, что провайдер есть в конфиге
        if provider not in self.config:
            return f"Ошибка: Провайдер '{provider}' не найден в конфигурации."

        # Получаем данные провайдера
        provider_data = self.config[provider]
        api_url = provider_data.get('api', '')
        api_key = provider_data.get('key', '')

        # Вызываем соответствующую функцию отправки
        try:
            if provider == 'claude':
                return self.send_claude(prompt, model, api_key, temperature, max_tokens)
            elif provider == 'gemini':
                return self.send_gemini(prompt, model, api_key, temperature, max_tokens)
            elif provider == 'openrouter':
                return self.send_openrouter(prompt, model, api_url, api_key, temperature, max_tokens)
            elif provider == 'chutes':
                return self.send_chutes(prompt, model, api_url, api_key, temperature, max_tokens)
            elif provider == 'deepseek':
                return self.send_deepseek(prompt, model, api_url, api_key, temperature, max_tokens)
            else:
                return f"Ошибка: Провайдер '{provider}' не поддерживается."

        except Exception as e:
            return f"Ошибка API: {str(e)}"

    # ---------- ФУНКЦИИ ОТПРАВКИ ДЛЯ КАЖДОГО ПРОВАЙДЕРА ----------

    def send_claude(self, prompt: str, model: str, api_key: str, temperature: float, max_tokens: int) -> str:
        """
        Отправка запроса к Claude API.

        Args:
            prompt: Текст промпта
            model: Название модели
            api_key: API ключ
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов

        Returns:
            Ответ от Claude
        """
        try:
            import anthropic
        except ImportError:
            return "Ошибка: Библиотека 'anthropic' не установлена. Выполните: pip install anthropic"

        if not api_key:
            return "Ошибка: API-ключ для Claude не указан."

        try:
            client = anthropic.Anthropic(api_key=api_key, max_retries=0)

            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )

            if hasattr(response, "content") and response.content:
                return self.clean_text(response.content[0].text)
            else:
                return "Ошибка: Claude вернул пустой ответ."

        except Exception as e:
            return f"Ошибка API Claude: {str(e)}"

    def send_gemini(self, prompt: str, model: str, api_key: str, temperature: float, max_tokens: int) -> str:
        """
        Отправка запроса к Gemini API.

        Args:
            prompt: Текст промпта
            model: Название модели
            api_key: API ключ
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов

        Returns:
            Ответ от Gemini
        """
        try:
            import google.generativeai as genai
        except ImportError:
            return "Ошибка: Библиотека 'google-generativeai' не установлена. Выполните: pip install google-generativeai"

        if not api_key:
            return "Ошибка: API-ключ для Gemini не указан."

        try:
            genai.configure(api_key=api_key)
            model_obj = genai.GenerativeModel(model)

            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }

            response = model_obj.generate_content(
                prompt,
                generation_config=generation_config
            )

            if hasattr(response, "text"):
                return self.clean_text(response.text)
            else:
                return "Ошибка: Gemini вернул неожиданный формат ответа."

        except Exception as e:
            return f"Ошибка API Gemini: {str(e)}"

    def send_openrouter(self, prompt: str, model: str, api_url: str, api_key: str, 
                       temperature: float, max_tokens: int) -> str:
        """
        Отправка запроса к OpenRouter API.

        Args:
            prompt: Текст промпта
            model: Название модели
            api_url: URL API
            api_key: API ключ
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов

        Returns:
            Ответ от OpenRouter
        """
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "http://localhost:5000",
            "X-Title": "AI Messenger",
        }

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }

        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            api_response = response.json()
            return self.clean_text(api_response["choices"][0]["message"]["content"])

        except requests.RequestException as e:
            return f"Ошибка API OpenRouter: {str(e)}"
        except KeyError:
            return f"Ошибка: неверный формат ответа от OpenRouter."

    def send_chutes(self, prompt: str, model: str, api_url: str, api_key: str,
                   temperature: float, max_tokens: int) -> str:
        """
        Отправка запроса к Chutes API.

        Args:
            prompt: Текст промпта
            model: Название модели
            api_url: URL API
            api_key: API ключ
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов

        Returns:
            Ответ от Chutes
        """
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        try:
            response = requests.post(
                api_url,
                headers=headers,
                json=body,
                timeout=30
            )
            response.raise_for_status()
            return self.clean_text(response.json()["choices"][0]["message"]["content"])

        except Exception as e:
            return f"Ошибка API Chutes: {str(e)}"

    def send_deepseek(self, prompt: str, model: str, api_url: str, api_key: str,
                     temperature: float, max_tokens: int) -> str:
        """
        Отправка запроса к DeepSeek API.

        Args:
            prompt: Текст промпта
            model: Название модели
            api_url: URL API
            api_key: API ключ
            temperature: Температура генерации
            max_tokens: Максимальное количество токенов

        Returns:
            Ответ от DeepSeek
        """
        try:
            from openai import OpenAI
        except ImportError:
            return "Ошибка: Библиотека 'openai' не установлена. Выполните: pip install openai"

        try:
            client = OpenAI(
                api_key=api_key,
                base_url=api_url
            )

            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False
            )

            return self.clean_text(response.choices[0].message.content)

        except Exception as e:
            return f"Ошибка API DeepSeek: {str(e)}"

    # ---------- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----------

    def clean_text(self, text: str) -> str:
        """
        Очищает текст от технических артефактов.

        Args:
            text: Исходный текст

        Returns:
            Очищенный текст
        """
        if not text:
            return "Ответ модели оказался пустым."

        # Убираем служебные хвосты
        cut_tags = ["СТОП", "INST", "Human:", "Assistant:", "###"]
        for tag in cut_tags:
            if tag in text:
                text = text.split(tag)[0]

        # Убираем лишние пробелы
        text = text.strip()

        return text if text else "Ответ модели оказался пустым после очистки."
