from aiogram import types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import InputMediaPhoto
from datetime import datetime
from loader import dp, db

from keyboard_buttons.subscription import confirm_kb
from states.admin import ReportForm


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


# === Foydalanuvchi “Kirish / Chiqish” ni tanlaganda ===
@dp.message(F.text.in_(["🚗 Kirish", "🚪 Chiqish"]))
async def choose_direction(message: types.Message, state: FSMContext):
    direction = "Kirish" if message.text == "🚗 Kirish" else "Chiqish"
    await state.update_data(direction=direction)
    await state.set_state(ReportForm.direction)

    await message.answer(f"✅ Siz {direction} yo‘nalishini tanladingiz.\nEndi mashina rasmini yuboring:")


# === Yo‘nalishni tanlash ===
@dp.message(ReportForm.direction)
async def choose_direction(message: types.Message, state: FSMContext):
    direction = message.text.strip()
    if direction not in ["🚗 Kirish", "🚪 Chiqish"]:
        await message.answer("Iltimos, quyidagi tugmalardan birini tanlang.")
        return

    direction = "Kirish" if "Kirish" in direction else "Chiqish"
    await state.update_data(direction=direction)
    await message.answer("Endi mashina rasmini yuboring 📸")
    await state.set_state(ReportForm.car_image)


# === Mashina rasmi ===
@dp.message(ReportForm.car_image, F.photo)
async def get_car_image(message: types.Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    await state.update_data(car_img_url=file_id)
    await message.answer("Endi invoice (hisobot) rasmini yuboring 🧾")
    await state.set_state(ReportForm.invoice_image)


# === Invoice rasmi ===
@dp.message(ReportForm.invoice_image, F.photo)
async def get_invoice_image(message: types.Message, state: FSMContext):
    file_id = message.photo[-1].file_id
    await state.update_data(invoice_img_url=file_id)

    # Ma'lumotlarni olish
    data = await state.get_data()
    direction = data.get("direction", "—")
    telegram_id = message.from_user.id
    user = db.select_user(telegram_id=telegram_id)
    full_name = user[0] if user else "—"
    squad = user[2] if user and len(user) > 2 else ""

    # Rasmli MediaGroup tayyorlash
    media = [
        InputMediaPhoto(media=data["car_img_url"], caption=f"🚗 Mashina rasmi ({direction})"),
        InputMediaPhoto(media=data["invoice_img_url"], caption="🧾 Invoice rasmi"),
    ]

    # Rasm guruhini yuborish
    await message.answer_media_group(media)

    # Ma'lumotlarni qisqacha ko‘rsatish + tasdiqlash
    summary = (
        f"<b>Maʼlumotlar to‘g‘rimi?</b>\n\n"
        f"👤 <b>Foydalanuvchi:</b> {full_name}\n"
        f"👥 <b>Otryad:</b> {squad}\n"
        f"🧭 <b>Yo‘nalish:</b> {direction}\n\n"
        f"Agar hammasi to‘g‘ri bo‘lsa — <b>Yuborish</b> tugmasini bosing.\n"
        f"Agar noto‘g‘ri bo‘lsa — <b>O‘chirish</b> tugmasini bosing."
    )

    await message.answer(summary, reply_markup=confirm_kb(), parse_mode="HTML")
    await state.set_state(ReportForm.confirm)


# === Yuborish callback ===
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
    squad = user[2] if len(user) > 2 else ""
    direction = data.get("direction", "")
    car_img_url = data.get("car_img_url", "")
    invoice_img_url = data.get("invoice_img_url", "")
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        db.add_report(
            telegram_id=telegram_id,
            full_name=full_name,
            direction=direction,
            squad=squad,
            created_at=created_at,
            car_img_url=car_img_url,
            invoice_img_url=invoice_img_url
        )
    except Exception as err:
        await call.message.edit_text(f"❌ Xatolik: {err}")
        await state.clear()
        return

    await call.message.edit_text(
        f"✅ <b>{direction}</b> uchun report muvaffaqiyatli saqlandi!\n🕒 Sana: {created_at}",
        parse_mode="HTML"
    )
    await state.clear()


# === O‘chirish callback ===
@dp.callback_query(F.data == "report_delete", ReportForm.confirm)
async def callback_report_delete(call: types.CallbackQuery, state: FSMContext):
    await call.answer()
    await state.clear()
    await call.message.edit_text("❌ Report bekor qilindi. Qayta yuborishingiz mumkin.")
