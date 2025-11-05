from loader import bot,db,dp,ADMINS
from aiogram.types import Message,ReplyKeyboardRemove,CallbackQuery, KeyboardButtonRequestUser
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from filters.admin import IsBotAdminFilter
from states.reklama import Adverts,ChannelState,DelChannelState
from states.admin import AddUser,UpdateUser,DeleteUser
from aiogram.fsm.context import FSMContext #new
from keyboard_buttons import admin_keyboard
import time 
from aiogram import F

@dp.message(Command("admin"),IsBotAdminFilter(ADMINS))
async def is_admin(message:Message):
    await message.answer(text="Admin menu",reply_markup=admin_keyboard.admin_button)

@dp.message(F.text == "Foydalanuvchilar soni", IsBotAdminFilter(ADMINS))
async def users_count(message: Message):
    counts = db.count_users()
    users = db.execute(
        "SELECT full_name, squad, telegram_id FROM users ORDER BY full_name ASC",
        fetchall=True
    )

    text = f"📊 <b>Botimizda {counts[0]} ta foydalanuvchi bor</b>\n\n"

    if users:
        for i, user in enumerate(users, start=1):
            full_name = user[0] or "—"
            squad = user[1] or "—"
            telegram_id = user[2]
            text += f"{i}. <b>{full_name}</b> — {squad}\n🆔 <code>{telegram_id}</code>\n\n"
    else:
        text += "❌ Hozircha foydalanuvchilar mavjud emas."

    for part in [text[i:i+4000] for i in range(0, len(text), 4000)]:
        await message.answer(part, parse_mode="HTML")


@dp.message(F.text=="Reklama yuborish",IsBotAdminFilter(ADMINS))
async def advert_dp(message:Message,state:FSMContext):
    await state.set_state(Adverts.adverts)
    await message.answer(text="Reklama yuborishingiz mumkin !")

@dp.message(Adverts.adverts)
async def send_advert(message:Message,state:FSMContext):
    
    message_id = message.message_id
    from_chat_id = message.from_user.id
    users = db.all_users_id()
    count = 0
    for user in users:
        try:
            await bot.copy_message(chat_id=user[0],from_chat_id=from_chat_id,message_id=message_id)
            count += 1
        except:
            pass
        time.sleep(0.01)
    
    await message.answer(f"Reklama {count}ta foydalanuvchiga yuborildi")
    await state.clear()



@dp.message(F.text=="⛓ Kanallar ro'yxati", IsBotAdminFilter(ADMINS))
async def send_ad_to_all(message: Message):
    channels = db.select_all_channels()
    text = "⛓ Kanallar ro'yxati:\n\n"
    tr = 1
    for chanel in channels:
        text += f"⛓ {tr} - {chanel[1]}\n⛓ Link: {chanel[2]}\n\n"
        tr += 1
    if text == "⛓ Kanallar ro'yxati:\n\n":
        await message.answer("Kanal yo'q")
    else:
        await message.answer(text)


@dp.message(F.text=="➕ Kanal qo'shish", IsBotAdminFilter(ADMINS))
async def send_ad_to_all(message: Message, state = FSMContext):
    await message.answer("Birinchi navbatda botni kanalga qo'shing.")
    await message.answer("Kanaldan biror postni forward qiling, \nyoki kanal id sini yuboring (-100....) \nyoki username sini yuboring ( misol uchun:  @mychannel )")
    await state.set_state(ChannelState.kanal_qoshish)
    
    
@dp.message(ChannelState.kanal_qoshish, IsBotAdminFilter(ADMINS))
async def send_ad_to_all(message: Message, state = FSMContext):
    try:
        if message.forward_from_chat:
            id = message.forward_from_chat.id
            name = message.forward_from_chat.title
            chat = await bot.get_chat(id)
            invite_link = await chat.export_invite_link()
        elif message.text:
            chanel = await bot.get_chat(message.text)
            id = chanel.id
            invite_link = await chanel.export_invite_link()
            name = chanel.full_name
        else:
            await message.answer("Nimadir xato ketti")
        
        await bot.get_chat_member(id, message.from_user.id)
        text = f"Name: {name}\n"
        text += f"Link: {invite_link}\n"
        text += f"\nQo'shildi ✅\n"
        db.add_chanel(id, name, invite_link)
        await message.answer(text,reply_markup=admin_keyboard.admin_button)
    except Exception as err:
        await message.answer(f"Oldin botni kanal yoki guruhga qo'shing, so'ngra qaytadan urinib ko'ring.\n\nYoki bot linki to'g'riligiga e'tibor bering: {err}",reply_markup=admin_keyboard.admin_button)
    await state.clear()
        
        
        
        
    
