import sqlite3

# データベースがなかったら作成する。
dbname = "db/server.db"
connect = sqlite3.connect(dbname)
cur = connect.cursor()
# テーブルがなかったら作成する。
sqlstring = f'create table if not exists media_dl (request_id primary key, title, url, thumbnail, id, status, time, format, silence, percent, path, download_url)'
cur.execute(sqlstring)
connect.close()


class media_dl:
    def __init__(self):
        self.table_name = "media_dl"
        self.conn = sqlite3.connect(dbname)
        self.c = self.conn.cursor()
        print("データベースと接続しました。")

    def save(self, data: dict):
        key = ", ".join(data.keys())
        value = ":" + ", :".join(data.keys())
        sql = f"insert into {self.table_name} ({key}) values ({value})"
        self.c.execute(sql, data)
        self.conn.commit()

    def update(self, request_id, data: dict):
        value = ""
        for key in data:
            value += f"{key} = '{data[key]}',"
        sql = f"update {self.table_name} set {value[:-1]} where request_id = '{request_id}'"
        self.c.execute(sql)
        self.conn.commit()

    def load(self, order:str = None, desc:bool = False) -> list:
        sql = f"select * from {self.table_name}"
        if order != None:
            sql += f" order by {order}"
            if desc:
                sql += " desc"
        self.c.execute(sql)
        return self.c.fetchall()
    
    def load_request_data(self, request_id):
        sql = f"select * from {self.table_name} where request_id = '{request_id}'"
        self.c.execute(sql)
        return self.c.fetchone()

    def __del__(self):
        self.conn.close()
        print("データベースとの接続を解除しました。")


class sus2svg:
    def __init__(self):
        pass