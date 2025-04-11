from aiogram import types
from aiogram.dispatcher import FSMContext

from config.config import DEFAULT_DELIVERY_ADDRESS
from keyboards.keyboards import get_delivery_menu, get_back_menu, get_main_menu
from keyboards.fallback import save_navigation_state, reset_navigation_history

async def process_delivery(callback_query: types.CallbackQuery):
    """Обработчик для перехода в раздел 'Доставка'."""
    try:
        await callback_query.answer()
        
        # Сохраняем текущее состояние навигации
        user_id = callback_query.from_user.id
        
        # При переходе к основным разделам лучше не сохранять историю
        # Это поможет избежать цикличных переходов между основными разделами
        if callback_query.data == "delivery":
            reset_navigation_history(user_id)
        
        await save_navigation_state(user_id, 'delivery')
        
        await callback_query.message.edit_text(
            "🚚 <b>Доставка</b>\n\n"
            "В этом разделе вы можете узнать информацию о доставке ваших заказов.",
            reply_markup=get_delivery_menu(),
            parse_mode='HTML'
        )
    except Exception as e:
        # print(f"Error in process_delivery for user {user_id}: {e}")
        try:
            await callback_query.message.edit_text(
                "Произошла ошибка. Выберите действие:",
                reply_markup=get_main_menu()
            )
        except:
            pass

async def process_show_address(callback_query: types.CallbackQuery):
    """Обработчик для отображения адреса доставки."""
    await callback_query.answer()
    
    # Сохраняем текущее состояние навигации
    user_id = callback_query.from_user.id
    await save_navigation_state(user_id, 'show_address')
    
    address_text = (
        "📍 <b>Адрес доставки</b>\n\n"
        f"{DEFAULT_DELIVERY_ADDRESS}\n\n"
        "<i>В текущей версии бота доступна доставка только на этот адрес.</i>"
    )
    
    await callback_query.message.edit_text(
        address_text,
        reply_markup=get_back_menu(),
        parse_mode='HTML'
    )

def register_delivery_handlers(dp):
    """Регистрация обработчиков раздела 'Доставка'."""
    dp.register_callback_query_handler(process_delivery, lambda c: c.data == "delivery")
    dp.register_callback_query_handler(process_show_address, lambda c: c.data == "show_address") 