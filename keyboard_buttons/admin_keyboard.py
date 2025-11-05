from aiogram.types import ReplyKeyboardMarkup, KeyboardButton,InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loader import dp, db, bot


admin_button = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="Foydalanuvchilar soni"),
            KeyboardButton(text="Reklama yuborish"),
        ],
         [
             KeyboardButton(text="➕ Foydalanuvchi qo'shish"),

            # KeyboardButton(text="⛓ Kanallar ro'yxati"), 
        ],
        [
            KeyboardButton(text="📊 Hisobot"),
        ],
        #  [
        #     KeyboardButton(text="➕ Kanal qo'shish"), 
        #     KeyboardButton(text="➖ Kanal o'chirish"), 
        # ],
        
    ],
   resize_keyboard=True,
   input_field_placeholder="Menudan birini tanlang"
)

def inline_wars_btn(wars):
    if len(wars)<=6:
        row = 3
    elif len(wars)<=8: 
        row = 4
    elif len(wars)<=12: 
        row = 6
    elif len(wars)<=16: 
        row = 8
    else:
        row = 10
    
    
    l = []
    tr = 1
    for war in wars:
        l.append(InlineKeyboardButton(text=f"{tr}", callback_data=f"{war[0]}"))
        tr += 1
    l.append(InlineKeyboardButton(text=f"Asosiy menuga qaytish", callback_data=f"back_admin"))
    wars_check = InlineKeyboardMarkup(inline_keyboard=[l])
    
    return wars_check




def squad_keyboard(squads):
    builder = InlineKeyboardBuilder()
    for squad in squads:
        builder.button(text=squad, callback_data=f"squad_{squad}")
    builder.adjust(2)
    return builder.as_markup()

def report_type_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="📅 Oylik", callback_data="type_month")
    builder.button(text="🗓 Kunlik", callback_data="type_day")
    builder.adjust(2)
    return builder.as_markup()

def squad_selection_keyboard(existing_squads: list):
    """
    existing_squads: list of strings
    """
    buttons = [[KeyboardButton(text=squad)] for squad in existing_squads]
    kb = ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return kb