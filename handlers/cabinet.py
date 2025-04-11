from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from database.database import get_user, get_orders, get_order
from keyboards.keyboards import get_cabinet_menu, get_main_menu, get_back_menu, get_user_orders_menu, get_payment_methods
from config.config import DEFAULT_DELIVERY_ADDRESS

# Создаем класс состояний для пагинации
class OrderHistoryStates(StatesGroup):
    viewing_history = State()

async def process_cabinet(callback_query: types.CallbackQuery):
    """Обработчик для перехода в раздел 'Мой кабинет'."""
    await callback_query.answer()
    
    await callback_query.message.edit_text(
        "🏠 <b>Мой кабинет</b>\n\n"
        "Здесь вы можете управлять своим профилем, "
        "просматривать историю заказов и настройки.",
        reply_markup=get_cabinet_menu(),
        parse_mode='HTML'
    )

async def process_profile(callback_query: types.CallbackQuery):
    """Обработчик для просмотра профиля пользователя."""
    await callback_query.answer()
    
    user_id = callback_query.from_user.id
    user = get_user(user_id)
    
    if user:
        profile_text = (
            "👤 <b>Мой профиль</b>\n\n"
            f"Имя: {user.first_name or 'Не указано'}\n"
            f"Фамилия: {user.last_name or 'Не указана'}\n"
            f"Телефон: {user.phone or 'Не указан'}\n"
        )
    else:
        profile_text = "❌ Произошла ошибка при получении данных профиля."
    
    await callback_query.message.edit_text(
        profile_text,
        reply_markup=get_back_menu(),
        parse_mode='HTML'
    )

