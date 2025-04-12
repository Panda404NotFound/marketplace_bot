import logging
import asyncio
from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import BotCommand

from config import BOT_TOKEN
from database import init_db
from handlers import register_all_handlers

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

async def main():
    """Основная функция."""
    # Инициализируем базу данных
    init_db()
    
    # Инициализируем бота и диспетчер
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(bot, storage=storage)
    
    # Устанавливаем команды для меню бота
    commands = [
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/help", description="Помощь по боту"),
        BotCommand(command="/instruction", description="Как покупать"),
        BotCommand(command="/reset", description="Сбросить состояние бота")
    ]
    await bot.set_my_commands(commands)
    
    # Регистрируем все обработчики
    register_all_handlers(dp)
    
    # Запускаем бота
    try:
        logger.info("Бот запущен")
        await dp.start_polling()
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        await bot.session.close()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Бот остановлен") 