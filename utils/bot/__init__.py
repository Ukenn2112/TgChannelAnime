from telebot.async_telebot import AsyncTeleBot
from telebot.asyncio_filters import SimpleCustomFilter

from utils.global_vars import config

from .down import ani_down, nc_msg_down
from .help import help_message
from .list import add_white, now_white
from .renfo import re_subject_nfo
from .sub import file_sub, send_sub


def bot_register(bot: AsyncTeleBot):
    """Bot register function."""
    bot.add_custom_filter(Administrator())
    bot.register_message_handler(nc_msg_down, chat_types=["private"], content_types=['video'], pass_bot=True, is_admin=True)
    bot.register_message_handler(file_sub, chat_types=["private"], content_types=['document'], pass_bot=True, is_admin=True)
    bot.register_message_handler(send_sub, regexp=r"[0-9]+ [0-9]+", chat_types=["private"], content_types=['text'], pass_bot=True, is_admin=True)
    bot.register_message_handler(add_white, commands=["baha", "b_global", "bilibili", "cr", "sentai", "admin", "bgmcom"], chat_types=["private"], pass_bot=True, is_admin=True)
    bot.register_message_handler(now_white, commands=["now_white"], chat_types=["private"], pass_bot=True, is_admin=True)
    bot.register_message_handler(ani_down, commands=["url"], chat_types=["private"], pass_bot=True, is_admin=True)
    bot.register_message_handler(help_message, commands=["help"], chat_types=["private"], pass_bot=True, is_admin=True)
    bot.register_message_handler(re_subject_nfo, commands=["re_nfo"], chat_types=["private"], pass_bot=True, is_admin=True)

class Administrator(SimpleCustomFilter):
    """Administrator filter."""
    key='is_admin'
    @staticmethod
    async def check(message):
        if message.from_user.id in config["admin_list"]:
            return True
        else:
            return False