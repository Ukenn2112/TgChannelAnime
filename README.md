# TgChannelAnime

## NC_Raws / Ani Telegram Channel 自动拉取新番

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

## NFO API 服务

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