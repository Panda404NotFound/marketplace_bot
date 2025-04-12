from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.utils.exceptions import MessageNotModified
import time

from keyboards.keyboards import (
    get_main_menu, get_cabinet_menu, get_delivery_menu, 
    get_cart_menu, get_payment_methods, get_back_menu
)

# Словарь для хранения предыдущих состояний пользователя
# Структура: {user_id: {'prev_screen': 'main', 'prev_data': {...}}}
user_navigation_history = {}

# Словарь соответствия разделов и функций для возврата к этим разделам
menu_generators = {
    'main': get_main_menu,
    'cabinet': get_cabinet_menu, 
    'delivery': get_delivery_menu,
    'cart': get_cart_menu,
    'payment': get_payment_methods,
}

# Словарь текстов для разных экранов
screen_texts = {
    'main': "Выберите, что хотите сделать:\n"
            "• 👤 Мой кабинет - профиль, заказы, настройки\n"
            "• 🛍️ Оформить заказ - добавить новый товар\n"
            "• 🚚 Доставка - информация о доставке\n"
            "• 🛒 Моя корзина - управление товарами\n\n"
            "📌 В любой момент можно вернуться в главное меню или ввести /help для справки",
    'cabinet': "👤 <b>Мой кабинет</b>\n\n"
               "Здесь вы можете управлять своим профилем, просматривать историю заказов и настройки.",
    'delivery': "🚚 <b>Доставка</b>\n\n"
                "Информация о доставке и вариантах получения заказа.",
    'cart': "🛒 <b>Моя корзина</b>\n\n"
            "Здесь отображаются ваши товары, можно управлять корзиной и оформлять заказы.",
    'payment': "💳 <b>Оплата</b>\n\n"
              "Выберите удобный способ оплаты для вашего заказа:"
}

async def save_navigation_state(user_id: int, screen: str, state_data=None):
    """
    Сохраняет текущий экран пользователя для возможности возврата назад.
    
    Args:
        user_id: ID пользователя
        screen: Идентификатор экрана (например, 'main', 'cabinet', 'profile')
        state_data: Дополнительные данные состояния (для экранов с параметрами)
    """
    if user_id not in user_navigation_history:
        user_navigation_history[user_id] = []
    
    # Добавляем новый экран в историю
    # Даже если предыдущий экран такой же, мы всё равно сохраняем,
    # чтобы корректно обрабатывать случаи повторного просмотра одного экрана
    user_navigation_history[user_id].append({
        'screen': screen,
        'state_data': state_data or {},
        'timestamp': int(time.time())  # Добавляем временную метку для дополнительного контроля
    })
    
    # Ограничиваем историю до 10 записей
    if len(user_navigation_history[user_id]) > 10:
        user_navigation_history[user_id].pop(0)
    
    # Для отладки - выводим в лог текущую историю навигации
    # print(f"Navigation history for user {user_id}: {[item['screen'] for item in user_navigation_history[user_id]]}")

async def get_previous_screen(user_id: int):
    """
    Получает предыдущий экран пользователя.
    
    Args:
        user_id: ID пользователя
        
    Returns:
        tuple: (screen, state_data) или ('main', {}) если истории нет
    """
    # Проверяем, что у пользователя есть история навигации
    if user_id not in user_navigation_history:
        # print(f"No navigation history for user {user_id}")
        return 'main', {}
    
    # Проверяем, что в истории есть хотя бы два элемента
    # (текущий экран и предыдущий)
    if len(user_navigation_history[user_id]) < 2:
        # print(f"Not enough history for user {user_id}, only {len(user_navigation_history[user_id])} items")
        return 'main', {}
    
    # Удаляем текущий экран
    current_screen = user_navigation_history[user_id].pop()
    
    # Получаем предыдущий экран
    prev_screen = user_navigation_history[user_id][-1]
    
    # Для отладки - выводим информацию о переходе
    # print(f"User {user_id} navigating back from '{current_screen['screen']}' to '{prev_screen['screen']}'")
    
    return prev_screen['screen'], prev_screen['state_data']

