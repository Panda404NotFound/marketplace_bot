from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# Главное меню
def get_main_menu():
    """Создать клавиатуру главного меню."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Мой кабинет", callback_data="cabinet"),
        InlineKeyboardButton("Оформить заказ", callback_data="new_order"),
        InlineKeyboardButton("Доставка", callback_data="delivery"),
        InlineKeyboardButton("Моя корзина", callback_data="cart")
    )
    return keyboard

# Клавиатура "Назад" и "Главное меню"
def get_back_menu():
    """Создать клавиатуру с кнопками "Назад" и "Главное меню"."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    )
    return keyboard

# Меню "Мой кабинет"
def get_cabinet_menu():
    """Создать клавиатуру для раздела "Мой кабинет"."""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("История заказов", callback_data="order_history"),
        InlineKeyboardButton("Мой профиль", callback_data="profile"),
        InlineKeyboardButton("Настройки", callback_data="settings")
    )
    # Добавляем кнопки "Назад" и "Главное меню"
    keyboard.row(
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    )
    return keyboard

# Меню "Доставка"
def get_delivery_menu():
    """Создать клавиатуру для раздела "Доставка"."""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Показать адрес", callback_data="show_address")
    )
    # Добавляем кнопки "Назад" и "Главное меню"
    keyboard.row(
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    )
    return keyboard

# Меню "Моя корзина"
def get_cart_menu():
    """Создать клавиатуру для раздела "Моя корзина"."""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Мои заказы", callback_data="my_orders"),
        InlineKeyboardButton("Удалить заказ", callback_data="delete_order"),
        InlineKeyboardButton("Оплатить все товары", callback_data="pay_orders")
    )
    # Добавляем кнопки "Назад" и "Главное меню"
    keyboard.row(
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    )
    return keyboard

# Методы оплаты
def get_payment_methods():
    """Создать клавиатуру с методами оплаты."""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("Карта МИР", callback_data="pay_mir"),
        InlineKeyboardButton("VISA/MASTERCARD", callback_data="pay_visa_mc")
    )
    # Добавляем кнопки "Назад" и "Главное меню"
    keyboard.row(
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    )
    return keyboard

# Динамическое создание клавиатуры со списком заказов для удаления
def get_orders_to_delete(orders):
    """
    Создать клавиатуру со списком заказов для удаления.
    
    Args:
        orders: список заказов в формате [{'id': 1, 'total_amount': 1000.0, ...}, ...]
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    if not orders:
        keyboard.add(InlineKeyboardButton("У вас нет заказов", callback_data="no_action"))
    else:
        for order in orders:
            order_id = order['id']
            total = order['total_amount']
            keyboard.add(
                InlineKeyboardButton(
                    f"Заказ #{order_id} - {total} ₽", 
                    callback_data=f"remove_order_{order_id}"
                )
            )
    
    # Добавляем кнопки "Назад" и "Главное меню"
    keyboard.row(
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    )
    
    return keyboard

# Клавиатура для подтверждения действия
def get_confirmation_keyboard(action, item_id):
    """
    Создать клавиатуру для подтверждения действия.
    
    Args:
        action: тип действия (например, 'remove_order')
        item_id: идентификатор элемента (например, id заказа)
    """
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("Да", callback_data=f"confirm_{action}_{item_id}"),
        InlineKeyboardButton("Нет", callback_data="cancel_action")
    )
    return keyboard

# Клавиатура для заказов пользователя
def get_user_orders_menu(orders, current_page=1, total_pages=1, has_pay_all_button=False):
    """
    Создать клавиатуру со списком заказов пользователя.
    
    Args:
        orders: список заказов в формате [{'id': 1, 'total_amount': 1000.0, ...}, ...]
        current_page: текущая страница (для пагинации)
        total_pages: общее количество страниц
        has_pay_all_button: добавить кнопку "Оплатить все заказы"
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    if not orders:
        keyboard.add(InlineKeyboardButton("У вас нет заказов", callback_data="no_action"))
    else:
        # Проверяем, есть ли неоплаченные заказы для возможности групповой оплаты
        has_unpaid_orders = any(order.get('status') == 'new' for order in orders)
        
        # Добавляем кнопку "Оплатить все заказы", если нужно и есть неоплаченные заказы
        if has_pay_all_button and has_unpaid_orders:
            keyboard.add(
                InlineKeyboardButton("💳 Оплатить все заказы", callback_data="pay_orders")
            )
        
        for order in orders:
            order_id = order['id']
            total = order['total_amount']
            status = order.get('status', 'new')
            
            # Определяем отображаемый статус
            status_display = {
                'new': 'Ожидает оплаты',
                'paid': 'Оплачен',
                'shipped': 'Отправлен',
                'delivered': 'Доставлен',
                'cancelled': 'Отменен'
            }.get(status, status)
            
            keyboard.add(
                InlineKeyboardButton(
                    f"Заказ #{order_id} - {total} ₽ ({status_display})", 
                    callback_data=f"order_details_{order_id}"
                )
            )
            # Добавляем кнопку "Оплатить", только если заказ не оплачен и не используется групповая оплата
            if status == 'new' and not has_pay_all_button:
                keyboard.add(
                    InlineKeyboardButton(
                        f"💳 Оплатить заказ #{order_id}", 
                        callback_data=f"pay_order_{order_id}"
                    )
                )
    
    # Добавляем кнопки пагинации, если всего страниц больше одной
    if total_pages > 1:
        nav_buttons = []
        
        # Кнопка "Предыдущая страница"
        if current_page > 1:
            nav_buttons.append(
                InlineKeyboardButton("◀️ Назад", callback_data="prev_page")
            )
        
        # Кнопка "Следующая страница"
        if current_page < total_pages:
            nav_buttons.append(
                InlineKeyboardButton("Вперед ▶️", callback_data="next_page")
            )
        
        # Добавляем кнопки навигации в клавиатуру
        keyboard.row(*nav_buttons)
    
    # Добавляем кнопки "Назад" и "Главное меню"
    keyboard.row(
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    )
    
    return keyboard

# Клавиатура с информацией о платеже и кнопкой "Оплатил"
def get_payment_info_keyboard(order_id):
    """
    Создать клавиатуру с информацией о платеже и кнопкой "Оплатил".
    
    Args:
        order_id: идентификатор заказа
    """
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("✅ Оплатил", callback_data=f"paid_order_{order_id}")
    )
    # Добавляем кнопки "Назад" и "Главное меню"
    keyboard.row(
        InlineKeyboardButton("◀️ Назад", callback_data="back"),
        InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
    )
    return keyboard 