from aiogram import types
from aiogram.dispatcher import FSMContext

from keyboards.keyboards import get_main_menu
from keyboards.fallback import register_fallback_handlers

async def process_main_menu(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик для возврата в главное меню."""
    try:
        await callback_query.answer()
        
        # Сбрасываем текущее состояние
        current_state = await state.get_state()
        if current_state:
            await state.finish()
        
        # Сбрасываем историю навигации
        from keyboards.fallback import user_navigation_history
        user_id = callback_query.from_user.id
        if user_id in user_navigation_history:
            user_navigation_history[user_id] = []
        
        await callback_query.message.edit_text(
            "Выберите, что хотите сделать:\n"
            "• 👤 Мой кабинет - профиль, заказы, настройки\n"
            "• 🛍️ Оформить заказ - добавить новый товар\n"
            "• 🚚 Доставка - информация о доставке\n"
            "• 🛒 Моя корзина - управление товарами\n\n"
            "📌 В любой момент можно вернуться в главное меню или ввести /help для справки",
            reply_markup=get_main_menu()
        )
    except Exception as e:
        print(f"Error in process_main_menu for user {callback_query.from_user.id}: {e}")
        # В случае ошибки пытаемся отправить новое сообщение
        try:
            await callback_query.message.reply(
                "Произошла ошибка. Выберите действие:\n"
                "• 👤 Мой кабинет - профиль, заказы, настройки\n"
                "• 🛍️ Оформить заказ - добавить новый товар\n"
                "• 🚚 Доставка - информация о доставке\n"
                "• 🛒 Моя корзина - управление товарами",
                reply_markup=get_main_menu()
            )
        except:
            pass

def register_navigation_handlers(dp):
    """Регистрация обработчиков навигации."""
    # Обработчик для кнопки главного меню
    dp.register_callback_query_handler(
        process_main_menu,
        lambda c: c.data == "main_menu",
        state="*"
    )
    
    # Регистрируем обработчики из модуля fallback
    register_fallback_handlers(dp)
    
    # Обработчик для кнопки "Назад" теперь регистрируется в fallback.py
    # dp.register_callback_query_handler(
    #     process_back,
    #     lambda c: c.data == "back",
    #     state="*"
    # ) 