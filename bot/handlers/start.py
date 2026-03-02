import asyncio
import logging

from aiogram import Bot, Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, WebAppInfo
from sqlalchemy.future import select

from bot.config import WEBAPP_BASE_URL, REGISTRATION_URL
from bot.database.db import SessionLocal
from bot.database.models import User, Referral, ReferralInvite, UserProgress
from bot.database.save_step import save_step

router = Router()
awaiting_ids = {}

# --- Клавиатуры ---

continue_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="▶️ Продолжить", callback_data="continue_flow")]
    ]
)

how_it_works_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Узнать, как это работает", callback_data="how_it_works")],
        [InlineKeyboardButton(text="🆘 Помощь", callback_data="help")]
    ]
)

instruction_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Получить инструкцию", callback_data="get_instruction")],
        [InlineKeyboardButton(text="🆘 Помощь", callback_data="help")]
    ]
)

reg_inline_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔗 ССЫЛКА ДЛЯ РЕГИСТРАЦИИ", callback_data="reg_link")],
        [InlineKeyboardButton(text="✅ Я ЗАРЕГИСТРИРОВАЛСЯ", callback_data="registered")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="back_to_start")],
        [InlineKeyboardButton(text="🆘 Помощь", callback_data="help")]
    ]
)

games_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="💎 MINES 💎", web_app=WebAppInfo(url=f"{WEBAPP_BASE_URL}/minesexplorer")),
            InlineKeyboardButton(text="⚽ GOAL ⚽", web_app=WebAppInfo(url=f"{WEBAPP_BASE_URL}/goalrush"))
        ],
        [
            InlineKeyboardButton(text="✈️ AVIATRIX ✈️", web_app=WebAppInfo(url=f"{WEBAPP_BASE_URL}/aviatrixflymod")),
            InlineKeyboardButton(text="🥅 PENALTY 🥅", web_app=WebAppInfo(url=f"{WEBAPP_BASE_URL}/penaltygame"))
        ],
        [InlineKeyboardButton(text="🆘 Помощь", callback_data="help")]
    ]
)


# --- Сообщение старта ---

async def send_start_text(bot: Bot, target, is_edit: bool = False):
    text = (
        "👋 Привет!\n\n"
        "Ты попал в бота, который используется для получения дохода на онлайн-играх с помощью автоматизированной аналитики.\n\n"
        "Система сделана так, чтобы даже новичок мог быстро разобраться и начать действовать без сложностей и опыта.\n\n"
        "💰 Пользователи, которые строго следуют инструкциям, зарабатывают 100–300$ уже с первого дня, работая с телефона и из дома.\n\n"
        "❗ Важно:\n"
        "❌ ничего ломать не нужно\n"
        "❌ специальных знаний не нужно\n"
        "❌ всё уже настроено за тебя\n\n"
        "Весь процесс расписан пошагово — 10–15 минут, и ты полностью понимаешь, что делать дальше.\n\n"
        "👇 Нажми кнопку ниже:"
    )
    if is_edit:
        await target.edit_text(text=text, reply_markup=how_it_works_keyboard)
    else:
        await bot.send_message(chat_id=target, text=text, reply_markup=how_it_works_keyboard)

    username = target.from_user.username or f"user_{target.from_user.id}"

    async with SessionLocal() as session:
        await save_step(target.from_user.id, "start", username)


async def send_access_granted_message(bot: Bot, message: Message, user_lang: str):
    # user_lang оставляем как параметр, чтобы не ломать остальную логику
    keyboard = games_keyboard
    text = (
        "✅ ДОСТУП ПРЕДОСТАВЛЕН ✅\n\n"
        "🔴 Инструкция:\n"
        "1️⃣ Выберите игру ниже\n"
        "2️⃣ Откройте её на сайте\n"
        "3️⃣ Получите сигнал и повторите его в игре ➕ 🐝"
    )
    await message.answer(text, reply_markup=keyboard)

    username = message.from_user.username or f"user_{message.from_user.id}"

    async with SessionLocal() as session:
        await save_step(message.from_user.id, "access_granted", username=username)


# --- Обработчик /start ---

