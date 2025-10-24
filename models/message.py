# models/message.py
# -*- coding: utf-8 -*-
"""
Модель данных сообщения
"""

class Message:
    """Класс представления сообщения."""
    
    def __init__(self, msg_id: str, sender: str, text: str, 
                 timestamp: str, msg_type: str = 'text', photo_path: str = ''):
        self.msg_id = msg_id
        self.sender = sender
        self.text = text
        self.timestamp = timestamp
        self.msg_type = msg_type
        self.photo_path = photo_path