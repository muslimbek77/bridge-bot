from aiogram import types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import ReplyKeyboardBuilder,InlineKeyboardBuilder
from aiogram.types import InputMediaPhoto
from datetime import datetime
from loader import dp, db,bot
from data.config import CHANNEL_ID,CHANNEL_USERNAME

from keyboard_buttons.subscription import confirm_kb
from states.admin import ReportForm


# === /start komanda ===
@dp.message(CommandStart())
async def start_command(message: types.Message, state: FSMContext):
    telegram_id = message.from_user.id
    user = db.select_user(telegram_id=telegram_id)

    if not user:
        await message.answer("❌ Siz ro‘yxatdan o‘tmagansiz. Avval admin orqali qo‘shiling.")
        return

    builder = ReplyKeyboardBuilder()
    builder.button(text="🚗 Kirish")
    builder.button(text="🚪 Chiqish")
    builder.adjust(2)

    await message.answer(
        text=f"Assalomu alaykum, {user[0]}!\nIltimos, yo‘nalishni tanlang:",
        reply_markup=builder.as_markup(resize_keyboard=True)
    )


@dp.message(F.text.in_(["🚗 Kirish", "🚪 Chiqish"]))
async def handle_direction(message: types.Message, state: FSMContext):
    direction = "Kirish" if message.text == "🚗 Kirish" else "Chiqish"
    await state.update_data(direction=direction)

    telegram_id = message.from_user.id
    user = db.select_user(telegram_id=telegram_id)
    squad = user[2] if len(user) > 2 else ""
    await state.update_data(squad=squad)

    # === Agar squad matnida "13" bo‘lsa, ikkita tugma chiqadi ===
    if "13" in squad:
        builder = InlineKeyboardBuilder()
        builder.button(text="13-Otryad butlash", callback_data="squad_13_butlash")
        builder.button(text="13-Otryad", callback_data="squad_13")
        await message.answer(
            f"Siz {direction} yo‘nalishini tanladingiz.\nEndi otryad turini tanlang:",
            reply_markup=builder.as_markup()
        )
        await state.set_state(ReportForm.choose_squad)
        return

    # Aks holda, oddiy davom etadi
    await state.set_state(ReportForm.car_image)
    await message.answer(
        f"✅ Siz {direction} yo‘nalishini tanladingiz.\nEndi mashina rasmini yuboring 📸"
    )


# === 13-otryad uchun callback ===
@dp.callback_query(F.data.in_(["squad_13_butlash", "squad_13"]), ReportForm.choose_squad)
async def choose_squad_callback(call: types.CallbackQuery, state: FSMContext):
    chosen = "13-Otryad butlash" if call.data == "squad_13_butlash" else "13-Otryad"
    await state.update_data(squad=chosen)
    await state.set_state(ReportForm.car_image)

    await call.answer()
    await call.message.edit_text(
        f"✅ Siz {chosen} ni tanladingiz.\nEndi mashina rasmini yuboring 📸"
    )
# === Mashina rasmi ===
@dp.message(ReportForm.car_image, F.photo)
async def get_car_image(message: types.Message, state: FSMContext):
    if not message.photo:
        await message.answer("❌ Iltimos, faqat rasm yuboring.")
        return

    file_id = message.photo[-1].file_id
    await state.update_data(car_img_url=file_id)
    await state.set_state(ReportForm.invoice_image)

    await message.answer("Endi hisobot rasmini yuboring 🧾")