@router.message(CommandStart())
async def start_handler(message: Message):
    try:
        await message.answer(
            "👋 Привет!\n\n"
            "Ты попал в бота, который используется для получения дохода на онлайн-играх с помощью автоматизированной аналитики.\n\n"
            "Система сделана так, чтобы даже новичок мог быстро разобраться и начать действовать без сложностей и опыта.\n\n"
            "💰 Пользователи, которые строго следуют инструкциям, зарабатывают 100–300$ уже с первого дня, работая с телефона и из дома.\n\n"
            "❗ Важно:\n"
            "❌ ничего ломать не нужно\n"
            "❌ специальных знаний не нужно\n"
            "❌ всё уже настроено за тебя\n\n"
            "Весь процесс расписан пошагово — 10–15 минут, и ты полностью понимаешь, что делать дальше.\n\n"
            "👇 Нажми кнопку ниже:",
            reply_markup=how_it_works_keyboard
        )

        parts = message.text.split(maxsplit=1)
        if len(parts) > 1:
            bot_tag = parts[1].strip()
            async with SessionLocal() as session:
                invite_result = await session.execute(
                    select(ReferralInvite).filter_by(bot_tag=bot_tag)
                )
                invite = invite_result.scalar_one_or_none()

                if invite:
                    await session.refresh(invite)
                    referral = await session.get(Referral, invite.referral_id)
                    if referral:
                        user_result = await session.execute(
                            select(User).filter_by(telegram_id=message.from_user.id)
                        )
                        user = user_result.scalar()

                        if not user:
                            user = User(
                                telegram_id=message.from_user.id,
                                username=message.from_user.username,
                                ref_tag=referral.tag,
                                bot_tag=bot_tag
                            )
                        else:
                            user.ref_tag = referral.tag
                            user.bot_tag = bot_tag

                        session.add(user)
                        await session.commit()

                        logging.info(
                            f"👤 Новый пользователь {message.from_user.id} пришёл по ссылке: /start={bot_tag}. "
                            f"Казино: {invite.casino_link}"
                        )
                    else:
                        logging.warning(f"⚠️ Invite найден, но Referral не найден")
                else:
                    logging.warning(
                        f"⚠️ Пользователь {message.from_user.id} пришёл с несуществующим bot_tag: {bot_tag}")
        username = message.from_user.username or f"user_{message.from_user.id}"

        async with SessionLocal() as session:
            await save_step(message.from_user.id, "start", username)

    except Exception as e:
        logging.error(f"❌ Ошибка в /start: {str(e)}")
        await message.answer("Произошла ошибка при старте.")


# --- Дальше по инструкции ---

@router.callback_query(F.data == "back_to_start")
async def back_to_start(callback: CallbackQuery):
    await callback.answer()
    await send_start_text(bot=callback.bot, target=callback.message, is_edit=True)


