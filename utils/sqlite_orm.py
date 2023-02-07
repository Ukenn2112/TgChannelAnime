import sqlite3


class SQLite:
    def __init__(self):
        self.conn = sqlite3.connect("data/sqldata.db", check_same_thread=False)
        self.cursor = self.conn.cursor()

###### 剧集数据库操作 ######
    def create_season_db(self):
        """创建剧集数据库"""
        self.cursor.execute("""create table if not exists
            Season(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            bgm_id INTEGER UNIQUE,
            tmdb_d VARCHAR(255),
            name_file VARCHAR(255),
            name_ja VARCHAR(255))
            """)
        self.conn.commit()

    def inquiry_name_ja(self, bgm_id) -> str:
        """使用 bgm_id 查询 name_ja"""
        data = self.cursor.execute(f"SELECT name_ja FROM Season WHERE bgm_id = {bgm_id}").fetchone()
        if data:
            return data[0]
        else:
            return ""

    def insert_data(self, bgm_id, tmdb_d, name_file, name_ja):
        """添加剧集数据"""
        self.cursor.execute(f"INSERT INTO Season (bgm_id, tmdb_d, name_file, name_ja) VALUES ({bgm_id}, '{tmdb_d}', '{name_file}', '{name_ja}')")
        self.conn.commit()

###### 订阅数据库操作 ######
    def create_subscribe_db(self):
        """创建订阅数据库"""
        self.cursor.execute("""create table if not exists
            Subscribe(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tg_id INTEGER,
            bgm_id INTEGER)
            """)
        self.conn.commit()

    def inquiry_subscribe_alluser(self, bgm_id) -> list:
        """使用 bgm_id 查询所有订阅用户"""
        data = self.cursor.execute(f"SELECT tg_id FROM Subscribe WHERE bgm_id = {bgm_id}").fetchall()
        if data:
            return [i[0] for i in data]
        else:
            return []
    
    def inquiry_subscribe_user(self, bgm_id, tg_id) -> bool:
        """使用 bgm_id 查询订阅用户"""
        data = self.cursor.execute(f"SELECT tg_id FROM Subscribe WHERE bgm_id = {bgm_id} AND tg_id = {tg_id}").fetchone()
        return bool(data)

    def insert_subscribe(self, bgm_id, tg_id):
        """添加订阅"""
        self.cursor.execute(f"INSERT INTO Subscribe (bgm_id, tg_id) VALUES ({bgm_id}, {tg_id})")
        self.conn.commit()
    
    def delete_subscribe(self, bgm_id, tg_id):
        """删除订阅"""
        self.cursor.execute(f"DELETE FROM Subscribe WHERE bgm_id = {bgm_id} AND tg_id = {tg_id}")
        self.conn.commit()

###### Abema 数据库操作 ######
    def create_abema_db(self):
        """创建 Abema 数据库"""
        self.cursor.execute("""create table if not exists
            Abema(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sid VARCHAR(255),
            down_eid VARCHAR(255),
            bgm_id INTEGER)
            """)
        self.conn.commit()
    
    def inquiry_abema(self, sid) -> list:
        """使用 sid 查询"""
        data = self.cursor.execute(f"SELECT down_eid FROM Abema WHERE sid = '{sid}'").fetchone()
        if data:
            return data
        else:
            return []
    
    def insert_abema(self, sid, down_eid, bgm_id):
        """添加 Abema 数据"""
        self.cursor.execute(f"INSERT INTO Abema (sid, down_eid, bgm_id) VALUES ('{sid}', '{down_eid}', {bgm_id})")
        self.conn.commit()


    def close(self):
        self.conn.close()