async def process_order_history(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик для просмотра истории заказов."""
    await callback_query.answer()
    
    # Извлекаем номер страницы из callback_data, если он есть
    page = 1
    if '_' in callback_query.data:
        try:
            # Формат: order_history_page_X
            parts = callback_query.data.split('_')
            if len(parts) >= 4 and parts[0] == 'order' and parts[1] == 'history' and parts[2] == 'page':
                page = int(parts[3])
        except (ValueError, IndexError):
            page = 1
    
    user_id = callback_query.from_user.id
    orders = get_orders(user_id)
    
    if not orders:
        await callback_query.message.edit_text(
            "📋 <b>История заказов</b>\n\n"
            "У вас пока нет оформленных заказов.",
            reply_markup=get_back_menu(),
            parse_mode='HTML'
        )
        return
    
    # Количество заказов на странице
    items_per_page = 5
    
    # Вычисляем общее количество страниц
    total_pages = (len(orders) + items_per_page - 1) // items_per_page
    
    # Проверяем валидность номера страницы
    if page < 1:
        page = 1
    elif page > total_pages:
        page = total_pages
    
    # Определяем диапазон заказов для текущей страницы
    start_idx = (page - 1) * items_per_page
    end_idx = min(start_idx + items_per_page, len(orders))
    
    # Получаем заказы для текущей страницы
    current_page_orders = orders[start_idx:end_idx]
    
    # Формируем текст истории заказов
    history_text = f"📋 <b>История заказов</b> (страница {page}/{total_pages})\n\n"
    
    for order in current_page_orders:
        try:
            order_id = order.id
            order_date = order.created_at.strftime('%d.%m.%Y %H:%M')
            
            # Форматируем статус заказа
            status_raw = order.status
            status_display = {
                'new': 'Ожидает оплаты',
                'paid': 'Оплачен',
                'shipped': 'Отправлен',
                'delivered': 'Доставлен',
                'cancelled': 'Отменен'
            }.get(status_raw, status_raw)
            
            # Добавляем эмодзи в зависимости от статуса
            status_emoji = {
                'new': '⏳',
                'paid': '✅',
                'shipped': '🚚',
                'delivered': '📦',
                'cancelled': '❌'
            }.get(status_raw, '❓')
            
            status_display = f"{status_emoji} {status_display}"
            
            payment_method = order.payment_method.upper() if order.payment_method else "Не указан"
            delivery_address = order.delivery_address or "Не указан"
            
            history_text += (
                f"<b>Заказ #{order_id}</b>\n"
                f"Дата: {order_date}\n"
                f"Статус: {status_display}\n"
                f"Способ оплаты: {payment_method}\n"
                f"Адрес доставки: {delivery_address}\n\n"
            )
        except Exception as e:
            print(f"Ошибка при обработке заказа: {e}")
            # Пропускаем этот заказ в случае ошибки
    
    # Сохраняем информацию о пагинации в состоянии
    await state.update_data(
        total_pages=total_pages,
        current_page=page
    )
    
    # Устанавливаем состояние просмотра истории
    await OrderHistoryStates.viewing_history.set()
    
    # Создаем клавиатуру только с кнопками навигации
    keyboard = InlineKeyboardMarkup(row_width=2)
    
    # Добавляем кнопки пагинации, если всего страниц больше одной
    if total_pages > 1:
        nav_buttons = []
        
        # Кнопка "Предыдущая страница"
        if page > 1:
            nav_buttons.append(
                InlineKeyboardButton("◀️ Назад", callback_data="prev_page")
            )
        
        # Кнопка "Следующая страница"
        if page < total_pages:
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
    
    await callback_query.message.edit_text(
        history_text,
        reply_markup=keyboard,
        parse_mode='HTML'
    )

async def process_order_history_navigation(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик навигации по страницам истории заказов."""
    # Получаем информацию о пагинации из состояния
    data = await state.get_data()
    current_page = data.get('current_page', 1)
    total_pages = data.get('total_pages', 1)
    
    # Определяем направление навигации
    if callback_query.data == 'prev_page':
        page = max(1, current_page - 1)
    elif callback_query.data == 'next_page':
        page = min(total_pages, current_page + 1)
    else:
        await callback_query.answer("Неизвестная команда навигации")
        return
    
    # Вызываем обработчик истории заказов с новым номером страницы
    callback_query.data = f"order_history_page_{page}"
    await process_order_history(callback_query, state)

async def process_settings(callback_query: types.CallbackQuery):
    """Обработчик для просмотра настроек (заглушка)."""
    await callback_query.answer()
    
    settings_text = (
        "⚙️ <b>Настройки</b>\n\n"
        "В данный момент настройки недоступны.\n"
        "Эта функция будет добавлена в будущих обновлениях."
    )
    
    await callback_query.message.edit_text(
        settings_text,
        reply_markup=get_back_menu(),
        parse_mode='HTML'
    )

async def process_pay_order_from_history(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик для кнопки 'Оплатить заказ' из истории заказов."""
    await callback_query.answer()
    
    # Получаем ID заказа из callback_data
    order_id = int(callback_query.data.split('_')[-1])
    
    # Получаем информацию о заказе для установки адреса доставки
    order_info = get_order(order_id)
    
    if order_info:
        # Сохраняем ID заказа и адрес доставки в состояние
        await state.update_data(
            order_id=order_id, 
            delivery_address=order_info.get('delivery_address') or ""
        )
    else:
        # Используем адрес по умолчанию, если информацию о заказе не удалось получить
        await state.update_data(
            order_id=order_id,
            delivery_address=DEFAULT_DELIVERY_ADDRESS
        )
    
    await callback_query.message.edit_text(
        f"💰 <b>Оплата заказа #{order_id}</b>\n\n"
        f"Выберите способ оплаты:",
        reply_markup=get_payment_methods(),
        parse_mode='HTML'
    )
    
    # Устанавливаем состояние ожидания выбора метода оплаты
    from handlers.cart import PaymentStates
    await PaymentStates.waiting_for_payment_method.set()

def register_cabinet_handlers(dp):
    """Регистрация обработчиков для раздела 'Мой кабинет'."""
    dp.register_callback_query_handler(process_cabinet, lambda c: c.data == "cabinet")
    dp.register_callback_query_handler(
        process_order_history, 
        lambda c: c.data == "order_history" or c.data.startswith("order_history_page_")
    )
    dp.register_callback_query_handler(
        process_order_history_navigation,
        lambda c: c.data in ['prev_page', 'next_page'],
        state=OrderHistoryStates.viewing_history
    )
    dp.register_callback_query_handler(process_profile, lambda c: c.data == "profile")
    dp.register_callback_query_handler(process_settings, lambda c: c.data == "settings")
    
    # Обработчик для оплаты заказа из истории
    dp.register_callback_query_handler(
        process_pay_order_from_history, 
        lambda c: c.data.startswith("pay_order_")
    ) 