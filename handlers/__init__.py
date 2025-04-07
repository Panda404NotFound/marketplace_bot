from .common import register_common_handlers
from .cabinet import register_cabinet_handlers
from .orders import register_order_handlers
from .delivery import register_delivery_handlers
from .cart import register_cart_handlers
from .navigation import register_navigation_handlers

def register_all_handlers(dp):
    """Регистрация всех обработчиков."""
    # Порядок регистрации важен!
    # Обработчики с более высоким приоритетом (более специфичные) должны быть зарегистрированы раньше
    
    # Регистрация обработчиков навигации
    register_navigation_handlers(dp)
    
    # Регистрация обработчиков для разделов
    register_cabinet_handlers(dp)
    register_order_handlers(dp)
    register_delivery_handlers(dp)
    register_cart_handlers(dp)
    
    # Регистрация общих обработчиков
    register_common_handlers(dp) 