# === Invoice rasmi ===
@dp.message(ReportForm.invoice_image, F.photo)
async def get_invoice_image(message: types.Message, state: FSMContext):
    if not message.photo:
        await message.answer("❌ Iltimos, faqat rasm yuboring.")
        return

    file_id = message.photo[-1].file_id
    await state.update_data(invoice_img_url=file_id)

    # Ma'lumotlarni olish
    data = await state.get_data()
    direction = data.get("direction", "—")
    telegram_id = message.from_user.id
    user = db.select_user(telegram_id=telegram_id)
    full_name = user[0] if user else "—"
    squad = data.get("squad", "—")

    # Rasmli MediaGroup tayyorlash
    media = [
        InputMediaPhoto(media=data["car_img_url"], caption=f"🚗 Mashina rasmi ({direction})"),
        InputMediaPhoto(media=data["invoice_img_url"], caption="🧾 Invoice rasmi"),
    ]
    await message.answer_media_group(media)

    # Ma'lumotlarni qisqacha ko‘rsatish + tasdiqlash
    summary = (
        f"<b>Maʼlumotlar to‘g‘rimi?</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {full_name}\n"
        f"👥 <b>Otryad:</b> {squad}\n"
        f"🧭 <b>Yo‘nalish:</b> {direction}\n\n"
        f"Agar hammasi to‘g‘ri bo‘lsa — <b>Yuborish</b> tugmasini bosing.\n"
        f"Agar noto‘g‘ri bo‘lsa — <b>Bekor qilish</b> tugmasini bosing."
    )
    await message.answer(summary, reply_markup=confirm_kb(), parse_mode="HTML")
    await state.set_state(ReportForm.confirm)


# Kanal ID (manfiy bo‘ladi, masalan -1002176402628)

@dp.callback_query(F.data == "report_send", ReportForm.confirm)
async def callback_report_send(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    data = await state.get_data()

    telegram_id = call.from_user.id
    user = db.select_user(telegram_id=telegram_id)
    if not user:
        await call.message.edit_text("❌ Foydalanuvchi topilmadi.")
        await state.clear()
        return

    full_name = user[0]
    squad = data.get("squad","-")
    direction = data.get("direction", "")
    car_img_url = data.get("car_img_url", "")
    invoice_img_url = data.get("invoice_img_url", "")
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    caption = (
        f"📋 <b>Yangi Hisobot</b>\n\n"
        f"👮 Navbatchi: <b>{full_name}</b>\n"
        f"🏷 Otryad: {squad}\n"
        f"📌 Yo‘nalish: <b>{direction}</b>\n"
        f"🕒 Sana: {created_at}"
    )

    msg_id = None
    report_url = None

    try:
        # === Kanalga yuborish ===
        if car_img_url and invoice_img_url:
            media = [
                InputMediaPhoto(media=car_img_url, caption=caption, parse_mode="HTML"),
                InputMediaPhoto(media=invoice_img_url)
            ]
            sent = await bot.send_media_group(chat_id=CHANNEL_ID, media=media)
            msg_id = sent[0].message_id  # birinchi post ID sini olamiz
        elif car_img_url:
            sent_msg = await bot.send_photo(chat_id=CHANNEL_ID, photo=car_img_url, caption=caption, parse_mode="HTML")
            msg_id = sent_msg.message_id
        elif invoice_img_url:
            sent_msg = await bot.send_photo(chat_id=CHANNEL_ID, photo=invoice_img_url, caption=caption, parse_mode="HTML")
            msg_id = sent_msg.message_id
        else:
            sent_msg = await bot.send_message(chat_id=CHANNEL_ID, text=caption, parse_mode="HTML")
            msg_id = sent_msg.message_id

        # === Xabar URL hosil qilish ===
        report_url = f"https://t.me/{CHANNEL_USERNAME}/{msg_id}"

    except Exception as e:
        await call.message.answer(f"⚠️ Kanalga yuborishda xatolik: {e}")
        report_url = None

    # === Ma'lumotni bazaga saqlash ===
    try:
        db.add_report(
            telegram_id=telegram_id,
            full_name=full_name,
            direction=direction,
            squad=squad,
            created_at=created_at,
            car_img_url=car_img_url,
            invoice_img_url=invoice_img_url,
            report_url=report_url
        )
    except Exception as err:
        await call.message.edit_text(f"❌ Xatolik: {err}")
        await state.clear()
        return

    # === Foydalanuvchiga javob ===
    text = (
        f"✅ <b>{direction}</b> uchun report muvaffaqiyatli saqlandi va kanalga yuborildi!\n"
        f"🕒 Sana: {created_at}\n"
        f"🔗 <a href='{report_url}'>Kanal xabari</a>"
    )

    await call.message.edit_text(text, parse_mode="HTML")
    await state.clear()


# === O‘chirish callback ===
@dp.callback_query(F.data == "report_delete", ReportForm.confirm)
async def callback_report_delete(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await state.clear()
    await call.message.edit_text("❌ Report bekor qilindi. Qayta yuborishingiz mumkin.")