@dp.message(F.text=="➖ Kanal o'chirish", IsBotAdminFilter(ADMINS))
async def send_ad_to_all(message: Message, state = FSMContext):
    await message.answer("Majburiy a'zolik kanallari", reply_markup=ReplyKeyboardRemove())
    channels = db.select_all_channels()
    text = "Qaysi kanallarni majburiy a'zolikdan olib tashlamoqchisiz:\n\n"
    text += "⛓ Kanallar ro'yxati:\n\n"
    tr = 1
    # print(channels)
    for chanel in channels:
        text += f"⛓ {tr} - {chanel[1]}\n⛓ Link: {chanel[2]}\n\n"
        tr += 1
    await message.answer(text, reply_markup=admin_keyboard.inline_wars_btn(channels))
        
     
        
    await state.set_state(DelChannelState.delete_channel)
    
    
     
@dp.callback_query(F.data =="back_admin",DelChannelState.delete_channel)
async def change_(call: CallbackQuery, state=FSMContext):
    await call.message.delete()
    await state.clear()
    await call.message.answer("admin menu", reply_markup=admin_keyboard.admin_button)
        
     
@dp.callback_query(DelChannelState.delete_channel)
async def golibni_aniqlash_war(call: CallbackQuery, state=FSMContext):
    await call.message.delete()
    try:
        
            
        chanel = await bot.get_chat(call.data)
        # print(chanel)
        id = chanel.id
        db.delete_channel(id)
        invite_link = await chanel.export_invite_link()
        name = chanel.full_name
        

        text = f"Name: {name}\n"
        text += f"Link: {invite_link}\n"
        text += f"\nO'chirildi ✅ \n"
        
        await call.message.answer(text)   
        
    except Exception as err:
        await call.message.answer(f"Nimadur xato ketti : {err}")  
         
    await state.clear()
    await call.message.answer("Bosh menu", reply_markup=admin_keyboard.admin_button)


# Boshlash
@dp.message(F.text == "➕ Foydalanuvchi qo'shish", IsBotAdminFilter(ADMINS))
async def start_add_user(message: Message, state: FSMContext):
    # Tugma orqali foydalanuvchi tanlash
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(
                text="👤 Foydalanuvchini tanlash",
                request_user=KeyboardButtonRequestUser(
                    request_id=999,  # Request ID har doim unikal bo‘lsin
                    user_is_bot=False
                )
            )]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await state.set_state(AddUser.telegram_id)
    await message.answer("Foydalanuvchini tanlang yoki ID yuboring:", reply_markup=kb)

@dp.message(AddUser.telegram_id, F.user_shared)
async def process_user_selection(message: Message, state: FSMContext):
    telegram_id = message.user_shared.user_id
    await state.update_data(telegram_id=telegram_id)
    await state.set_state(AddUser.full_name)
    await message.answer("Endi foydalanuvchining to‘liq ismini kiriting:", reply_markup=ReplyKeyboardRemove())


@dp.message(AddUser.telegram_id, IsBotAdminFilter(ADMINS))
async def add_user_full_name(message: Message, state: FSMContext):
    try:
        telegram_id = int(message.text)
    except:
        await message.answer("Iltimos, to'g'ri Telegram ID kiriting (raqam bilan)")
        return
    await state.update_data(telegram_id=telegram_id)
    await state.set_state(AddUser.full_name)
    await message.answer("Foydalanuvchining to'liq ismini kiriting:")


@dp.message(AddUser.full_name, IsBotAdminFilter(ADMINS))
async def add_user_squad(message: Message, state: FSMContext):
    await state.update_data(full_name=message.text)

    # Bazadan unikal squadlarni olish
    squads_data = db.execute("SELECT DISTINCT squad FROM Users", fetchall=True)
    squads = set({s[0].strip() for s in squads_data if s[0]})
    kb = admin_keyboard.squad_selection_keyboard(squads)
    await state.set_state(AddUser.squad)
    await message.answer(
        "Otryad nomini tanlang yoki yangi otryad qo‘shing:",
        reply_markup=kb
    )


@dp.message(AddUser.squad, IsBotAdminFilter(ADMINS))
async def save_user_to_db(message: Message, state: FSMContext):
    data = await state.get_data()
    telegram_id = data["telegram_id"]
    full_name = data["full_name"]
    squad = message.text

    try:
        db.add_user(telegram_id=telegram_id, full_name=full_name,squad=squad)
        await message.answer(f"Foydalanuvchi {full_name} bazaga qo'shildi ✅")
    except Exception as err:
        await message.answer(f"Xatolik yuz berdi: {err}")

    await state.clear()



@dp.message(F.text == "🔄 Foydalanuvchini yangilash", IsBotAdminFilter(ADMINS))
async def start_update_user(message: Message, state: FSMContext):
    # Tugma orqali foydalanuvchi tanlash
    kb = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(
                text="👤 Foydalanuvchini tanlash",
                request_user=KeyboardButtonRequestUser(
                    request_id=777,
                    user_is_bot=False
                )
            )]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await state.set_state(UpdateUser.telegram_id)
    await message.answer("Yangilamoqchi bo‘lgan foydalanuvchini tanlang yoki Telegram ID yuboring:", reply_markup=kb)


