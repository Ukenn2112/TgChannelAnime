from requests import Session
from yt_dlp import YoutubeDL

from utils.global_vars import config, queue, sql

s = Session()
s.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Authorization": "bearer " + config["abema_barer"]
    })

ydl = YoutubeDL({
        'username': config['abema_username'],
        'password': config['abema_password'],
        'quiet': False,
        'no_warnings': True,
        'outtmpl': config['save_path'] + '%(series)s - S01E%(episode_number)02d - Abema/%(series)s - S01E%(episode_number)02d - Abema.%(ext)s',
        'allow_unplayable_formats': True,
        'fixup': 'never',
        'overwrites': True,
        'external_downloader': 'aria2c'
    })

async def abema_worker(sid: str, bgm_id, tmdb_d = None, eid = None):
    is_downs = sql.inquiry_abema(sid)
    season_data = s.get(f"https://api.p-c3-e.abema-tv.com/v1/video/series/{sid}")
    season_data.raise_for_status()
    season_data = season_data.json()
    info_data = s.get(
        f"https://api.p-c3-e.abema-tv.com/v1/video/series/{sid}/programs",
        params={
            "seriesVersion": season_data["version"],
            "seasonId": [i["id"] for i in season_data["seasons"] if i["name"] == "本編"][0],
            "offset": 0,
            "order": "seq",
            "limit": 25
        })
    info_data.raise_for_status()
    if eid:
        for i in info_data.json()["programs"]:
            if i["id"] == eid:
                return await queue.put((
                    "https://abema.tv/video/episode/" + i['id'], i['series']['title'], "mp4", 
                    i['episode']['number'], "Abema", bgm_id, tmdb_d
                    ))
    for i in info_data.json()["programs"]:
        if int(i["id"].split("_p")[-1]) >= 500:
            continue
        elif i["id"] not in is_downs:
            await queue.put((
                "https://abema.tv/video/episode/" + i['id'], i['series']['title'], "mp4", 
                i['episode']['number'], "Abema", bgm_id, tmdb_d
                ))


def abema_download(url: str, bgm_id):
    ydl.download(url)
    sql.insert_abema(url.split("/")[-1].split("_s")[0], url.split("/")[-1], bgm_id)
