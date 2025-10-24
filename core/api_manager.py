# core/api_manager.py
# -*- coding: utf-8 -*-
"""
Управление API запросами к различным провайдерам
"""
import yaml
import os
import requests
from typing import Dict, Any

class APIManager:
    """Класс для работы с API провайдерами."""
    
    def __init__(self, providers_config_path="config/providers.yml"):
        self.config_path = providers_config_path
        self.config = {}
        self.current_provider = None
        self.current_model = None
        self.load_config()
    
    def load_config(self):
        """Загружает конфигурацию провайдеров."""
        if not os.path.exists(self.config_path):
            print(f"ПРЕДУПРЕЖДЕНИЕ: Файл {self.config_path} не найден!")
            return
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
    
    def get_providers(self):
        """Возвращает список доступных провайдеров."""
        return list(self.config.keys())
    
    def get_models(self, provider):
        """Возвращает список моделей для провайдера."""
        return self.config.get(provider, {}).get('models', [])
    
    def set_provider_and_model(self, provider, model):
        """Устанавливает текущего провайдера и модель."""
        self.current_provider = provider
        self.current_model = model
    
    def send_message(self, prompt: str, temperature: float = 0.7, max_tokens: int = 300) -> str:
        """Отправляет запрос к текущему API."""
        if not self.current_provider or not self.current_model:
            return "Ошибка: Провайдер или модель не выбраны"
        
        provider_data = self.config.get(self.current_provider, {})
        api_key = provider_data.get('key', '')
        
        try:
            if self.current_provider == 'claude':
                return self._send_claude(prompt, api_key, temperature, max_tokens)
            elif self.current_provider == 'gemini':
                return self._send_gemini(prompt, api_key, temperature, max_tokens)
            elif self.current_provider in ['openrouter', 'chutes', 'featherless', 'moonshot']:
                api_url = provider_data.get('api', '')
                return self._send_openai_compatible(prompt, api_url, api_key, temperature, max_tokens)
            elif self.current_provider == 'deepseek':
                api_url = provider_data.get('api', '')
                return self._send_deepseek(prompt, api_url, api_key, temperature, max_tokens)
            else:
                return f"Провайдер {self.current_provider} не поддерживается"
        except Exception as e:
            return f"Ошибка API: {str(e)}"
    
    def _send_claude(self, prompt: str, api_key: str, temperature: float, max_tokens: int) -> str:
        """Отправка к Claude API."""
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=api_key, max_retries=0)
            response = client.messages.create(
                model=self.current_model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}]
            )
            return self._clean_text(response.content[0].text)
        except Exception as e:
            return f"Ошибка Claude: {str(e)}"
    
    def _send_gemini(self, prompt: str, api_key: str, temperature: float, max_tokens: int) -> str:
        """Отправка к Gemini API."""
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel(self.current_model)
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            response = model.generate_content(prompt, generation_config=generation_config)
            return self._clean_text(response.text)
        except Exception as e:
            return f"Ошибка Gemini: {str(e)}"
    
    def _send_openai_compatible(self, prompt: str, api_url: str, api_key: str, 
                                 temperature: float, max_tokens: int) -> str:
        """Отправка к OpenAI-совместимым API."""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.current_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }
        try:
            response = requests.post(api_url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            api_response = response.json()
            return self._clean_text(api_response["choices"][0]["message"]["content"])
        except Exception as e:
            return f"Ошибка API: {str(e)}"
    
    def _send_deepseek(self, prompt: str, api_url: str, api_key: str,
                       temperature: float, max_tokens: int) -> str:
        """Отправка к DeepSeek API."""
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key, base_url=api_url)
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=max_tokens,
                temperature=temperature,
                stream=False
            )
            return self._clean_text(response.choices[0].message.content)
        except Exception as e:
            return f"Ошибка DeepSeek: {str(e)}"
    
    def _clean_text(self, text: str) -> str:
        """Очищает текст от артефактов."""
        if not text:
            return "Ответ пустой"
        cut_tags = ["СТОП", "INST", "Human:", "Assistant:", "###"]
        for tag in cut_tags:
            if tag in text:
                text = text.split(tag)[0]
        return text.strip() if text.strip() else "Ответ пустой"
