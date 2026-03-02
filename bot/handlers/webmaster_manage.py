from aiogram import Router, F, types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload

from bot.database.db import SessionLocal
from bot.database.models import Referral, Admin
from bot.states.admin_states import AdminStates
import logging

router = Router()


# 🗑 Удаление вебмастера (выбор)
@router.callback_query(F.data == "remove_webmaster")
async def choose_webmaster_to_remove(callback: CallbackQuery):
    logging.info("[ADMIN PANEL] Запрошено удаление вебмастера")

    async with SessionLocal() as session:
        result = await session.execute(select(Referral))
        referrals = result.scalars().all()

    if not referrals:
        await callback.message.answer("📭 Список вебмастеров пуст.")
        return await callback.answer()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Удалить: {ref.tag}", callback_data=f"remove_wm_confirm:{ref.id}")]
        for ref in referrals
    ])

    await callback.message.answer("Выберите вебмастера для полного удаления:", reply_markup=kb)
    await callback.answer()


# Подтверждение удаления
@router.callback_query(F.data.startswith("remove_wm_confirm:"))
async def confirm_webmaster_removal(callback: CallbackQuery):
    ref_id = int(callback.data.split(":")[1])

    logging.info(f"[ADMIN PANEL] Подтверждено удаление вебмастера ID {ref_id}")

    async with SessionLocal() as session:
        referral = await session.get(Referral, ref_id)

        if referral:
            tag = referral.tag
            await session.delete(referral)
            await session.commit()
            await callback.message.answer(f"✅ Вебмастер {tag} успешно удалён.", parse_mode="Markdown")
        else:
            await callback.message.answer("❌ Вебмастер не найден.")

    await callback.answer()


# Переназначение вебмастера на другого администратора
@router.callback_query(F.data == "reassign_webmaster")
async def choose_webmaster_to_reassign(callback: CallbackQuery, state: FSMContext):
    async with SessionLocal() as session:
        result = await session.execute(
            select(Referral).options(selectinload(Referral.links))
        )
        referrals = result.scalars().all()

    if not referrals:
        await callback.message.answer("⚠️ Список вебмастеров пуст.")
        return await callback.answer()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{ref.tag} ({ref.links[0].link[:25]}...)" if ref.links else f"{ref.tag} (без ссылок)",
            callback_data=f"reassign_ref:{ref.id}")]
        for ref in referrals
    ])

    await callback.message.answer("Выберите вебмастера для переназначения:", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("reassign_ref:"))
async def ask_for_new_admin(callback: CallbackQuery, state: FSMContext):
    referral_id = int(callback.data.split(":")[1])
    await state.update_data(referral_id_to_reassign=referral_id)
    await callback.message.answer("Введите ID нового администратора:")
    await state.set_state(AdminStates.awaiting_new_admin_id)
    await callback.answer()


@router.message(AdminStates.awaiting_new_admin_id)
async def process_admin_reassignment(message: types.Message, state: FSMContext):
    new_admin_id = message.text.strip()

    if not new_admin_id.isdigit():
        await message.answer("❌ ID должен быть числом.")
        return

    data = await state.get_data()
    referral_id = data.get("referral_id_to_reassign")

    async with SessionLocal() as session:
        referral = await session.get(Referral, referral_id)

        if not referral:
            await message.answer("❌ Вебмастер не найден.")
            return

        admin = await session.scalar(select(Admin).filter_by(telegram_id=int(new_admin_id)))
        if not admin:
            await message.answer("❌ Администратор не найден.")
            return

        referral.admin_id = int(new_admin_id)
        await session.commit()

    await message.answer(f"✅ Вебмастер {referral.tag} переназначен на админа с ID {new_admin_id}.", parse_mode="Markdown")
    await state.clear()


# Статистика вебмастеров
@router.callback_query(F.data == "webmaster_stats")
async def webmaster_stats(callback: CallbackQuery):
    logging.info("[ADMIN PANEL] Получение статистики вебмастеров")
    
    async with SessionLocal() as session:
        result = await session.execute(
            select(Referral).options(selectinload(Referral.links))
        )
        referrals = result.scalars().all()

    total_webmasters = len(referrals)
    total_links = sum(len(ref.links) for ref in referrals)

    await callback.message.answer(
        f"📈 <b>Статистика вебмастеров</b>\n\n"
        f"👷 Всего вебмастеров (тегов): <b>{total_webmasters}</b>\n"
        f"🔗 Всего ссылок (основных и дополнительных): <b>{total_links}</b>",
        parse_mode="HTML"
    )

    await callback.answer()
