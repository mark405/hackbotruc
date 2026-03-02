from aiogram import Router, types, F
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.future import select
from bot.database.db import SessionLocal
from bot.database.models import Referral, ReferralInvite
from bot.states.admin_states import AdminStates
import re

from bot.handlers.webmaster_links import show_links_for_webmaster

router = Router()

def is_valid_http_url(url: str) -> bool:
    return re.match(r"^https?://", url.strip()) is not None


@router.callback_query(F.data == "add_bot_casino")
async def start_add_bot_casino(callback: CallbackQuery, state: FSMContext):
    async with SessionLocal() as session:
        result = await session.execute(select(Referral))
        referrals = result.scalars().all()

    if not referrals:
        await callback.message.answer("📭 Список вебмастеров пуст.")
        return await callback.answer()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{r.tag}", callback_data=f"add_invite:{r.id}")]
        for r in referrals
    ])
    await callback.message.answer("Выберите вебмастера:", reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data.startswith("add_invite:"))
async def input_bot_tag(callback: CallbackQuery, state: FSMContext):
    referral_id = int(callback.data.split(":")[1])
    await state.update_data(referral_id=referral_id)
    await callback.message.answer("Введите тег, который будет использоваться в ссылке на бота (без /start=):")
    await state.set_state(AdminStates.awaiting_bot_tag)
    await callback.answer()


@router.message(AdminStates.awaiting_bot_tag)
async def input_casino_link(message: types.Message, state: FSMContext):
    bot_tag = message.text.strip()

    if not re.match(r"^[a-zA-Z0-9_]+$", bot_tag):
        await message.answer("❌ Недопустимый тег. Используйте только буквы, цифры и подчёркивание.")
        return

    async with SessionLocal() as session:
        existing = await session.execute(
            select(ReferralInvite).where(ReferralInvite.bot_tag == bot_tag)
        )
        if existing.scalar():
            await message.answer("⚠️ Такой тег уже используется. Введите другой тег:")
            return

    await state.update_data(bot_tag=bot_tag)
    await message.answer("Теперь отправьте ссылку на казино:")
    await state.set_state(AdminStates.awaiting_casino_link)


@router.message(AdminStates.awaiting_casino_link)
async def process_bot_casino_link(message: types.Message, state: FSMContext):
    data = await state.get_data()
    referral_id = data.get("referral_id")
    bot_tag = data.get("bot_tag")
    casino_link = message.text.strip()

    if not is_valid_http_url(casino_link):
        await message.answer("❌ Некорректная ссылка. Начинается с http:// или https://")
        return

    async with SessionLocal() as session:
        invite = ReferralInvite(
            referral_id=referral_id,
            bot_tag=bot_tag,
            casino_link=casino_link
        )
        session.add(invite)
        await session.commit()

    bot_username = (await message.bot.get_me()).username
    await message.answer(
        f"✅ Связка добавлена:\n\n"
        f"<code>/start={bot_tag}</code>\n"
        f"<a href=\"https://t.me/{bot_username}?start={bot_tag}\">https://t.me/{bot_username}?start={bot_tag}</a>\n"
        f"<a href=\"{casino_link}\">{casino_link}</a>",
        parse_mode="HTML", disable_web_page_preview=True
    )

    fake_callback = types.CallbackQuery(
        id="dummy",
        from_user=message.from_user,
        message=message,
        data=f"wm_links:{referral_id}"
    )
    await show_links_for_webmaster(fake_callback)
    await state.clear()


@router.callback_query(F.data.startswith("add_invite_to:"))
async def add_invite_to(callback: CallbackQuery, state: FSMContext):
    referral_id = int(callback.data.split(":")[1])
    async with SessionLocal() as session:
        referral = await session.get(Referral, referral_id)
        if not referral:
            await callback.message.answer("❌ Вебмастер не найден.")
            return await callback.answer()

        existing = await session.execute(
            select(ReferralInvite).where(ReferralInvite.referral_id == referral.id)
        )
        invites = existing.scalars().all()

        # Автонумерация
        number = len(invites) + 1
        bot_tag = f"{referral.tag}_{str(number).zfill(2)}"

    await state.update_data(referral_id=referral_id, bot_tag=bot_tag)
    await callback.message.answer(
        f"Введите ссылку на казино для связки:\n\n"
        f"<b>Тег будет:</b> <code>{bot_tag}</code>",
        parse_mode="HTML"
    )
    await state.set_state(AdminStates.awaiting_casino_link)
    await callback.answer()


@router.callback_query(F.data.startswith("edit_invite:"))
async def edit_invite(callback: CallbackQuery, state: FSMContext):
    invite_id = int(callback.data.split(":")[1])
    await state.update_data(editing_invite_id=invite_id)
    await callback.message.answer("✏️ Введите новую ссылку на казино:")
    await state.set_state(AdminStates.awaiting_edit_casino_link)
    await callback.answer()


@router.message(AdminStates.awaiting_edit_casino_link)
async def process_edit_invite_link(message: types.Message, state: FSMContext):
    new_link = message.text.strip()
    if not is_valid_http_url(new_link):
        await message.answer("❌ Некорректная ссылка. Начинается с http:// или https://")
        return

    data = await state.get_data()
    invite_id = data.get("editing_invite_id")

    async with SessionLocal() as session:
        invite = await session.get(ReferralInvite, invite_id)
        if not invite:
            await message.answer("❌ Связка не найдена.")
            return await state.clear()

        invite.casino_link = new_link
        await session.commit()

    await message.answer("✅ Ссылка на казино успешно обновлена.")
    await state.clear()


@router.callback_query(F.data.startswith("delete_invite:"))
async def delete_invite(callback: CallbackQuery):
    invite_id = int(callback.data.split(":")[1])

    async with SessionLocal() as session:
        invite = await session.get(ReferralInvite, invite_id)
        if not invite:
            return await callback.message.answer("❌ Связка не найдена.")

        await session.delete(invite)
        await session.commit()

    await callback.message.answer("🗑 Связка 'бот + казино' удалена.")
    await callback.answer()
