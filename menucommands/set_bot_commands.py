from aiogram import Bot
from aiogram.methods.set_my_commands import BotCommand
from aiogram.types import BotCommandScopeAllPrivateChats


async def set_default_commands(bot: Bot):
    commands = [
        BotCommand(command="/start", description="Botni ishga tushirish"),
        BotCommand(command="/help", description="https://t.me/kuprikqurilish"),
        BotCommand(command="/about", description=""" "Ko'prikqurilish" AJ """),

    ]
    await bot.set_my_commands(commands=commands, scope=BotCommandScopeAllPrivateChats())