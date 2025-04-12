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
            f"Выберите, что хотите сделать:\n"
            f"• 👤 Мой кабинет - профиль, заказы, настройки\n"
            f"• 🛍️ Оформить заказ - добавить новый товар\n"
            f"• 🚚 Доставка - информация о доставке\n"
            f"• 🛒 Моя корзина - управление товарами\n\n"
            f"📌 В любой момент можно вернуться в главное меню или ввести /help для справки"
            ,
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
        "Выберите, что хотите сделать:\n"
        "• 👤 Мой кабинет - профиль, заказы, настройки\n"
        "• 🛍️ Оформить заказ - добавить новый товар\n"
        "• 🚚 Доставка - информация о доставке\n"
        "• 🛒 Моя корзина - управление товарами\n\n"
        "📌 В любой момент можно вернуться в главное меню или ввести /help для справки"
        ,
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
        f"Выберите, что хотите сделать:\n"
        f"• 👤 Мой кабинет - профиль, заказы, настройки\n"
        f"• 🛍️ Оформить заказ - добавить новый товар\n"
        f"• 🚚 Доставка - информация о доставке\n"
        f"• 🛒 Моя корзина - управление товарами\n\n"
        f"📌 В любой момент можно вернуться в главное меню или ввести /help для справки"
        ,
        reply_markup=get_main_menu()
    )

async def cmd_help(message: types.Message):
    """Обработчик команды /help."""
    help_text = (
        "🛍️ <b>Бот-Маркетплейс</b> - удобный способ заказывать товары!\n\n"
        "<b>Основные команды:</b>\n"
        "• /start - Запуск бота и возврат в главное меню\n"
        "• /help - Показать это сообщение\n"
        "• /instruction - Подробная инструкция по покупке\n"
        "• /reset - Сбросить состояние бота (используйте при зависаниях)\n\n"
        
        "<b>Доступные функции:</b>\n"
        "• <b>Мой кабинет</b> - просмотр профиля, истории заказов и настроек\n"
        "• <b>Оформить заказ</b> - создание нового заказа\n"
        "• <b>Доставка</b> - информация о доставке\n" 
        "• <b>Моя корзина</b> - управление товарами в корзине\n\n"
        
        "<b>Как сделать заказ:</b>\n"
        "1. Нажмите 'Оформить заказ' в главном меню\n"
        "2. Отправьте ссылку на товар с Wildberries, Ozon или Яндекс.Маркета\n"
        "3. Укажите количество, размер и цвет товара\n"
        "4. После добавления товара перейдите в 'Моя корзина'\n"
        "5. Нажмите 'Оплатить все товары'\n"
        "6. Выберите способ оплаты\n"
        "7. После оплаты нажмите кнопку 'Оплатил'\n"
        "8. Дождитесь связи менеджера для подтверждения заказа\n\n"
        
        "<b>Важно:</b> По всем вопросам, проблемам или обнаруженным ошибкам обращайтесь к менеджеру."
    )
    
    # Используем существующую функцию для создания клавиатуры главного меню
    keyboard = get_main_menu()
    
    await message.answer(help_text, reply_markup=keyboard, parse_mode='HTML')

async def cmd_instruction(message: types.Message):
    """Обработчик команды /instruction."""
    instruction_text = (
        "🔍 <b>Как правильно оформить заказ</b>\n\n"
        "<b>Перед отправкой ссылки:</b>\n"
        "• Тщательно выберите товар на маркетплейсе (Wildberries, Ozon, Яндекс.Маркет)\n"
        "• Определитесь с моделью, цветом и размером заранее\n"
        "• Проверьте наличие товара на маркетплейсе\n"
        "• После чего отправьте ссылку на товар в бот\n\n"
        
        "<b>Процесс оформления заказа:</b>\n"
        "1. Нажмите кнопку '🛍️ Оформить заказ' в главном меню\n"
        "2. Отправьте боту ссылку на выбранный товар\n"
        "3. Внимательно укажите количество, размер и цвет товара\n"
        "4. Проверьте данные перед добавлением в корзину\n"
        "5. Перейдите в '🛒 Моя корзина' и нажмите 'Оплатить все товары'\n"
        "6. Выберите подходящий способ оплаты\n"
        "7. После совершения оплаты нажмите кнопку 'Оплатил'\n\n"
        
        "<b>Важно:</b>\n"
        "• Внимательно проверяйте все детали заказа перед подтверждением\n"
        "• Сохраняйте чек об оплате до получения товара\n"
        "• По любым вопросам и проблемам сразу обращайтесь к менеджеру\n\n"
        
        "Желаем вам приятных покупок! 🛒✨"
    )
    
    # Используем существующую функцию для создания клавиатуры главного меню
    keyboard = get_main_menu()
    
    await message.answer(instruction_text, reply_markup=keyboard, parse_mode='HTML')

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
    dp.register_message_handler(cmd_instruction, commands=["instruction"], state="*")
    dp.register_message_handler(cmd_reset, commands=["reset"], state="*")
    dp.register_message_handler(process_name, state=RegisterStates.waiting_for_name)
    
    # Обработчик callback_query будет дополнен в других файлах 