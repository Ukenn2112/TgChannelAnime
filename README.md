# TgChannelAnime

## NC_Raws / Ani Telegram Channel 自动拉取新番

> 以 NC_Raws 频道 Baha 源为主, 其他源或频道通过白名单判断

### 功能

- [x] Telegram Bot
    - [x] 通过链接/转发频道下载
    - [x] 操作白名单
    - [x] 上传字幕
    - [x] 更新提醒订阅
- [x] NFO 生成
- [x] 更新提醒频道
- [x] 监听群组内字幕转发至频道

......

### 配置

- `data/config.example.json` 重命名 `config.json`

```json
{
    "api_id": 1231231, # 前往生成 https://my.telegram.org/auth
    "api_hash": "7xxxxxxxx", # 前往生成 https://my.telegram.org/auth
    "bot_username": "xxxx_bot", # Bot 名 去 @
    "bot_token": "591xxxxx37:Axxxxxxx25kUiAcY", # Bot 密钥
    "bgm_token": "", bgm_token https://next.bgm.tv/demo/access-token 生成一个最长时间密钥
    "tmdb_token": "xxx", tmdb api token
    "abema_username": "xxx", # abema 账号 （无需求可不填写）
    "abema_password": "xxx", # abema 密码 （无需求可不填写）
    "abema_barer": "xxx", # abema 认证头 （无需求可不填写）
    "admin_list": [
        123123 # 可操作机器人的用户 TG ID 可多个，后续可通过 Bot 操作
    ],
    # 由于监听频道 ID 可能会有变动 需自行填写 监听频道 ID
    "notice_chat": -123123, # 下载更新通知频道 ID
    "nc_chat_id": 123123, # 监听 NC 频道 ID 去前 -100
    "ani_chat_id": 123123, # 监听 Ani 频道 ID 去前 -100
    "forward_chat_id": 123123, # 转发字幕目的地频道 去前 -100
    "nc_group_id": 123123, # 监听字幕群组 ID 去前 -100
    "save_path": "./", # 临时下载路径
    "rclone_config_name": "xxxx_gd", # rclone 挂载盘配置名
    "max_num": 5, # 最大同时下载线程
    # 以下均通过 Bot 操作
    "bgm_compare": [],
    "Baha_blacklist": [],
    "B_Global_whitelist": [],
    "Bilibili_whitelist": [],
    "CR_whitelist": [],
    "Sentai_whitelist": [],
    "abema_list": []
}
```

### Bot 操作

命令列表:

> **Note** 添加白名单或黑名单 均通过判断消息的 Tag name 进行判断 指的就是频道每条消息上的 #<番剧名>

```txt
/baha [add/del] [黑名单] 添加或删除黑名单 多个以#隔开

/b_global [add/del] [白名单] 添加或删除白名单 多个以#隔开

/bilibili [add/del] [白名单/BGM ID] 添加需要 BGM ID 使用 如 大雪海的卡納/366250 删除只需要 TagName

/cr [add/del] [白名单] 解释同上

/sentai [add/del] [白名单] 解释同上

/abema [add/del] [Note/Abema SeasonId/BGM ID/week(1~7)/time(00:00~23:59)] 
添加需要 备注 和 Abema SeasonId 和 BGM ID 使用 如 不当哥哥/19-149/378862/5/0:30(服务器当地时区) 删除只需要 SeasonId

/bgmcom [add/del] [白名单/BGM ID] BGM ID 对照表

/admin [add/del] [白名单] 解释同上

/now_white 获取现在的白名单

/url <bgmid> <tv|movie/tmdbid(可选)> <url> url Ani/Abema 的下载链接

下载 NC-Raws 的视频直接转发频道消息即可

/re_nfo <bgmid> <tmdbid> [tv/movie] 重新生成剧集 NFO

添加字幕，直接将 str 转发给机器人后按提示操作

/help 本帮助
```

### NFO API 服务

- `localhost:1899`

    - `/ping` 在线检测

        `return 200` `{'status': 'OK', 'msg': 'Pong'}`

    - `/send_nfo` 提交生成 NFO 任务

        `Content-Type: application/json`
        ```json
        {
            "season_name": "藍色監獄",
            "volume": 16,
            "bgm_id": "341163",
            "tmdb_d": "tv/131041"
        }
        ```

        正常 `return 200` `{'status': 'OK', 'msg': '已加入生成队列'}`

        错误 `return 400` `{'status': 'ERROR', 'msg': '参数错误'}`

### 文件

```text
.
├── README.md
├── data
│   ├── channel_downloader.session
│   ├── config.example.json
│   ├── config.json
│   ├── run.log
│   └── sqldata.db
├── main.py
├── requirements.txt
└── utils
    ├── abema.py
    ├── bgm_nfo.py
    ├── bot
    │   ├── __init__.py
    │   ├── down.py
    │   ├── help.py
    │   ├── list.py
    │   ├── renfo.py
    │   ├── sendmsg.py
    │   ├── sub.py
    │   └── subscribe.py
    ├── download.py
    ├── global_vars.py
    ├── msg_events.py
    ├── queue_api.py
    ├── schedule_orm.py
    └── sqlite_orm.py
```