# === Tugma orqali foydalanuvchi tanlandi ===
@dp.message(UpdateUser.telegram_id, F.user_shared)
async def process_update_user_selection(message: Message, state: FSMContext):
    telegram_id = message.user_shared.user_id
    user = db.select_user(telegram_id=telegram_id)
    if not user:
        await message.answer("❌ Bunday foydalanuvchi topilmadi.")
        await state.clear()
        return

    await state.update_data(telegram_id=telegram_id)
    await state.set_state(UpdateUser.choice)

    await message.answer(
        "Qaysi ma'lumotni yangilaysiz?\n\n1️⃣ Ism-familiya\n2️⃣ Otryad",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="1️⃣ Ism-familiya")],
                [KeyboardButton(text="2️⃣ Otryad")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )


# === ID orqali foydalanuvchi tanlandi ===
@dp.message(UpdateUser.telegram_id, IsBotAdminFilter(ADMINS))
async def update_user_by_id(message: Message, state: FSMContext):
    try:
        telegram_id = int(message.text)
    except ValueError:
        await message.answer("Iltimos, to‘g‘ri Telegram ID kiriting (faqat raqam).")
        return

    user = db.select_user(telegram_id=telegram_id)
    if not user:
        await message.answer("❌ Bunday foydalanuvchi topilmadi.")
        await state.clear()
        return

    await state.update_data(telegram_id=telegram_id)
    await state.set_state(UpdateUser.choice)

    await message.answer(
        f"Tanlangan foydalanuvchi: {user[1]} (ID: {telegram_id})\n\nQaysi maydonni yangilaysiz?",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="1️⃣ Ism-familiya")],
                [KeyboardButton(text="2️⃣ Otryad")]
            ],
            resize_keyboard=True,
            one_time_keyboard=True
        )
    )


# === Qaysi maydon yangilanadi ===
@dp.message(UpdateUser.choice, IsBotAdminFilter(ADMINS))
async def update_choice(message: Message, state: FSMContext):
    if "1" in message.text:
        await state.set_state(UpdateUser.full_name)
        await message.answer("Yangi ism-familiyasini kiriting:", reply_markup=ReplyKeyboardRemove())
    elif "2" in message.text:
        # mavjud squadlardan tanlash imkoniyati
        squads_data = db.execute("SELECT DISTINCT squad FROM Users", fetchall=True)
        squads = {s[0].strip() for s in squads_data if s[0]}
        kb = admin_keyboard.squad_selection_keyboard(squads)

        await state.set_state(UpdateUser.squad)
        await message.answer(
            "Yangi otryad nomini tanlang yoki kiriting:",
            reply_markup=kb
        )
    else:
        await message.answer("Iltimos, 1 yoki 2 ni tanlang.")


# === Yangi ism saqlash ===
@dp.message(UpdateUser.full_name, IsBotAdminFilter(ADMINS))
async def save_new_full_name(message: Message, state: FSMContext):
    data = await state.get_data()
    telegram_id = data["telegram_id"]
    db.update_user(telegram_id=telegram_id, full_name=message.text)
    await message.answer("✅ Ism-familiya yangilandi.", reply_markup=admin_keyboard.admin_button)
    await state.clear()


# === Yangi otryad saqlash ===
@dp.message(UpdateUser.squad, IsBotAdminFilter(ADMINS))
async def save_new_squad(message: Message, state: FSMContext):
    data = await state.get_data()
    telegram_id = data["telegram_id"]
    db.update_user(telegram_id=telegram_id, squad=message.text)
    await message.answer("✅ Otryad yangilandi.", reply_markup=admin_keyboard.admin_button)
    await state.clear()


@dp.message(F.text == "🗑 Foydalanuvchini o'chirish", IsBotAdminFilter(ADMINS))
async def start_delete_user(message: Message, state: FSMContext):
    users = db.execute("SELECT full_name, telegram_id FROM users", fetchall=True)
    if not users:
        await message.answer("❌ Bazada foydalanuvchilar topilmadi.")
        return

    # Har bir foydalanuvchi uchun tugma yaratamiz
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=f"{user[0]} ({user[1]})")] for user in users],
        resize_keyboard=True,
        one_time_keyboard=True
    )

    await state.set_state(DeleteUser.telegram_id)
    await message.answer("Kimni o‘chirmoqchisiz? Tanlang:", reply_markup=kb)


@dp.message(DeleteUser.telegram_id, IsBotAdminFilter(ADMINS))
async def delete_user_from_db(message: Message, state: FSMContext):
    text = message.text.strip()

    # Format: "Foydalanuvchi ism (123456789)"
    try:
        telegram_id = int(text.split("(")[-1].replace(")", ""))
    except:
        await message.answer("❌ Noto‘g‘ri format. Iltimos, tugmadan tanlang yoki ID kiriting.")
        return

    user = db.select_user(telegram_id=telegram_id)
    if not user:
        await message.answer("❌ Bunday foydalanuvchi topilmadi.")
    else:
        db.delete_user(telegram_id)
        await message.answer(f"✅ {user[1]} foydalanuvchisi muvaffaqiyatli o‘chirildi.", reply_markup=ReplyKeyboardRemove())

    await state.clear()