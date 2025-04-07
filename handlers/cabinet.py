from aiogram import types
from aiogram.dispatcher import FSMContext

from database.database import get_user, get_orders
from keyboards.keyboards import get_cabinet_menu, get_main_menu, get_back_menu

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

async def process_order_history(callback_query: types.CallbackQuery):
    """Обработчик для просмотра истории заказов."""
    await callback_query.answer()
    
    user_id = callback_query.from_user.id
    orders = get_orders(user_id)
    
    if orders:
        # Формируем текст с историей заказов
        orders_text = "📦 <b>История заказов</b>\n\n"
        
        for order in orders:
            order_id = order['id']
            total = order['total_amount']
            status = order['status']
            date = order['created_at'].strftime('%d.%m.%Y %H:%M')
            
            # Статусы заказов на русском
            status_ru = {
                'new': 'Новый',
                'paid': 'Оплачен',
                'shipped': 'Отправлен',
                'delivered': 'Доставлен',
                'cancelled': 'Отменен'
            }
            
            orders_text += (
                f"<b>Заказ #{order_id}</b>\n"
                f"Дата: {date}\n"
                f"Сумма: {total} ₽\n"
                f"Статус: {status_ru.get(status, status)}\n\n"
            )
    else:
        orders_text = "📦 <b>История заказов</b>\n\nУ вас пока нет заказов."
    
    await callback_query.message.edit_text(
        orders_text,
        reply_markup=get_back_menu(),
        parse_mode='HTML'
    )

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

def register_cabinet_handlers(dp):
    """Регистрация обработчиков раздела 'Мой кабинет'."""
    dp.register_callback_query_handler(process_cabinet, lambda c: c.data == "cabinet")
    dp.register_callback_query_handler(process_profile, lambda c: c.data == "profile")
    dp.register_callback_query_handler(process_order_history, lambda c: c.data == "order_history")
    dp.register_callback_query_handler(process_settings, lambda c: c.data == "settings") 