from aiogram import types, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from aiogram.filters import Command
from sqlalchemy.future import select
import logging
import re

from bot.database.db import SessionLocal
from bot.database.models import Referral, ReferralInvite
from bot.states.admin_states import AdminStates

router = Router()

# Старт добавления вебмастера
@router.callback_query(lambda c: c.data == "add_webmaster")
async def add_webmaster_start(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Введите тег вебмастера (буквы и/или цифры):")
    await state.set_state(AdminStates.awaiting_webmaster_id)
    await callback.answer()

# Обработка тега вебмастера
@router.message(AdminStates.awaiting_webmaster_id)
async def process_webmaster_id(message: types.Message, state: FSMContext):
    tag = message.text.strip()

    if not tag.isalnum():
        await message.answer("❌ Тег должен содержать только буквы и/или цифры. Введите ещё раз:")
        return

    await state.update_data(webmaster_tag=tag)
    await message.answer("Теперь введите первую ссылку на казино для этого вебмастера:")
    await state.set_state(AdminStates.awaiting_webmaster_link)

# Обработка ссылки и создание вебмастера + первой связки
@router.message(AdminStates.awaiting_webmaster_link)
async def process_webmaster_link(message: types.Message, state: FSMContext):
    casino_link = message.text.strip()
    data = await state.get_data()
    tag = data.get("webmaster_tag")
    admin_id = message.from_user.id

    logging.info(f"[ADMIN PANEL] Добавление вебмастера {tag} с первой ссылкой {casino_link}")

    async with SessionLocal() as session:
        # Проверка на уникальность тега
        existing = await session.scalar(select(Referral).filter_by(tag=tag))
        if existing:
            await message.answer("❗️ Вебмастер с таким тегом уже существует.")
            await state.clear()
            return

        # Создание вебмастера
        referral = Referral(tag=tag, admin_id=admin_id)
        session.add(referral)
        await session.flush()

        # Создание первой связки bot + казино
        first_bot_tag = f"{tag}_01"
        first_invite = ReferralInvite(
            referral_id=referral.id,
            bot_tag=first_bot_tag,
            casino_link=casino_link,
            is_main=True
        )
        session.add(first_invite)
        await session.commit()

    # Формируем красивый вывод
    bot_username = (await message.bot.get_me()).username
    await message.answer(
        f"✅ Вебмастер <code>{tag}</code> успешно добавлен с первой связкой:\n\n"
        f"<code>{first_bot_tag}</code>\n"
        f"<a href=\"https://t.me/{bot_username}?start={first_bot_tag}\">https://t.me/{bot_username}?start={first_bot_tag}</a>\n"
        f"<a href=\"{casino_link}\">{casino_link}</a>",
        parse_mode="HTML", disable_web_page_preview=True
    )

    # Кнопка возврата
    back_kb = types.InlineKeyboardMarkup(inline_keyboard=[
    [types.InlineKeyboardButton(text=f"📂 Открыть карточку {tag}", callback_data=f"wm_links:{referral.id}")],
    [types.InlineKeyboardButton(text="⬅️ Назад к вебмастерам", callback_data="webmaster_links")]
])

    await message.answer("📋 Выберите дальнейшее действие:", reply_markup=back_kb)

    await state.clear()
