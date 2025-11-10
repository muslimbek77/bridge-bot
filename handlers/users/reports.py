from aiogram import types, F
from aiogram.fsm.context import FSMContext
from loader import dp, db
from states.admin import ReportPDFForm
from keyboard_buttons.admin_keyboard import squad_keyboard, report_type_keyboard
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import os

# === Boshlang‘ich hisobot tugmasi ===
@dp.message(F.text == "📊 Hisobot")
async def get_report_start(message: types.Message, state: FSMContext):
    squads_data = db.execute("SELECT DISTINCT squad FROM REPORTS", fetchall=True)
    squads = list({s[0].strip() for s in squads_data if s[0]})  # strip() bilan bo‘sh joylarni olib tashlaymiz
    squads.sort() 
    await message.answer("Qaysi otryad uchun hisobot kerak?", reply_markup=squad_keyboard(squads))
    await state.set_state(ReportPDFForm.choose_squad)

# === Otryad tanlash ===
@dp.callback_query(F.data.startswith("squad_"), ReportPDFForm.choose_squad)
async def choose_squad(call: types.CallbackQuery, state: FSMContext):
    squad = call.data.replace("squad_", "")
    await state.update_data(squad=squad)
    await call.message.edit_text(f"📂 <b>{squad}</b> uchun hisobot turi:", parse_mode="HTML", reply_markup=report_type_keyboard())
    await state.set_state(ReportPDFForm.choose_type)

# === Hisobot turi tanlash ===
@dp.callback_query(F.data.in_(["type_month", "type_day"]), ReportPDFForm.choose_type)
async def choose_type(call: types.CallbackQuery, state: FSMContext):
    report_type = "oy" if call.data == "type_month" else "kun"
    await state.update_data(report_type=report_type)
    if report_type == "oy":
        await call.message.edit_text("📆 Oyni kiriting (masalan: 2025-10):")
    else:
        await call.message.edit_text("🗓 Sanani kiriting (masalan: 2025-10-05):")
    await state.set_state(ReportPDFForm.enter_date)

# === Sana kiritilganda PDF yaratish ===
@dp.message(ReportPDFForm.enter_date)
async def create_pdf_report(message: types.Message, state: FSMContext):
    data = await state.get_data()
    squad = data.get("squad")
    report_type = data.get("report_type")
    date_str = message.text.strip()

    # Filter sharti
    query = "SELECT full_name, direction, created_at, report_url FROM REPORTS WHERE squad = ? AND created_at LIKE ?"
    params = (squad, f"{date_str}%")
    reports = db.execute(query, parameters=params, fetchall=True)

    if not reports:
        await message.answer("❌ Bu sana uchun hech qanday ma’lumot topilmadi.")
        await state.clear()
        return

    # === PDF generatsiya ===
    pdf_name = f"arxiv_{squad.replace(' ', '_')}_{date_str}.pdf"
    pdf_path = f"/tmp/{pdf_name}"

    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title = Paragraph(f"■ {squad.upper()} — Arxiv ({date_str})", styles["Title"])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Link style
    link_style = ParagraphStyle(name="link_style", textColor=colors.blue, underline=True)

    # Table data
    table_data = [["№", "F.I.Sh", "Yo‘nalish", "Vaqt", "Telegram havola"]]
    for i, row in enumerate(reports, 1):
        full_name, direction, created_at, report_url = row
        if report_url:
            link_paragraph = Paragraph(f'<a href="{report_url}">{report_url}</a>', link_style)
        else:
            link_paragraph = Paragraph("—", styles["Normal"])
        table_data.append([str(i), full_name, direction, created_at, link_paragraph])

    table = Table(table_data, colWidths=[25, 120, 100, 100, 220])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ]))

    elements.append(table)
    doc.build(elements)

    # Foydalanuvchiga yuborish
    await message.answer_document(types.FSInputFile(pdf_path), caption=f"📄 {pdf_name}")
    os.remove(pdf_path)
    await state.clear()
