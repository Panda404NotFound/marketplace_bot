from aiogram import types
from aiogram.dispatcher import FSMContext

from keyboards.keyboards import get_main_menu

async def process_main_menu(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработчик для возврата в главное меню."""
    await callback_query.answer()
    
    # Сбрасываем текущее состояние
    current_state = await state.get_state()
    if current_state:
        await state.finish()
    
    await callback_query.message.edit_text(
        "Выберите, что хотите сделать:",
        reply_markup=get_main_menu()
    )

async def process_back(callback_query: types.CallbackQuery):
    """
    Обработчик для кнопки "Назад".
    
    Эта функция обрабатывает общий случай - возврат в родительское меню.
    Для разных разделов возврат назад может быть разным, и это 
    обрабатывается в соответствующих файлах-обработчиках.
    """
    await callback_query.answer()
    
    # Стандартное поведение - возврат в главное меню
    # В большинстве случаев это будет переопределено в специфических обработчиках
    await callback_query.message.edit_text(
        "Выберите, что хотите сделать:",
        reply_markup=get_main_menu()
    )

def register_navigation_handlers(dp):
    """Регистрация обработчиков навигации."""
    # Обработчик для кнопки главного меню
    dp.register_callback_query_handler(
        process_main_menu,
        lambda c: c.data == "main_menu",
        state="*"
    )
    
    # Обработчик для кнопки "Назад"
    # Этот обработчик будет иметь низкий приоритет,
    # чтобы специфические обработчики в других файлах могли его переопределить
    dp.register_callback_query_handler(
        process_back,
        lambda c: c.data == "back",
        state="*"
    ) 