async def process_fallback(callback_query: types.CallbackQuery, state: FSMContext):
    """
    Обработчик для кнопки "Назад" с логикой возврата на предыдущий экран.
    
    Args:
        callback_query: Объект callback_query
        state: FSMContext для работы с состоянием
    """
    try:
        await callback_query.answer()
        
        user_id = callback_query.from_user.id
        prev_screen, prev_data = await get_previous_screen(user_id)
        
        # Проверяем, что меню для предыдущего экрана существует
        if prev_screen in menu_generators:
            try:
                # Получаем текст и клавиатуру для предыдущего экрана
                menu_markup = menu_generators[prev_screen]()
                screen_text = screen_texts.get(prev_screen, "Выберите действие:")
                
                # Обновляем сообщение
                await callback_query.message.edit_text(
                    screen_text,
                    reply_markup=menu_markup,
                    parse_mode='HTML'
                )
                # print(f"Successfully navigated user {user_id} back to '{prev_screen}'")
            except MessageNotModified:
                # Игнорируем исключение, если сообщение не изменилось
                # print(f"Message not modified for user {user_id} when navigating to '{prev_screen}'")
                pass
            except Exception as e:
                # Логируем ошибку
                # print(f"Error navigating back to '{prev_screen}' for user {user_id}: {e}")
                # В случае ошибки пытаемся вернуться в главное меню
                await callback_query.message.edit_text(
                    "Выберите, что хотите сделать:\n"
                    "• 👤 Мой кабинет - профиль, заказы, настройки\n"
                    "• 🛍️ Оформить заказ - добавить новый товар\n"
                    "• 🚚 Доставка - информация о доставке\n"
                    "• 🛒 Моя корзина - управление товарами\n\n"
                    "📌 В любой момент можно вернуться в главное меню или ввести /help для справки",
                    reply_markup=get_main_menu()
                )
        else:
            # Если предыдущий экран не найден в menu_generators,
            # проверяем его дополнительно
            if prev_screen == 'profile':
                # Особая обработка для профиля
                await callback_query.message.edit_text(
                    "🏠 <b>Мой кабинет</b>\n\n"
                    "Здесь вы можете управлять своим профилем, "
                    "просматривать историю заказов и настройки.",
                    reply_markup=get_cabinet_menu(),
                    parse_mode='HTML'
                )
            elif prev_screen == 'show_address':
                # Особая обработка для адреса доставки
                await callback_query.message.edit_text(
                    "🚚 <b>Доставка</b>\n\n"
                    "В этом разделе вы можете узнать информацию о доставке ваших заказов.",
                    reply_markup=get_delivery_menu(),
                    parse_mode='HTML'
                )
            else:
                # По умолчанию возвращаемся в главное меню
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
        # print(f"Critical error in process_fallback for user {callback_query.from_user.id}: {e}")
        # В случае критической ошибки пытаемся вернуться в главное меню
        try:
            await callback_query.message.edit_text(
                "Произошла ошибка при навигации. Выберите действие:\n"
                "• 👤 Мой кабинет - профиль, заказы, настройки\n"
                "• 🛍️ Оформить заказ - добавить новый товар\n"
                "• 🚚 Доставка - информация о доставке\n"
                "• 🛒 Моя корзина - управление товарами",
                reply_markup=get_main_menu()
            )
        except:
            # Игнорируем вторичные ошибки
            pass

def register_fallback_handlers(dp):
    """
    Регистрирует обработчики для системы fallback.
    
    Args:
        dp: Диспетчер бота
    """
    # Обработчик для кнопки "Назад"
    dp.register_callback_query_handler(
        process_fallback,
        lambda c: c.data == "back",
        state="*"
    ) 

def reset_navigation_history(user_id: int):
    """
    Полностью сбрасывает историю навигации пользователя.
    
    Args:
        user_id: ID пользователя
    """
    if user_id in user_navigation_history:
        # print(f"Resetting navigation history for user {user_id}")
        user_navigation_history[user_id] = []
        return True
    return False

# Обновляем список экспортируемых функций
__all__ = [
    'save_navigation_state',
    'get_previous_screen',
    'process_fallback',
    'register_fallback_handlers',
    'reset_navigation_history'
] 