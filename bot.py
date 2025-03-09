#    This file is part of the AutoAnime distribution.
#    Copyright (c) 2024 Kaif_00z
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
#    General Public License for more details.
#
# License can be found in < https://github.com/kaif-00z/AutoAnimeBot/blob/main/LICENSE > .

# If you are using this following code then don't forget to give proper
# credit to t.me/kAiF_00z (github.com/kaif-00z)

from traceback import format_exc
from telethon import Button, events

from core.bot import Bot
from core.executors import Executors
from database import DataBase
from functions.info import AnimeInfo
from functions.schedule import ScheduleTasks, Var
from functions.tools import Tools, asyncio
from functions.utils import AdminUtils
from libs.ariawarp import Torrent
from libs.logger import LOGS, Reporter
from libs.subsplease import SubsPlease

# Initialize bot and utilities
tools = Tools()
tools.init_dir()
bot = Bot()
dB = DataBase()
subsplease = SubsPlease(dB)
torrent = Torrent()
schedule = ScheduleTasks(bot)
admin = AdminUtils(dB, bot)

async def is_fsubbed(uid):
    if len(Var.FSUB_CHATS) == 0:
        return True
    for chat_id in Var.FSUB_CHATS:
        try:
            member = await bot.get_chat_member(chat_id=chat_id, user_id=uid)
        except UserNotParticipant:
            return False
        except Exception as err:
            await rep.report(format_exc(), "warning")
            continue
    return True

async def get_fsubs(uid, txtargs):
    txt = "⚠️ You must join our channel(s) to use this bot!\n"
    buttons = []
    for chat_id in Var.FSUB_CHATS:
        invite_link = await bot.export_chat_invite_link(chat_id)
        buttons.append([InlineKeyboardButton("Join Channel", url=invite_link)])
    buttons.append([InlineKeyboardButton("✅ I've Joined", callback_data=f'fsub_check_{uid}')])
    return txt, InlineKeyboardMarkup(buttons)

@bot.on(events.NewMessage(incoming=True, pattern="^/start ?(.*)", func=lambda e: e.is_private))
async def _start(event):
    xnx = await event.reply("`Please Wait...`")
    msg_id = event.pattern_match.group(1)
    await dB.add_broadcast_user(event.sender_id)

    is_user_joined = await is_fsubbed(event.sender_id)  # ✅ Fix: Properly checking user subscription
    if not is_user_joined:
        return await xnx.edit(
            f"**Please Join The Following Channel To Use This Bot 🫡**",
            buttons=[
                [
                    Button.url(
                        "♻️ REFRESH",
                        url=f"https://t.me/{((await bot.get_me()).username)}?start={msg_id}",
                    )
                ],
            ],
        )

    if msg_id:
        if msg_id.isdigit():
            msg = await bot.get_messages(Var.BACKUP_CHANNEL, ids=int(msg_id))
            await event.reply(msg)
        else:
            items = await dB.get_store_items(msg_id)
            if items:
                for id in items:
                    msg = await bot.get_messages(Var.CLOUD_CHANNEL, ids=id)
                    await event.reply(file=[i for i in msg])
    else:
        if event.sender_id == Var.OWNER:
            return await xnx.edit(
                "** <                ADMIN PANEL                 > **",
                buttons=admin.admin_panel(),
            )
        await event.reply(
            f"**Enjoy Ongoing Anime's Best Encode 24/7 🫡**",
            buttons=[
                [
                    Button.url("👨‍💻 DEV", url="t.me/kaif_00z"),
                    Button.url(
                        "💖 OPEN SOURCE",
                        url="https://github.com/kaif-00z/AutoAnimeBot/",
                    ),
                ]
            ],
        )
    await xnx.delete()

@bot.on(events.NewMessage(incoming=True, pattern="^/about", func=lambda e: e.is_private))
async def _(e):
    await admin._about(e)

@bot.on(events.callbackquery.CallbackQuery(data="slog"))
async def _(e):
    await admin._logs(e)

@bot.on(events.callbackquery.CallbackQuery(data="sret"))
async def _(e):
    await admin._restart(e, schedule)

@bot.on(events.callbackquery.CallbackQuery(data="entg"))
async def _(e):
    await admin._encode_t(e)

@bot.on(events.callbackquery.CallbackQuery(data="butg"))
async def _(e):
    await admin._btn_t(e)

@bot.on(events.callbackquery.CallbackQuery(data="scul"))
async def _(e):
    await admin._sep_c_t(e)

@bot.on(events.callbackquery.CallbackQuery(data="cast"))
async def _(e):
    await admin.broadcast_bt(e)

@bot.on(events.callbackquery.CallbackQuery(data="bek"))
async def _(e):
    await e.edit(buttons=admin.admin_panel())

async def anime(data):
    try:
        torr = [data.get("480p"), data.get("720p"), data.get("1080p")]
        anime_info = AnimeInfo(torr[0].title)
        poster = await tools._poster(bot, anime_info)
        if await dB.is_separate_channel_upload():
            chat_info = await tools.get_chat_info(bot, anime_info, dB)
            await poster.edit(
                buttons=[
                    [
                        Button.url(
                            f"EPISODE {anime_info.data.get('episode_number', '')}".strip(),
                            url=chat_info["invite_link"],
                        )
                    ]
                ]
            )
            poster = await tools._poster(bot, anime_info, chat_info["chat_id"])
        await torrent.download_magnet(torr[0].link, "./downloads/")
    except BaseException:
        LOGS.error(str(format_exc()))

try:
    bot.loop.run_until_complete(subsplease.on_new_anime(anime))
    bot.run()
except KeyboardInterrupt:
    subsplease._exit()
    
