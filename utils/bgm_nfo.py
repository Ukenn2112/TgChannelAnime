import logging

import cairosvg
import requests
import xmltodict

from utils.global_vars import config

s = requests.Session()
s.headers = {
    'User-Agent':'Ukenn/Bangumi2NFO',
    'Authorization': 'Bearer ' + config['bgm_token']
}

def subject_nfo(subject_id, tmdb_d: str = None) -> dict:
    """Bangumi Subject ID 生成 NFO 内容
    :param subject_id: Bangumi Subject ID
    :return: NFO 内容 \n`{"tvshowNfo": "tvshow nfo xml", "seasonNfo": "season nfo xml", "posterImg": ("poster image", "file_type"), "clearlogoImg": ("clearlogo image", "file_type"), "fanartImg": ("fanart image", "file_type")}`
    :rtype: `dict` \n`{"tvshowNfo": str, "seasonNfo": str , "posterImg": (bytes, str), "clearlogoImg": (bytes, str), "fanartImg": (bytes, str)}`
    """
    data = get_bgm_subject(subject_id)
    tvshow_json = {
        "tvshow": {
            "plot": data['summary'],
            "outline": data['summary'],
            "lockdata": False,
            "title": data['name_cn'] or data['name'],
            "originaltitle": data['name'],
            "director": [],
            "writer": [],
            "credits": [],
            "rating": data['rating']['score'],
            "year": data['date'][:4],
            "runtime": 24,
            "genre": [],
            "studio": [],
            "mpaa": [],
            "status": '',
            "premiered": data['date'],
            "releasedate": data['date'],
            "tag": [tag['name'] for tag in data['tags'][:9]],
            "bangumiid": data['id'],
            "thumb": [
                {
                    "@aspect": "poster",
                    "#text": data['images']['large'],
                },
                {
                    "@aspect": "poster",
                    "@season": 1,
                    "@type": "season",
                    "#text": data['images']['large'],
                }
            ],
            "fanart": {},
            "actor": [],
            "season": -1,
            "episode": -1,
        }
    }
    for person in data['persons']:
        if person['relation'] == "导演":
            tvshow_json['tvshow']['director'].append(person['name'])
        elif person['relation'] == "脚本":
            tvshow_json['tvshow']['writer'].append(person['name'])
            tvshow_json['tvshow']['credits'].append(person['name'])
        # elif person['relation'] == "制片人":
        #     z = {'name': person['name'], 'role': 'Producer', 'profile': 'https://bgm.tv/person/' + str(person['id'])}
        #     if person['images']['large']:
        #         z['thumb'] = person['images']['large']
        #     tvshow_json['tvshow']['actor'].append(z)
        # elif person['relation'] == "系列构成":
        #     x = {'name': person['name'], 'role': 'Composer', 'profile': 'https://bgm.tv/person/' + str(person['id'])}
        #     if person['images']['large']:
        #         x['thumb'] = person['images']['large']
        #     tvshow_json['tvshow']['actor'].append(x)
    for character in data['characters']:
        for actor in character['actors']:
            c = {
                    'name': actor['name'], 
                    'role': character['name'], 
                    'type': 'Actor', 
                    'profile': 'https://bgm.tv/person/' + str(actor['id'])
                }
            if actor['images']['large']:
                c['thumb'] = actor['images']['large']
            tvshow_json['tvshow']['actor'].append(c)
    clearlogo_img = None
    poster_img = (s.get(data['images']['large']).content, data['images']['large'].split('.')[-1])
    tmdb_data = None
    if tmdb_d:
        tmdb_d: list = tmdb_d.split('/')
        try:
            tmdb_data = get_tmdb_subject(tmdb_d[1], tmdb_d[0])
        except:
            logging.warning(f'获取 TMDB 数据失败，跳过 TMDB 数据获取 {tmdb_d[1]}/{tmdb_d[0]}')
    if tmdb_data:
        if tmdb_data['episode_run_time']:
            tvshow_json['tvshow']['runtime'] = tmdb_data['episode_run_time'][0]
        if tmdb_data['genres']:
            tvshow_json['tvshow']['genre'] = [g['name'] for g in tmdb_data['genres'][:3]]
        if tmdb_data['production_companies']:
            tvshow_json['tvshow']['studio'] = [s['name'] for s in tmdb_data['production_companies']]
        if tmdb_data['content_ratings']['results']:
            tvshow_json['tvshow']['mpaa'] = [r['rating'] for r in tmdb_data['content_ratings']['results'] if r['iso_3166_1'] == 'US'] or tmdb_data['content_ratings']['results'][0]['rating']
        tvshow_json['tvshow']['status'] = 'Continuing' if tmdb_data['status'] == 'Returning Series' else tmdb_data['status']

        tmdb_imgs = get_tmdb_images(tmdb_d[1], tmdb_d[0])
        if tmdb_imgs['backdrops']:
            tvshow_json['tvshow']['fanart']['thumb'] = ['https://image.tmdb.org/t/p/original' + img['file_path'] for img in tmdb_imgs['backdrops'] if not img['iso_639_1']]
            tvshow_json['tvshow']['thumb'].append({
                    "@aspect": "landscape",
                    "#text": 'https://image.tmdb.org/t/p/original/' + tmdb_imgs['backdrops'][0]['file_path'],
                })
            fanart_img = (requests.get('https://image.tmdb.org/t/p/original/' + tmdb_imgs['backdrops'][0]['file_path']).content, tmdb_imgs['backdrops'][0]['file_path'].split('.')[-1])
        if tmdb_imgs['logos']:
            _logo = False
            for logo in tmdb_imgs['logos']:
                if logo['iso_639_1'] == 'ja':
                    tvshow_json['tvshow']['thumb'].append({
                        "@aspect": "clearlogo",
                        "#text": 'https://image.tmdb.org/t/p/original' + logo['file_path'],
                    })
                    clearlogo_img = (requests.get('https://image.tmdb.org/t/p/original' + logo['file_path']).content, logo['file_path'].split('.')[-1])
                    _logo = True
                    break
            if not _logo:
                tvshow_json['tvshow']['thumb'].append({
                    "@aspect": "clearlogo",
                    "#text": 'https://image.tmdb.org/t/p/original' + tmdb_imgs['logos'][0]['file_path'],
                })
                clearlogo_img = (requests.get('https://image.tmdb.org/t/p/original' + tmdb_imgs['logos'][0]['file_path']).content, tmdb_imgs['logos'][0]['file_path'].split('.')[-1])
            if clearlogo_img[1] == 'svg':
                clearlogo_img = (cairosvg.svg2png(bytestring=clearlogo_img[0]), 'png')
    else:
         tvshow_json['tvshow']['fanart']['thumb'] = [data['images']['large']]
         fanart_img = poster_img
    tvshow_xml = '<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n'
    tvshow_xml += xmltodict.unparse(tvshow_json, encoding='UTF-8', pretty=True, indent="  ", full_document=False)
    season_json = {
        "season": {
            "plot": data['summary'],
            "outline": data['summary'],
            "lockdata": False,
            "title": data['name'],
            "art": {
                "poster": data['images']['large'],
            },
        }
    }
    season_xml = '<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n'
    season_xml += xmltodict.unparse(season_json, encoding='UTF-8', pretty=True, indent="  ", full_document=False)
    return {
        "tvshowNfo": tvshow_xml,
        "seasonNfo": season_xml,
        "posterImg": poster_img,
        "fanartImg": fanart_img,
        "clearlogoImg": clearlogo_img,
    }


