# models/character.py
# -*- coding: utf-8 -*-
"""
Модель данных персонажа
"""
from typing import List, Dict

class Character:
    """Класс представления персонажа."""
    
    def __init__(self, char_id: str, name: str, private_prompt: str, 
                 group_prompt: str, photos: List[Dict] = None):
        self.char_id = char_id
        self.name = name
        self.private_prompt = private_prompt
        self.group_prompt = group_prompt
        self.photos = photos or []
