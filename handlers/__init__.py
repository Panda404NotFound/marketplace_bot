"""
Определяет маршрутизацию обработчиков сообщений в боте.
"""

from aiogram import Dispatcher

from handlers.common import register_common_handlers
from handlers.navigation import register_navigation_handlers
from handlers.orders import register_order_handlers
from handlers.delivery import register_delivery_handlers
from handlers.cart import register_cart_handlers
from handlers.cabinet import register_cabinet_handlers

def register_all_handlers(dp: Dispatcher):
    """
    Регистрирует все обработчики бота.
    
    Args:
        dp: Экземпляр диспетчера бота
    """
    # Порядок регистрации имеет значение!
    
    # Сначала регистрируем общие обработчики
    register_common_handlers(dp)
    
    # Регистрируем обработчики навигации
    # важно регистрировать их раньше других специфических обработчиков,
    # чтобы fallback обработчики имели приоритет
    register_navigation_handlers(dp)
    
    # Затем специфические обработчики
    register_order_handlers(dp)
    register_delivery_handlers(dp)
    register_cart_handlers(dp)
    register_cabinet_handlers(dp) 