def episode_nfo(subject_id, num, _type = 0) -> str:
    """Bangumi Episode ID 生成 NFO 内容
    :param subject_id: Bangumi Subject ID
    :param num: 第几集
    :param _type: 0 = 本篇 `默认`, 1 = 特别篇, 2 = OP, 3 = ED, 4 = 预告/宣传/广告, 5 = MAD, 6 = 其他
    :return: NFO 内容
    :rtype: `str`
    """
    data = get_bgm_episode(subject_id, num, _type)
    if not data: return ""
    if data['desc']:
        l = data['desc'].split('\r\n\r\n')
        if len(l) > 1 and '脚本' in l[1]:
            data['desc'] = l[0]
    episode_json = {
        "episodedetails": {
            "plot": data['desc'],
            "lockdata": False,
            "title": data['name_cn'] or data['name'],
            "originaltitle": data['name'],
            "year": data['airdate'][:4],
            "bangumiid": data['id'],
            "art": {
                "poster": data['poster'],
            },
            "showtitle": data['showtitle'],
            "episode": data['sort'],
            "season": 1,
            "aired": data['airdate'],
            "fileinfo":{
                "streamdetails": ""
            }
        }
    }
    episode_xml = '<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n'
    episode_xml += xmltodict.unparse(episode_json, encoding='UTF-8', pretty=True, indent="  ", full_document=False)
    return episode_xml


