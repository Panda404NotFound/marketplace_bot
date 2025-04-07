from aiogram import types
from aiogram.dispatcher import FSMContext

from config.config import DEFAULT_DELIVERY_ADDRESS
from keyboards.keyboards import get_delivery_menu, get_back_menu

async def process_delivery(callback_query: types.CallbackQuery):
    """Обработчик для перехода в раздел 'Доставка'."""
    await callback_query.answer()
    
    await callback_query.message.edit_text(
        "🚚 <b>Доставка</b>\n\n"
        "В этом разделе вы можете узнать информацию о доставке ваших заказов.",
        reply_markup=get_delivery_menu(),
        parse_mode='HTML'
    )

async def process_show_address(callback_query: types.CallbackQuery):
    """Обработчик для отображения адреса доставки."""
    await callback_query.answer()
    
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