import xmltodict
import requests

import utils.global_vars as global_vars

s = requests.Session()
s.headers = {
    'User-Agent':'Ukenn/Bangumi2NFO',
    'Authorization': 'Bearer ' + global_vars.config['bgm_token']
}

def subject_nfo(subject_id) -> dict:
    """Bangumi Subject ID 生成 NFO 内容
    :param subject_id: Bangumi Subject ID
    :return: NFO 内容  `{"originalTitle": "原始标题", "tvshowNfo": "tvshow nfo xml", "seasonNfo": "season nfo xml"}`
    :rtype: `dict`  `{"originalTitle": str, "tvshowNfo": str, "seasonNfo": str}`
    """
    data = get_subject(subject_id)
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
            "premiered": data['date'],
            "releasedate": data['date'],
            "tag": [tag['name'] for tag in data['tags'][:9]],
            "bangumiid": data['id'],
            "thumb": [{
                "@aspect": "poster",
                "#text": data['images']['large'],
            },
            {
                "@aspect": "poster",
                "@season": 1,
                "@type": "season",
                "#text": data['images']['large'],
            }],
            "art": {
                "poster": data['images']['large'],
            },
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
        elif person['relation'] == "制片人":
            z = {'name': person['name'], 'role': 'Producer', 'profile': 'https://bgm.tv/person/' + str(person['id'])}
            if person['images']['large']:
                z['thumb'] = person['images']['large']
            tvshow_json['tvshow']['actor'].append(z)
        elif person['relation'] == "系列构成":
            x = {'name': person['name'], 'role': 'Composer', 'profile': 'https://bgm.tv/person/' + str(person['id'])}
            if person['images']['large']:
                x['thumb'] = person['images']['large']
            tvshow_json['tvshow']['actor'].append(x)
    for character in data['characters']:
        for actor in character['actors']:
            c = {'name': actor['name'], 'role': character['name'], 'type': 'Actor', 'profile': 'https://bgm.tv/person/' + str(actor['id'])}
            if actor['images']['large']:
                c['thumb'] = actor['images']['large']
            tvshow_json['tvshow']['actor'].append(c)
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
        "originalTitle": data['name'],
        "tvshowNfo": tvshow_xml,
        "seasonNfo": season_xml,
    }


def episode_nfo(subject_id, num, _type = 0) -> str:
    """Bangumi Episode ID 生成 NFO 内容
    :param subject_id: Bangumi Subject ID
    :param num: 第几集
    :param _type: 0 = 本篇 `默认`, 1 = 特别篇, 2 = OP, 3 = ED, 4 = 预告/宣传/广告, 5 = MAD, 6 = 其他
    :return: NFO 内容
    :rtype: `str`
    """
    data = get_episode(subject_id, num, _type)
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


def get_subject(subject_id) -> dict:
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


def get_episode(subject_id, num, _type = 0) -> dict:
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
        if i['sort'] == int(num):
            i['showtitle'] = rr.json()['name_cn'] or rr.json()['name']
            i['poster'] = rr.json()['images']['large']
            return i
    return None