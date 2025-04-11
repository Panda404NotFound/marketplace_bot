"""
Модуль администрирования для бота-маркетплейса.
Содержит функции для отправки сообщений администратору и в группу.
"""

from admin.notification import send_order_to_chat

__all__ = ['send_order_to_chat'] 