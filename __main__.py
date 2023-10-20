from aiogram import Dispatcher

# from bot.commands import set_default_commands
from bot_settings import dp
from loguru import logger
from handlers.other import other_router
from handlers.admin import router
from handlers.group import groupRouter
from asyncio import run
from bot_settings import bot


async def startup(dp: Dispatcher) -> None:
    """initialization"""
    # await db.create_tables()
    # await set_default_commands(dp)
    logger.add("bot started")


async def shutdown(dp: Dispatcher) -> None:
    """and need to close Redis and PostgreSQL connection when shutdown"""
    # await db.close_database()
    await dp.storage.close()
    logger.add("bot finished")


async def init() -> None:
    dp.include_routers(groupRouter, other_router, router)

    await dp.start_polling(
        bot, skip_updates=True, on_startup=startup, on_shutdown=shutdown
    )


if __name__ == "__main__":
    logger.add(
        "logs/debug.log",
        level="DEBUG",
        format="{time} | {level} | {module}:{function}:{line} | {message}",
        rotation="30 KB",
        compression="zip",
    )
    run(init())
