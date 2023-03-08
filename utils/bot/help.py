from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message


async def help_message(message: Message, bot: AsyncTeleBot):
    await bot.reply_to(message, (
        "命令列表:\n\n"
        "`/baha [add/del] [黑名单]` 添加或删除黑名单 多个以#隔开\n\n"
        "`/b_global [add/del] [白名单]` 添加或删除白名单 多个以#隔开\n\n"
        "`/bilibili [add/del] [白名单/BGM ID]` 添加需要 BGM ID 使用 如 `大雪海的卡納/366250` 删除只需要 TagName\n\n"
        "`/cr [add/del] [白名单]` 解释同上\n\n"
        "`/sentai [add/del] [白名单]` 解释同上\n\n"
        "`/abema [add/del] [Note/Abema SeasonId/BGM ID/week(1~7)/time(00:00~23:59)]` 添加需要 备注 和 Abema SeasonId 和 BGM ID 使用 如 `不当哥哥/19-149/378862` 删除只需要 SeasonId\n\n"
        "`/bgmcom [add/del] [白名单/BGM ID]` BGM ID 对照表\n\n"
        "`/admin [add/del] [白名单]` 解释同上\n\n"
        "`/now_white` 获取现在的白名单\n\n"
        "`/url <bgmid> <tv|movie/tmdbid(可选)> <url>` url Ani/Abema 的下载链接\n\n"
        "下载 NC-Raws 的视频直接转发频道消息即可\n\n"
        "`/re_nfo <bgmid> {<tmdbid> [tv/movie] (可选)}` 重新生成剧集 NFO 如果tmdb相关数据不填写则跳过 Season NFO 的生成\n\n"
        "`/re_nfo all` 重新生成所有剧集 NFO\n\n"
        "添加字幕，直接将 str 转发给机器人后按提示操作\n\n"
        "`/help 本帮助`\n\n"
        ), parse_mode="Markdown")
