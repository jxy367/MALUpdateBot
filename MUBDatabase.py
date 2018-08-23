import psycopg2
from enum import Enum


class Tables(Enum):
    USERS = 1
    GUILDS = 2
    GUILD_USERS = 3


class MUBDatabase:
    db_url = ""
    conn = ""
    cur = ""

    user_table = {"table_name": "users", "user": "name", "anime": "last_anime", "manga": "last_manga"}
    guild_table = {"table_name": "guilds", "guild": "id", "channel": "channel_id"}
    guild_users_table = {"table_name": "guild_users", "guild": "id", "user": "name"}

    def __init__(self, db_url: str):
        self.conn = psycopg2.connect(db_url, sslmode='require')
        self.cur = self.conn.cursor()

    def check_value(self, table: int, check_item: str, value):
        if table == 1:
            table_dictionary = self.user_table
        elif table == 2:
            table_dictionary = self.guild_table
        elif table == 3:
            table_dictionary = self.guild_users_table
        else:
            raise ValueError("Check value received unexpected integer")

        sql = ""
        if check_item == "guild" or check_item == "channel":
            sql = """SELECT EXISTS (SELECT * FROM """ + table_dictionary["table_name"] + """ WHERE ("""\
                  + table_dictionary[check_item] + """" = %d));"""

        else:
            sql = """SELECT EXISTS (SELECT * FROM """ + table_dictionary["table_name"] + """ WHERE ("""\
                  + table_dictionary[check_item] + """" = %s));"""

        self.cur.execute(sql, (value,))

        return self.cur.fetchone()[0][0]

    def add_guild_user(self, guild: int, user: str):
        sql = """INSERT INTO guild_users(id, name) VALUES(%s, %s);"""
        try:
            self.cur.execute(sql, (guild, user))
            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            print(e)
            print("Guild user was not added")
            return False
        return True

    def add_user(self, user: str, anime: str, manga: str):
        sql = """INSERT INTO users(name, last_anime, last_manga) VALUES(%s, %s, %s);"""
        try:
            self.cur.execute(sql, (user, anime, manga))
            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            print(e)
            print("User was not added")
            return False
        return True

    def add_guild(self, guild: int, channel_id: int):
        sql = """INSERT INTO guilds(id, channel_id) VALUES(%s, %s);"""
        try:
            self.cur.execute(sql, (guild, channel_id))
            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            print(e)
            print("Guild was not added")
            return False
        return True

    def remove_guild_user(self, guild: int, user: str):
        sql = """DELETE FROM guild_users WHERE id = %s AND name = %s;"""
        try:
            self.cur.execute(sql, (guild, user))
            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            print(e)
            print("Guild user was not removed")
            return False
        return True

    def remove_guild_users(self, guild: int):
        sql = """DELETE FROM guild_users WHERE id = %s"""
        try:
            self.cur.execute(sql, (guild,))
            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            print(e)
            print("Guild users were not removed")
            return False
        return True

    def remove_user(self, user: str):
        sql = """DELETE FROM users WHERE name = %s;"""
        try:
            self.cur.execute(sql, (user,))
            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            print(e)
            print("User was not removed")
            return False
        return True

    def remove_guild(self, guild: int):
        sql = """DELETE FROM guild_users WHERE id = %s);"""
        try:
            self.remove_guild_users(guild)
            self.cur.execute(sql, (guild,))
            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            print(e)
            print("Guild was not removed")
            return False
        return True

    def update_user(self, user: str, anime: str, manga: str):
        sql = """UPDATE users SET last_anime = %s, last_manga = %s WHERE name = %s"""
        try:
            self.cur.execute(sql, (anime, manga, user))
            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            print(e)
            print("User was not updated")
            return False
        return True

    def update_guild(self, guild: int, channel: int):
        sql = """UPDATE guilds SET channel_id = %s WHERE id = %s"""
        try:
            self.cur.execute(sql, (channel, guild))
            self.conn.commit()

        except Exception as e:
            self.conn.rollback()
            print(e)
            print("Guild was not updated")
            return False
        return True

    def get_users(self):
        users = {}
        sql = """SELECT * from users"""
        try:
            self.cur.execute(sql)
            data = self.cur.fetchall()
            for tup in data:
                users[tup[0]] = (tup[1], tup[2])
        except Exception as e:
            print(e)
            print("Failed to get users")
        return users

    def get_guilds(self):
        guilds = {}
        sql = """SELECT * from guilds"""
        try:
            self.cur.execute(sql)
            data = self.cur.fetchall()
            for tup in data:
                guilds[tup[0]] = tup[1]
        except Exception as e:
            print(e)
            print("Failed to get guilds")
        return guilds

    def get_guild_users(self):
        guild_users = {}
        sql = """SELECT * from guild_users"""
        try:
            self.cur.execute(sql)
            data = self.cur.fetchall()
            for tup in data:
                if tup[0] in guild_users:
                    guild_users[tup[0]].append(tup[1])
                else:
                    guild_users[tup[0]] = [tup[1]]
        except Exception as e:
            print(e)
            print("Failed to get guild users")
        return guild_users



#    def synchronize(self, mal_users, server_users, server_channels):
#        synchronize_users(mal_users)
#        synchronize_guilds(server_channels)
#        synchronize_guild_users(server_users)

#    def synchronize_users(self, mal_users):
#        for user in mal_users:
