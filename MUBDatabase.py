import psycopg2
from enum import Enum
import time


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
        self.db_url = db_url
        self.conn = psycopg2.connect(db_url, sslmode='require')
        self.cur = self.conn.cursor()

    async def check_value(self, table: int, check_item: str, value):
        start = time.time()
        await self.check_connection()
        if table == 1:
            table_dictionary = self.user_table
        elif table == 2:
            table_dictionary = self.guild_table
        elif table == 3:
            table_dictionary = self.guild_users_table
        else:
            raise ValueError("Check value received unexpected integer")

        if check_item == "guild" or check_item == "channel":
            sql = """SELECT EXISTS (SELECT * FROM """ + table_dictionary["table_name"] + """ WHERE ("""\
                  + table_dictionary[check_item] + """" = %d));"""

        else:
            sql = """SELECT EXISTS (SELECT * FROM """ + table_dictionary["table_name"] + """ WHERE ("""\
                  + table_dictionary[check_item] + """" = %s));"""

        self.cur.execute(sql, (value,))
        end = time.time()
        print("Check Value: ", end-start)
        return self.cur.fetchone()[0][0]

    async def add_guild_user(self, guild: int, user: str):
        start = time.time()
        await self.check_connection()
        result = False
        sql = """INSERT INTO guild_users(id, name) VALUES(%s, %s);"""
        try:
            self.cur.execute(sql, (guild, user))
            self.conn.commit()
            result = True
        except:
            self.conn.rollback()
            print("Guild user was not added")
        end = time.time()
        print("Add Guild User: ", end-start)
        return result

    async def add_user(self, user: str, anime: str, manga: str):
        start = time.time()
        await self.check_connection()
        result = False
        sql = """INSERT INTO users(name, last_anime, last_manga) VALUES(%s, %s, %s);"""
        try:
            self.cur.execute(sql, (user, anime, manga))
            self.conn.commit()
            result = True
        except:
            self.conn.rollback()
            print("User was not added")

        end = time.time()
        print("Add User: ", end-start)

        return result

    async def add_guild(self, guild: int, channel_id: int):
        start = time.time()
        await self.check_connection()
        result = False
        sql = """INSERT INTO guilds(id, channel_id) VALUES(%s, %s);"""
        try:
            self.cur.execute(sql, (guild, channel_id))
            self.conn.commit()
            result = True
        except:
            self.conn.rollback()
            print("Guild was not added")

        end = time.time()
        print("Add Guild: ", end-start)
        return result

    async def remove_guild_user(self, guild: int, user: str):
        start = time.time()
        await self.check_connection()
        result = False
        sql = """DELETE FROM guild_users WHERE id = %s AND name = %s;"""
        try:
            self.cur.execute(sql, (guild, user))
            self.conn.commit()
            result = True
        except:
            self.conn.rollback()
            print("Guild user was not removed")

        end = time.time()
        print("Remove Guild User: ", end-start)
        return result

    async def remove_guild_users(self, guild: int):
        start = time.time()
        await self.check_connection()
        result = False
        sql = """DELETE FROM guild_users WHERE id = %s"""
        try:
            self.cur.execute(sql, (guild,))
            self.conn.commit()
            result = True
        except:
            self.conn.rollback()
            print("Guild users were not removed")
        end = time.time()
        print("Remove Guild Users: ", end-start)
        return result

    async def remove_user(self, user: str):
        start = time.time()
        await self.check_connection()
        result = False
        sql = """DELETE FROM users WHERE name = %s;"""
        try:
            self.cur.execute(sql, (user,))
            self.conn.commit()
            result = True
        except:
            self.conn.rollback()
            print("User was not removed")

        end = time.time()
        print("Remove User: ", end-start)
        return result

    async def remove_guild(self, guild: int):
        start = time.time()
        await self.check_connection()
        result = False
        sql = """DELETE FROM guild_users WHERE id = %s);"""
        try:
            await self.remove_guild_users(guild)
            self.cur.execute(sql, (guild,))
            self.conn.commit()
            result = True
        except:
            self.conn.rollback()
            print("Guild was not removed")
        end = time.time()
        print("Remove Guild: ", end-start)
        return result

    async def update_user(self, user: str, anime: str, manga: str):
        start = time.time()
        await self.check_connection()
        result = False
        sql = """UPDATE users SET last_anime = %s, last_manga = %s WHERE name = %s"""
        try:
            self.cur.execute(sql, (anime, manga, user))
            self.conn.commit()
            result = True
        except:
            self.conn.rollback()
            print("User was not updated")
        end = time.time()
        print("Update User: ", end-start)
        return result

    async def update_guild(self, guild: int, channel: int):
        start = time.time()
        await self.check_connection()
        result = False
        sql = """UPDATE guilds SET channel_id = %s WHERE id = %s"""
        try:
            self.cur.execute(sql, (channel, guild))
            self.conn.commit()
            result = True
        except:
            self.conn.rollback()
            print("Guild was not updated")
        end = time.time()
        print("Update Guild: ", end-start)
        return result

    async def get_users(self):
        start = time.time()
        await self.check_connection()
        users = {}
        sql = """SELECT * from users"""
        try:
            self.cur.execute(sql)
            data = self.cur.fetchall()
            for tup in data:
                users[tup[0]] = (tup[1], tup[2])
        except:
            print("Failed to get users")
        end = time.time()
        print("Get Users: ", end-start)
        return users

    async def get_guilds(self):
        start = time.time()
        await self.check_connection()
        guilds = {}
        sql = """SELECT * from guilds"""
        try:
            self.cur.execute(sql)
            data = self.cur.fetchall()
            for tup in data:
                guilds[tup[0]] = tup[1]
        except:
            print("Failed to get guilds")
        end = time.time()
        print("Get Guilds: ", end-start)
        return guilds

    async def get_guild_users(self):
        start = time.time()
        await self.check_connection()
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
        except:
            print("Failed to get guild users")
        end = time.time()
        print("Get Guild Users: ", end-start)
        return guild_users

    async def check_connection(self):
        start = time.time()
        print("Connection closed: " + str(self.conn.closed))
        if self.conn.closed != 0:
            self.cur.close()
            self.conn.close()
            self.conn = psycopg2.connect(self.db_url, sslmode='require')
            self.cur = self.conn.cursor()
        end = time.time()
        print("Check Connection: ", end-start)

#    def synchronize(self, mal_users, server_users, server_channels):
#        synchronize_users(mal_users)
#        synchronize_guilds(server_channels)
#        synchronize_guild_users(server_users)

#    def synchronize_users(self, mal_users):
#        for user in mal_users:
