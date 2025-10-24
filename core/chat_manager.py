# core/chat_manager.py
# -*- coding: utf-8 -*-
"""
Управление чатами и историей сообщений
"""
import json
import os
import yaml
from datetime import datetime
from typing import Dict, List, Optional
from models.character import Character
from models.group import Group
from models.message import Message
from config.settings import CHARACTERS_DIR, GROUPS_DIR, CHATS_DIR, MAX_MESSAGES_IN_HISTORY, MAX_MESSAGES_FOR_API

class ChatManager:
    """Класс для управления чатами."""
    
    def __init__(self):
        self.characters: Dict[str, Character] = {}
        self.groups: Dict[str, Group] = {}
        self.chats: Dict[str, List[Message]] = {}
        self._ensure_directories()
        self.load_all_data()
    
    def _ensure_directories(self):
        """Создает необходимые директории."""
        for directory in [CHARACTERS_DIR, GROUPS_DIR, CHATS_DIR]:
            os.makedirs(directory, exist_ok=True)
    
    def load_all_data(self):
        """Загружает всех персонажей, группы и чаты."""
        self._load_characters()
        self._load_groups()
        self._load_chats()
    
    def _load_characters(self):
        """Загружает персонажей из файлов."""
        if not os.path.exists(CHARACTERS_DIR):
            return
        for char_folder in os.listdir(CHARACTERS_DIR):
            char_path = os.path.join(CHARACTERS_DIR, char_folder)
            if not os.path.isdir(char_path):
                continue
            config_path = os.path.join(char_path, "character.yml")
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    char = Character(
                        char_id=data['id'],
                        name=data['name'],
                        private_prompt=data.get('private_prompt', ''),
                        group_prompt=data.get('group_prompt', ''),
                        photos=data.get('photos', [])
                    )
                    self.characters[char.char_id] = char
    
    def _load_groups(self):
        """Загружает группы из файлов."""
        if not os.path.exists(GROUPS_DIR):
            return
        for group_file in os.listdir(GROUPS_DIR):
            if group_file.endswith('.yml'):
                with open(os.path.join(GROUPS_DIR, group_file), 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    group = Group(
                        group_id=data['id'],
                        name=data['name'],
                        members=data.get('members', []),
                        group_context=data.get('group_context', '')
                    )
                    self.groups[group.group_id] = group
    
    def _load_chats(self):
        """Загружает историю чатов."""
        if not os.path.exists(CHATS_DIR):
            return
        for chat_file in os.listdir(CHATS_DIR):
            if chat_file.endswith('.json'):
                chat_id = chat_file.replace('.json', '')
                messages = self._load_chat_history(chat_id)
                self.chats[chat_id] = messages
    
    def _load_chat_history(self, chat_id: str) -> List[Message]:
        """Загружает историю конкретного чата."""
        chat_path = os.path.join(CHATS_DIR, f"{chat_id}.json")
        if not os.path.exists(chat_path):
            return []
        try:
            with open(chat_path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return []
                data = json.loads(content)
                messages = []
                for msg_data in data.get('messages', []):
                    msg = Message(
                        msg_id=msg_data['id'],
                        sender=msg_data['sender'],
                        text=msg_data.get('text', ''),
                        timestamp=msg_data['timestamp'],
                        msg_type=msg_data['type'],
                        photo_path=msg_data.get('photo_path', '')
                    )
                    messages.append(msg)
                return messages
        except Exception as e:
            print(f"Ошибка загрузки чата {chat_id}: {e}")
            return []
    
    def save_chat_history(self, chat_id: str):
        """Сохраняет историю чата."""
        if chat_id not in self.chats:
            return
        
        chat_type = 'group' if chat_id in self.groups else 'private'
        character_id = None if chat_type == 'group' else chat_id
        
        messages_data = []
        for msg in self.chats[chat_id][-MAX_MESSAGES_IN_HISTORY:]:
            msg_dict = {
                'id': msg.msg_id,
                'sender': msg.sender,
                'text': msg.text,
                'timestamp': msg.timestamp,
                'type': msg.msg_type
            }
            if msg.photo_path:
                msg_dict['photo_path'] = msg.photo_path
            messages_data.append(msg_dict)
        
        chat_data = {
            'chat_id': chat_id,
            'chat_type': chat_type,
            'character_id': character_id,
            'messages': messages_data
        }
        
        chat_path = os.path.join(CHATS_DIR, f"{chat_id}.json")
        with open(chat_path, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, ensure_ascii=False, indent=2)
    
    def add_message(self, chat_id: str, sender: str, text: str, msg_type: str = 'text', photo_path: str = ''):
        """Добавляет сообщение в чат."""
        if chat_id not in self.chats:
            self.chats[chat_id] = []
        
        msg = Message(
            msg_id=f"msg_{int(datetime.now().timestamp() * 1000)}",
            sender=sender,
            text=text,
            timestamp=datetime.now().isoformat(),
            msg_type=msg_type,
            photo_path=photo_path
        )
        self.chats[chat_id].append(msg)
        self.save_chat_history(chat_id)
        return msg
    
    def get_chat_messages(self, chat_id: str) -> List[Message]:
        """Возвращает сообщения чата."""
        return self.chats.get(chat_id, [])
    
    def build_prompt(self, chat_id: str, character: Character, is_group: bool = False) -> str:
        """Формирует промпт для API."""
        system_prompt = character.group_prompt if is_group else character.private_prompt
        
        if is_group and chat_id in self.groups:
            group = self.groups[chat_id]
            members_names = ', '.join([
                self.characters.get(m, Character(m, m, '', '', [])).name 
                for m in group.members
            ])
            system_prompt = system_prompt.format(
                group_name=group.name,
                members=members_names
            )
        
        messages = self.chats.get(chat_id, [])[-MAX_MESSAGES_FOR_API:]
        history_text = ""
        for msg in messages:
            if msg.msg_type == 'text':
                sender_name = "Пользователь" if msg.sender == 'user' else \
                              self.characters.get(msg.sender, Character(msg.sender, msg.sender, '', '', [])).name
                history_text += f"{sender_name}: {msg.text}\n"
        
        return f"{system_prompt}\n\nИстория переписки:\n{history_text}\nОтветь на последнее сообщение."
    
    def create_group(self, name: str, members: List[str]) -> str:
        """Создает новую группу."""
        group_id = f"group_{int(datetime.now().timestamp())}"
        group = Group(
            group_id=group_id,
            name=name,
            members=members,
            group_context=f"Групповой чат '{name}'"
        )
        self.groups[group_id] = group
        
        group_data = {
            'id': group_id,
            'name': name,
            'members': members,
            'group_context': group.group_context
        }
        
        group_path = os.path.join(GROUPS_DIR, f"{group_id}.yml")
        with open(group_path, 'w', encoding='utf-8') as f:
            yaml.dump(group_data, f, allow_unicode=True, default_flow_style=False)
        
        self.chats[group_id] = []
        return group_id