def get_bgm_subject(subject_id) -> dict:
    """请求 Bangumi API 获取番剧信息"""
    r = s.get(f'https://api.bgm.tv/v0/subjects/{subject_id}')
    r.raise_for_status()
    data = r.json()
    r = s.get(f'https://api.bgm.tv/v0/subjects/{subject_id}/persons')
    r.raise_for_status()
    data['persons'] = r.json()
    r = s.get(f'https://api.bgm.tv/v0/subjects/{subject_id}/characters')
    r.raise_for_status()
    data['characters'] = r.json()
    return data

def subject_name(subject_id) -> str:
    """请求 Bangumi API 获取番剧信息"""
    r = s.get(f'https://api.bgm.tv/v0/subjects/{subject_id}')
    r.raise_for_status()
    return r.json()['name']

def get_tmdb_subject(tmdb_id, _type = 'tv') -> dict:
    """请求 TMDB API 获取番剧信息"""
    r = requests.get(
        f'https://api.themoviedb.org/3/{_type}/{tmdb_id}',
        params = {'api_key': config['tmdb_token'], 'language': 'zh-CN'}
        )
    r.raise_for_status()
    data = r.json()
    r = requests.get(
        f'https://api.themoviedb.org/3/{_type}/{tmdb_id}/content_ratings',
        params = {'api_key': config['tmdb_token']}
        )
    r.raise_for_status()
    data['content_ratings'] = r.json()
    return data

def get_tmdb_images(tmdb_id, _type = 'tv') -> dict:
    """请求 TMDB API 获取剧集海报"""
    r = requests.get(
        f'https://api.themoviedb.org/3/{_type}/{tmdb_id}/images',
        params = {'api_key': config['tmdb_token']}
        )
    r.raise_for_status()
    return r.json()

def get_bgm_episode(subject_id, num, _type = 0) -> dict:
    """请求 Bangumi API 获取剧集信息
    :param subject_id: Bangumi Subject ID
    :param num: 第几集
    :param _type: 0 = 本篇 `默认`, 1 = 特别篇, 2 = OP, 3 = ED, 4 = 预告/宣传/广告, 5 = MAD, 6 = 其他
    :return: Bangumi Episode Data"""
    r = s.get(f'https://api.bgm.tv/v0/episodes', params = {'subject_id': subject_id, 'type': _type})
    r.raise_for_status()
    rr = s.get(f'https://api.bgm.tv/v0/subjects/{subject_id}')
    rr.raise_for_status()
    for i in r.json()['data']:
        if i['sort'] == int(num) or i['ep'] == int(num):
            i['showtitle'] = rr.json()['name_cn'] or rr.json()['name']
            i['poster'] = rr.json()['images']['large']
            return i
    return None