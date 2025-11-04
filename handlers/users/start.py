from aiogram.types import Message
from loader import dp,db, ADMINS
from aiogram.filters import CommandStart,Command

@dp.message(CommandStart())
async def start_command(message:Message):

    await message.answer(text="Assalomu alaykum, botimizga hush kelibsiz")


