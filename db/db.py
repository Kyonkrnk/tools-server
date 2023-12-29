import sqlite3




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
    
    def show_database(self):
        data = self.load("time", True)
        for record in data:
            print("------------------------------")
            print(f"request_id:   {record[0]}")
            print(f"title:        {record[1]}")
            print(f"url:          {record[2]}")
            print(f"thumbnail:    {record[3]}")
            print(f"id:           {record[4]}")
            print(f"status:       {record[5]}")
            print(f"time:         {record[6]}")
            print(f"format:       {record[7]}")
            print(f"silence:      {record[8]}")
            print(f"percent:      {record[9]}")
            print(f"path:         {record[10]}")
            print(f"download_url: {record[11]}")
        print("------------------------------\n")
    
    def delete(self, request_id):
        sql = f"delete from {self.table_name} where request_id = '{request_id}'"
        self.c.execute(sql)
        self.conn.commit()

    def __del__(self):
        self.conn.close()
        print("データベースとの接続を解除しました。")


class sus2svg:
    def __init__(self):
        pass


if __name__ == "__main__":
    dbname = "server.db"
    mode = input("1)データ挿入 2)データ更新 3)データ削除 4)jsonから変換\n-> ")
    database = media_dl()
    if mode == "1":
        pass
    elif mode == "2":
        pass
    elif mode == "3":
        database.show_database()
        request_id = input("削除したいレコードのrequest_idを入力してください。\n-> ")
        database.delete(request_id)
        print("削除しました。")
    elif mode == "4":
        import os
        import glob
        import json
        for path in glob.glob("../media_info/*.json"):
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
                data["request_id"] = os.path.basename(path).split(".", 1)[0]
                database.save(data)
                print(f"{path}のデータを保存しました。")
else:
    # データベースがなかったら作成する。
    dbname = "db/server.db"
    connect = sqlite3.connect(dbname)
    cur = connect.cursor()
    # テーブルがなかったら作成する。
    sqlstring = f'create table if not exists media_dl (request_id primary key, title, url, thumbnail, id, status, time, format, silence, percent, path, download_url)'
    cur.execute(sqlstring)
    connect.close()