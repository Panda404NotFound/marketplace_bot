from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from database.database import get_user, create_user, update_user
from keyboards.keyboards import get_main_menu
from keyboards.fallback import reset_navigation_history

class RegisterStates(StatesGroup):
    """Состояния для регистрации пользователя."""
    waiting_for_name = State()

async def cmd_start(message: types.Message, state: FSMContext):
    """Обработчик команды /start."""
    # Сбрасываем текущее состояние
    await state.finish()
    
    # Сбрасываем историю навигации
    user_id = message.from_user.id
    reset_navigation_history(user_id)
    
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # Проверяем, существует ли пользователь
    user = get_user(user_id)
    
    if not user:
        # Пользователь не существует, создаем и запрашиваем имя
        create_user(user_id, username, first_name, last_name)
        
        await message.answer(
            f"Добро пожаловать в бот-маркетплейс! 👋\n\n"
            f"Для начала, скажите, как к вам обращаться?"
        )
        
        # Устанавливаем состояние ожидания имени
        await RegisterStates.waiting_for_name.set()
    else:
        # Пользователь существует, показываем главное меню
        await message.answer(
            f"С возвращением! 👋\n\n"
            f"Выберите, что хотите сделать:",
            reply_markup=get_main_menu()
        )

async def cmd_reset(message: types.Message, state: FSMContext):
    """Обработчик команды /reset для сброса состояния бота."""
    # Сбрасываем текущее состояние
    await state.finish()
    
    # Сбрасываем историю навигации
    user_id = message.from_user.id
    reset_navigation_history(user_id)
    
    await message.answer(
        "Состояние бота сброшено! 🔄\n\n"
        "Выберите, что хотите сделать:",
        reply_markup=get_main_menu()
    )

async def process_name(message: types.Message, state: FSMContext):
    """Обработчик ввода имени пользователя."""
    user_id = message.from_user.id
    name = message.text
    
    # Обновляем имя пользователя
    update_user(user_id, first_name=name)
    
    # Завершаем состояние регистрации
    await state.finish()
    
    # Показываем главное меню
    await message.answer(
        f"Спасибо, {name}! Теперь вы можете пользоваться всеми функциями бота.\n\n"
        f"Выберите, что хотите сделать:",
        reply_markup=get_main_menu()
    )

async def cmd_help(message: types.Message):
    """Обработчик команды /help."""
    help_text = (
        "🛍️ <b>Бот-Маркетплейс</b> - удобный способ заказывать товары!\n\n"
        "<b>Основные команды:</b>\n"
        "• /start - Запуск бота и возврат в главное меню\n"
        "• /help - Показать это сообщение\n"
        "• /reset - Сбросить состояние бота (используйте при зависаниях)\n\n"
        
        "<b>Доступные функции:</b>\n"
        "• <b>Мой кабинет</b> - просмотр профиля, истории заказов и настроек\n"
        "• <b>Оформить заказ</b> - создание нового заказа\n"
        "• <b>Доставка</b> - информация о доставке\n" 
        "• <b>Моя корзина</b> - управление товарами в корзине\n\n"
        
        "<b>Как использовать:</b>\n"
        "• Отправьте ссылку на товар с Wildberries, Ozon или Яндекс.Маркета\n"
        "• Добавьте товар в корзину\n"
        "• Оформите и оплатите заказ\n\n"
        
        "Если у вас возникли вопросы или проблемы, обратитесь к администратору."
    )
    
    await message.answer(help_text, parse_mode='HTML')

async def process_callback(callback_query: types.CallbackQuery, state: FSMContext):
    """Общий обработчик callback_query для перехода между меню."""
    # TODO: Здесь будет обработка различных callback_query
    # Этот метод будет дополнен позже
    
    # Для примера - заглушка
    await callback_query.answer()

def register_common_handlers(dp):
    """Регистрация обработчиков общих команд."""
    dp.register_message_handler(cmd_start, commands=["start"], state="*")
    dp.register_message_handler(cmd_help, commands=["help"], state="*")
    dp.register_message_handler(cmd_reset, commands=["reset"], state="*")
    dp.register_message_handler(process_name, state=RegisterStates.waiting_for_name)
    
    # Обработчик callback_query будет дополнен в других файлах 