from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# Главное меню админ-панели
admin_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🗃️ Список админов", callback_data="admin_list")],
        [InlineKeyboardButton(text="➕ Добавить админа", callback_data="admin_add")],
        [InlineKeyboardButton(text="🚫 Удалить админа", callback_data="admin_remove")],
        [InlineKeyboardButton(text="📋 Список пользователей", callback_data="user_list")],
        [InlineKeyboardButton(text="👷 Вебмастера", callback_data="webmaster_menu")],  # новая кнопка
    ]
)

# Подменю вебмастеров
webmaster_submenu = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="📋 Список вебмастеров", callback_data="webmaster_list")],
        [InlineKeyboardButton(text="➕ Добавить вебмастера", callback_data="add_webmaster")],
        [InlineKeyboardButton(text="✏️ Изменить ссылку", callback_data="edit_referral_link")],
        [InlineKeyboardButton(text="🔁 Переназначить", callback_data="reassign_webmaster")],
        [InlineKeyboardButton(text="🔗 Управление ссылками", callback_data="webmaster_links")],  # ← вот эта
        [InlineKeyboardButton(text="📈 Статистика", callback_data="webmaster_stats")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_back_to_main")],
    ]
)


# Клавиатура действий со ссылкой
def link_actions_keyboard(link_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔗 Перейти", url="placeholder"),  # будет заменено динамически
            ],
            [
                InlineKeyboardButton(text="✏️ Изменить", callback_data=f"edit_link:{link_id}"),
                InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_link:{link_id}"),
            ],
            [
                InlineKeyboardButton(text="⭐ Сделать основной", callback_data=f"make_main_link:{link_id}")
            ]
        ]
    )

# Кнопка добавить новую ссылку
add_new_link_button = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="➕ Добавить новую ссылку", callback_data="add_new_link")]
    ]
)
