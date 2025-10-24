# models/group.py
# -*- coding: utf-8 -*-
"""
Модель данных группы
"""
from typing import List

class Group:
    """Класс представления группы."""
    
    def __init__(self, group_id: str, name: str, members: List[str], group_context: str = ''):
        self.group_id = group_id
        self.name = name
        self.members = members
        self.group_context = group_context
