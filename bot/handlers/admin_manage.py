from aiogram import Router, F, types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from bot.database.db import SessionLocal
from bot.database.models import Admin, Referral
from bot.admin_panel.admin_utils import list_admins, remove_admin
from bot.states.admin_states import AdminStates

router = Router()


# Список админов для просмотра их вебмастеров
@router.callback_query(F.data == "admin_list")
async def show_admin_list(callback: CallbackQuery):
    admins = await list_admins()

    if not admins:
        await callback.message.answer("❗️ Список админов пуст.")
        return await callback.answer()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"@{admin.username}" if admin.username else f"ID {admin.telegram_id}",
                              callback_data=f"admin_wm_list:{admin.telegram_id}")]
        for admin in admins
    ])

    await callback.message.answer("Выберите администратора для просмотра его вебмастеров:", reply_markup=kb)
    await callback.answer()


# Вебмастера выбранного админа
@router.callback_query(F.data.startswith("admin_wm_list:"))
async def show_admin_webmasters(callback: CallbackQuery):
    admin_id = int(callback.data.split(":")[1])

    async with SessionLocal() as session:
        result = await session.execute(
            select(Referral)
            .filter_by(admin_id=admin_id)
            .options(selectinload(Referral.links))
        )
        referrals = result.scalars().all()

    if not referrals:
        await callback.message.answer("📭 У этого администратора нет вебмастеров.")
        return await callback.answer()

    text_blocks = []
    for ref in referrals:
        main_link = next((l for l in ref.links if l.is_main), None)
        other_links = [l for l in ref.links if not l.is_main]

        block = f"🔹 Вебмастер <b>{ref.tag}</b>\n"
        if main_link:
            block += f"⭐ Основная: <code>{main_link.link}</code>\n"
        if other_links:
            block += "📎 Доп. ссылки:\n" + "\n".join(
                [f"🔸 <code>{l.link}</code>" for l in other_links]
            )
        block += "\n<code>────────────</code>"
        text_blocks.append(block)

    await callback.message.answer("\n\n".join(text_blocks), parse_mode="HTML")
    await callback.answer()


# Удаление администратора (выбор)
@router.callback_query(F.data == "admin_remove")
async def choose_admin_to_remove(callback: CallbackQuery, state: FSMContext):
    admins = await list_admins()

    if not admins:
        await callback.message.answer("⚠️ Администраторов нет.")
        return await callback.answer()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Удалить: {admin.telegram_id} - @{admin.username}", callback_data=f"remove_admin:{admin.telegram_id}")]
        for admin in admins
    ])

    await callback.message.answer("Выберите администратора для удаления:", reply_markup=kb)
    await callback.answer()


# Подтверждение удаления
@router.callback_query(F.data.startswith("remove_admin:"))
async def confirm_admin_removal(callback: CallbackQuery, state: FSMContext):
    admin_id = int(callback.data.split(":")[1])
    await state.update_data(removing_admin_id=admin_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm_admin_removal")],
        [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_admin_removal")]
    ])

    await callback.message.answer(f"Вы уверены, что хотите удалить администратора с ID {admin_id}?", reply_markup=kb)
    await callback.answer()


# Удаление подтверждено
@router.callback_query(F.data == "confirm_admin_removal")
async def remove_admin_confirmed(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    admin_id = data.get("removing_admin_id")

    try:
        await remove_admin(admin_id)
        await callback.message.answer(f"✅ Администратор с ID {admin_id} успешно удалён.")
    except Exception as e:
        await callback.message.answer(f"❌ Не удалось удалить администратора: {str(e)}")

    await state.clear()
    await callback.answer()


# Отмена удаления
@router.callback_query(F.data == "cancel_admin_removal")
async def cancel_admin_removal(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("❌ Удаление администратора отменено.")
    await state.clear()
    await callback.answer()
