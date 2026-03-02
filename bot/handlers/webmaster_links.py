from aiogram import Router, F, types
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
import re

from bot.database.db import SessionLocal
from bot.database.models import Referral, ReferralLink, ReferralInvite
from bot.states.admin_states import AdminStates

router = Router()

def is_valid_http_url(url: str) -> bool:
    return re.match(r"^https?://", url.strip()) is not None


@router.callback_query(F.data == "webmaster_links")
async def choose_webmaster_for_links(callback: CallbackQuery):
    async with SessionLocal() as session:
        result = await session.execute(select(Referral))
        webmasters = result.scalars().all()

    if not webmasters:
        await callback.message.answer("📭 Список вебмастеров пуст.")
        return await callback.answer()

    # Кнопки с вебмастерами
    kb_rows = [
        [InlineKeyboardButton(text=f"{wm.tag}", callback_data=f"wm_links:{wm.id}")]
        for wm in webmasters
    ]

    # Добавляем кнопку назад
    kb_rows.append([InlineKeyboardButton(text="⬅️ Назад", callback_data="webmaster_menu")])

    kb = InlineKeyboardMarkup(inline_keyboard=kb_rows)

    await callback.message.edit_text("Выберите вебмастера для просмотра ссылок:", reply_markup=kb)
    await callback.answer()



@router.callback_query(F.data.startswith("wm_links:"))
async def show_links_for_webmaster(callback: CallbackQuery):
    wm_id = int(callback.data.split(":")[1])

    async with SessionLocal() as session:
        result = await session.execute(
            select(Referral).options(
                selectinload(Referral.admin),
                selectinload(Referral.invites)
            ).where(Referral.id == wm_id)
        )
        referral = result.scalar_one_or_none()

    if not referral:
        await callback.message.answer("❌ Вебмастер не найден.")
        return await callback.answer()

    bot_username = (await callback.bot.get_me()).username
    admin_username = (
        f"@{referral.admin.username}" if referral.admin and referral.admin.username
        else f"ID {referral.admin_id}"
    )
    created = referral.created_at.strftime("%d.%m.%Y") if referral.created_at else "—"

    # 🔹 Заголовок
    text = (
        f"<b>👤 Вебмастер: {referral.tag}</b>\n"
        f"📌 Добавил: {admin_username}\n"
        f"📅 Добавлен: {created}"
        f"\n🧩 Связок (бот+казино): <b>{len(referral.invites)}</b>"
    )
    await callback.message.answer(text, parse_mode="HTML")

    # 🔗 Бот + казино
    if referral.invites:
        await callback.message.answer("🔗 <b>Ссылки на вход в бота + казино:</b>", parse_mode="HTML")
        for invite in referral.invites:
            invite_text = (
                f"<b>{invite.bot_tag}</b>\n"
                f"<code>https://t.me/{bot_username}?start={invite.bot_tag}</code>\n"
                f"<a href=\"{invite.casino_link}\">{invite.casino_link}</a>"
            )

            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="📋 Скопировать казино", callback_data=f"copy_casino:{invite.id}")],
                [
                    InlineKeyboardButton(text="✏️ Изменить ссылку", callback_data=f"edit_invite:{invite.id}"),
                    InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete_invite:{invite.id}")
                ]
            ])

            await callback.message.answer(invite_text, reply_markup=keyboard, parse_mode="HTML", disable_web_page_preview=True)
    else:
        await callback.message.answer("ℹ️ У вебмастера пока нет ссылок на бота + казино.")

    # 🔘 Действия внизу
    actions = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить бота+казино", callback_data=f"add_invite_to:{referral.id}")],
        [InlineKeyboardButton(text="🗑 Удалить вебмастера", callback_data=f"remove_wm_confirm:{referral.id}")],
        [InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="webmaster_links")]
    ])
    await callback.message.answer("📋 Выберите действие с этим вебмастером:", reply_markup=actions)
    await callback.answer()



@router.callback_query(F.data.startswith("copy_casino:"))
async def copy_casino_link(callback: CallbackQuery):
    invite_id = int(callback.data.split(":")[1])

    async with SessionLocal() as session:
        invite = await session.get(ReferralInvite, invite_id)

    if not invite:
        await callback.answer("❌ Ссылка не найдена", show_alert=True)
        return

    await callback.answer(
        f"Скопируйте ссылку:\n{invite.casino_link}",
        show_alert=True
    )

# ---------------------------
# Скрытые (неиспользуемые сейчас) хендлеры для ReferralLink
# ---------------------------

@router.callback_query(F.data.startswith("edit_link:"))
async def edit_link(callback: CallbackQuery, state: FSMContext):
    link_id = int(callback.data.split(":")[1])
    await state.update_data(editing_link_id=link_id)
    await callback.message.answer("✏️ Введите новую ссылку:")
    await state.set_state(AdminStates.awaiting_new_referral_link)
    await callback.answer()


@router.message(AdminStates.awaiting_new_referral_link)
async def process_link_edit(message: types.Message, state: FSMContext):
    data = await state.get_data()
    link_id = data.get("editing_link_id")
    new_url = message.text.strip()

    async with SessionLocal() as session:
        link = await session.get(ReferralLink, link_id)
        if link:
            link.link = new_url
            await session.commit()
            await message.answer("✅ Ссылка успешно обновлена.")
        else:
            await message.answer("❌ Ссылка не найдена.")
    await state.clear()


@router.callback_query(F.data.startswith("make_main_link:"))
async def make_main_link(callback: CallbackQuery):
    link_id = int(callback.data.split(":")[1])

    async with SessionLocal() as session:
        link = await session.get(ReferralLink, link_id)
        if not link:
            return await callback.message.answer("❌ Ссылка не найдена.")

        all_links = await session.execute(
            select(ReferralLink).where(ReferralLink.referral_id == link.referral_id)
        )
        for l in all_links.scalars():
            l.is_main = False

        link.is_main = True
        await session.commit()

    await callback.message.answer("⭐ Ссылка сделана основной.")
    await callback.answer()


@router.callback_query(F.data.startswith("delete_link:"))
async def delete_link(callback: CallbackQuery):
    link_id = int(callback.data.split(":")[1])

    async with SessionLocal() as session:
        link = await session.get(ReferralLink, link_id)
        if not link:
            return await callback.message.answer("❌ Ссылка не найдена.")

        await session.delete(link)
        await session.commit()

    await callback.message.answer("🗑 Ссылка удалена.")
    await callback.answer()