@router.callback_query(F.data == "how_it_works")
async def how_it_works(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text(
        "Основa системы — Telegram-бот с аналитическим модулем, который работает со статистикой мини-игр и повторяющимися сценариями.\n\n"
        "⚙️ Что именно он делает:\n"
        " • 📊 Анализирует серии выигрышей и проигрышей\n"
        " • 🔄 Определяет повторяющиеся паттерны\n"
        " • ✅ Показывает оптимальную последовательность действий\n\n"
        "<b>🛡 Ты не рискуешь наудачу и не принимаешь решение «на удачу».</b>\n\n"
        "Твоя задача проста: повторять готовую схему, которую даёт бот, уже на реальной платформе.\n\n"
        "👇 Нажми кнопку ниже:",
        reply_markup=instruction_keyboard,
        parse_mode="HTML"
    )
    username = callback.message.from_user.username or f"user_{callback.message.from_user.id}"

    async with SessionLocal() as session:
        await save_step(callback.from_user.id, "how_it_works", username)


@router.callback_query(F.data == "get_instruction")
async def get_instruction(callback: CallbackQuery):
    await callback.answer()

    await callback.message.answer(
        "1️⃣ Зарегистрируй аккаунт на платформе, к которой подключён бот (ссылка ниже).\n"
        "2️⃣ После регистрации скопируй ID своего аккаунта.\n"
        "3️⃣ Отправь ID сюда в бот.\n\n"
        "💡 Для чего это нужно? Это необходимо, чтобы система синхронизировалась именно с твоим профилем.\n"
        "⚠️ Без ID бот не сможет активировать аналитику.\n"
        "🎥 Ниже я добавил короткую видео-инструкцию, чтобы тебе было проще."
    )

    video_file_id = "BAACAgIAAxkBAAIW1mmZ70Pxs33ok-Hb7ottbnU1E_W-AAKqkAACV27RSHAEwXqQ2LrLOgQ"
    await callback.message.answer_video(video=video_file_id)

    await asyncio.sleep(15)

    await callback.message.answer(
        "💸 Твой первый доход уже совсем близко! Всего один шаг отделяет тебя от старта. "
        "Регистрируйся сейчас, чтобы заработать свои первые деньги уже сегодня.",
        reply_markup=reg_inline_keyboard
    )
    username = callback.message.from_user.username or f"user_{callback.message.from_user.id}"

    async with SessionLocal() as session:
        await save_step(callback.from_user.id, "instruction", username)

# --- Регистрация пользователя через кнопку ---

@router.callback_query(F.data == "reg_link")
async def send_registration_link(callback: CallbackQuery):
    await callback.answer()

    async with SessionLocal() as session:
        user_result = await session.execute(
            select(User).filter_by(telegram_id=callback.from_user.id)
        )
        user = user_result.scalar()

        referral_link = REGISTRATION_URL  # fallback
        if user and user.bot_tag:
            invite_result = await session.execute(
                select(ReferralInvite).filter_by(bot_tag=user.bot_tag)
            )
            invite = invite_result.scalar_one_or_none()
            if invite:
                referral_link = invite.casino_link
        logging.info(f"Generated registration link for user {callback.from_user.id}: {referral_link}")
        await callback.message.answer(f"Ось посилання для реєстрації: {referral_link}")
    username = callback.message.from_user.username or f"user_{callback.message.from_user.id}"

    async with SessionLocal() as session:
        await save_step(callback.from_user.id, "reg_link", username)


@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("Напишите поддержке:\n@supp_winbot")


@router.callback_query(F.data == "registered")
async def registered(callback: CallbackQuery):
    await callback.answer()
    awaiting_ids[callback.from_user.id] = True
    await callback.message.answer("🔢 Укажи ID своего нового аккаунта (только цифры)")


@router.callback_query(F.data == "continue_flow")
async def continue_flow(callback: CallbackQuery):
    await callback.answer()

    async with SessionLocal() as session:
        result = await session.execute(
            select(UserProgress).filter_by(telegram_id=callback.from_user.id, bot_name="hackbotruc")
        )
        progress = result.scalar()

    if not progress:
        await send_start_text(callback.bot, callback.message, is_edit=True)
        return

    step = progress.last_step

    if step == "start":
        await send_start_text(callback.bot, callback.message, is_edit=True)

    elif step == "how_it_works":
        await how_it_works(callback)

    elif step == "instruction":
        await get_instruction(callback)

    elif step in ["entered_id", "access_granted"]:
        await send_access_granted_message(callback.bot, callback.message, "uk")

    else:
        await send_start_text(callback.bot, callback.message, is_edit=True)


# --- Проверка ID пользователя ---

@router.message()
async def process_user_message(message: Message):
    if message.video:
        logging.info(f"Received video from user {message.from_user.id}: {message.video.file_id}")
        return
    if message.text.startswith("/"):
        print(f"❓ Ненадіслана команда: {message.text}")
        await message.answer("❗ Невідома команда.")
        return

    if message.from_user.id not in awaiting_ids:
        return

    if not message.text.isdigit():
        await message.answer("❌ Введи только цифры.")
        return
    username = message.from_user.username or f"user_{message.from_user.id}"

    async with SessionLocal() as session:
        await save_step(message.from_user.id, "entered_id", username)

    await message.answer("🔍 Проверяю ID в базе...")
    await send_access_granted_message(message.bot, message, "uk")
    awaiting_ids.pop(message.from_user.id, None)


# --- Неизвестные колбэки ---

@router.callback_query()
async def catch_unhandled_callbacks(callback: CallbackQuery):
    known_callbacks = [
        "help", "how_it_works", "get_instruction",
        "registered", "reg_link",
        "admin_stats", "admin_add", "admin_remove", "user_list",
        "admin_list", "add_ref_link", "remove_ref_link", "referral_stats"
    ]

    if callback.data not in known_callbacks:
        await callback.answer()
        async with SessionLocal() as session:
            user_result = await session.execute(select(User).filter_by(telegram_id=callback.from_user.id))
            user = user_result.scalar()

        text = "Вы нажали неизвестную кнопку!"
        await callback.message.answer(text)
