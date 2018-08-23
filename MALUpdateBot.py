import discord
from discord.ext import commands
import asyncio
import os
import urllib
from urllib import request
from urllib import error
import psycopg2
from MUBDatabase import MUBDatabase

from bs4 import BeautifulSoup
import json

TOKEN = os.environ.get('TOKEN')
DATABASE_URL = os.environ['DATABASE_URL']
mub_db = MUBDatabase(DATABASE_URL)

client = commands.Bot(command_prefix="MUB ", case_insensitive=True)

on_cooldown = {}
cooldown_time = 10

mal_users = mub_db.get_users()  # MAL usernames and (latest anime and manga)
server_channel = mub_db.get_guilds()  # Guild id and MAL usernames
server_users = mub_db.get_guild_users()  # Guild id and preferred channel

anime_statuses = {1: "Watching", 2: "Completed", 3: "On-Hold", 4: "Dropped", 6: "Plans to watch"}
manga_statuses = {1: "Reading", 2: "Completed", 3: "On-Hold", 4: "Dropped", 6: "Plans to read"}


def get_cooldown_key(message_or_channel):
    global on_cooldown
    try:
        key = message_or_channel.guild
    except AttributeError:
        if isinstance(message_or_channel, discord.Message):
            key = message_or_channel.channel.id
        elif isinstance(message_or_channel, discord.TextChannel):
            key = message_or_channel.id
        else:
            key = "unfortunate"
    if key not in on_cooldown:
        on_cooldown[key] = 0
    return key


def get_current_cooldown(message_or_channel):
    key = get_cooldown_key(message_or_channel)
    return on_cooldown[key]


def reset_cooldown(message_or_channel):
    global on_cooldown
    global cooldown_time
    key = get_cooldown_key(message_or_channel)
    on_cooldown[key] = cooldown_time


def is_mal_user(user: str):
    url = "https://myanimelist.net/profile/" + user
    try:
        response = urllib.request.urlopen(url)
        return True
    except urllib.error.HTTPError:
        return False


def mal_list(user: str, list_type: str):
    url = "https://myanimelist.net/" + list_type + "list/" + user + "?order=5&status=7"
    try:
        response = urllib.request.urlopen(url)
        html = response.read()
        soup = BeautifulSoup(html, "html.parser")
        table = soup.find(attrs={"class": "list-table"})
        blah = "woo"
        if table.has_attr('data-items'):
            blah = table.get('data-items')
        user_list = json.loads(blah)
        return user_list
    except urllib.error.HTTPError:
        print("WAAAA")
    return []


def latest_entry(user: str, list_type: str):
    user_list = mal_list(user, list_type)
    if len(user_list) > 0:
        return user_list[0]
    return ""


def latest_entry_title(user: str, list_type: str):
    entry = latest_entry(user, list_type)
    if entry == "":
        return ""
    else:
        return entry[list_type + '_title']


def convert_updates_to_embeds(user, updates):
    embeds = []
    for update in updates:
        if 'anime_title' in update:
            embed = convert_anime_update_to_embed(user, update)
            embeds.append(embed)
        elif 'manga_title' in update:
            embed = convert_manga_update_to_embed(user, update)
            embeds.append(embed)
        else:
            print("welp")
    return embeds


def convert_anime_update_to_embed(user, update):
    title = update['anime_title']
    embed = discord.Embed(title=user + " updated " + title)
    if 'anime_image_path' in update:
        embed.set_image(url=update['anime_image_path'])
    embed.add_field(name="Status: ", value=anime_statuses[int(update['status'])], inline=False)
    if update['score'] != 0:
        embed.add_field(name="Score: ", value=str(update['score']), inline=False)
    if update['tags'] != '':
        embed.add_field(name="Tags: ", value=update['tags'], inline=False)

    if update['is_rewatching'] != 0:
        embed.add_field(name="Rewatched: ", value=str(update['is_rewatching']) + " times", inline=False)

    if update['anime_media_type_string'] != 'Movie':
        if 'num_watched_episodes' in update and 'anime_num_episodes' in update:
            embed.add_field(name="Episodes watched: ", value=str(update['num_watched_episodes']) + "/" + str(
                update['anime_num_episodes']), inline=False)

    return embed


def convert_manga_update_to_embed(user, update):
    title = update['manga_title']
    embed = discord.Embed(title=user + " updated " + title)
    if 'manga_image_path' in update:
        embed.set_image(url=update['manga_image_path'])
    embed.add_field(name="Status: ", value=manga_statuses[int(update['status'])], inline=False)
    if update['score'] != 0:
        embed.add_field(name="Score: ", value=str(update['score']), inline=False)
    if update['tags'] != '':
        embed.add_field(name="Tags: ", value=update['tags'], inline=False)

    if update['is_rereading'] != 0:
        embed.add_field(name="Reread: ", value=str(update['is_rereading']) + " times", inline=False)

    if 'num_read_chapters' in update and 'manga_num_chapters' in update:
        read_chapters = update['num_read_chapters']
        num_chapters = update['manga_num_chapters']
        if read_chapters < num_chapters:
            embed.add_field(name="Chapters read: ", value=str(read_chapters) + "/" + str(num_chapters), inline=False)
        else:
            embed.add_field(name="Chapters read: ", value=str(read_chapters), inline=False)

    return embed


def get_user_updates(user: str):
    updates = []
    last_anime_entry, last_manga_entry = mal_users[user]
    anime_list = mal_list(user, "anime")
    manga_list = mal_list(user, "manga")

    for anime_entry in anime_list:
        if anime_entry['anime_title'] == last_anime_entry:
            break

        updates.append(anime_entry)

        if last_anime_entry == "":
            break

    for manga_entry in manga_list:
        if manga_entry['manga_title'] == last_manga_entry:
            break

        updates.append(manga_entry)

        if last_manga_entry == "":
            break

    updates.reverse()  # So that updates are in from oldest to newest

    if len(updates) > 0:
        anime = anime_list[0]['anime_title']
        manga = manga_list[0]['manga_title']
        mal_users[user] = (anime, manga)
        mub_db.update_user(user, anime, manga)

    return updates


def add_user(user: str, guild_id: int):
    if user not in mal_users:
        anime_entry = latest_entry_title(user, "anime")
        manga_entry = latest_entry_title(user, "manga")
        mal_users[user] = (anime_entry, manga_entry)
        mub_db.add_user(user, anime_entry, manga_entry)

    if user not in server_users[guild_id]:
        server_users[guild_id].append(user)
        mub_db.add_guild_user(guild_id, user)
        return True

    return False


def remove_user(user: str, guild_id: int):
    if guild_id not in server_users:
        return False
    return_value = False
    user_in_server = False

    if user in server_users[guild_id]:
        server_users[guild_id].remove(user)
        mub_db.remove_guild_user(guild_id, user)
        return_value = True

    for guild in server_users:
        if user in server_users[guild]:
            user_in_server = True
            break

    if not user_in_server:
        del mal_users[user]
        mub_db.remove_user(user)

    return return_value


def remove_unnecessary_users():
    unnecessary_users = []
    for user in mal_users:
        user_necessary = False
        for guild_id in server_users:
            if user in server_users[guild_id]:
                user_necessary = True
                break
        if not user_necessary:
            unnecessary_users.append(user)

    for unnecessary_user in unnecessary_users:
        del mal_users[unnecessary_user]
        mub_db.remove_user(user)


def print_values():
    print("--------------------------")
    print("Number of users: " + str(len(mal_users)))
    for u in mal_users:
        print("User: " + str(u) + ", Anime: " + str(mal_users[u][0]) + ", Manga: " + str(mal_users[u][1]))
    print("Number of servers: " + str(len(server_channel)))
    for sc in server_channel:
        print("Server " + str(sc) + " : " + str(server_channel[sc]))
    print("Server and users")
    for s in server_users:
        print("Server " + str(s) + " : " + str(server_users[s]))


def print_status():
    print("---- Status ------")
    print("Bot status: " + str(client.status))
    print("Is closed: " + str(client.is_closed()))
    print("Is ready: " + str(client.is_ready()))
    print("Websocket: " + str(client.ws))
    print("Per server: ")
    for g in client.guilds:
        print(str(g.me.status))


async def main_update():
    # Printing output
    #print_output()

    # Printing status
    print_status()

    # Actual update
    for user in mal_users:
        updates = get_user_updates(user)
        updates = convert_updates_to_embeds(user, updates)
        for guild in server_users:
            if user in server_users[guild]:
                channel = client.get_channel(server_channel[guild])
                if channel is None:
                    channel = client.get_guild(guild).text_channels[0]
                    server_channel[guild] = channel.id
                    mub_db.update_guild(guild, channel.id)
                for embed in updates:
                    await channel.send(embed=embed)


async def reset_display_name():
    for changed_guild in client.guilds:
        if changed_guild.me.display_name != "MAL Update Bot":
            print(changed_guild.name)
            print(changed_guild.me.display_name)
            print("---")
            await changed_guild.me.edit(nick=None)


async def background_update():
    await client.wait_until_ready()
    while not client.is_closed():
        await main_update()
        await reset_display_name()
        await asyncio.sleep(60)


async def cooldown():
    global on_cooldown
    await client.wait_until_ready()
    while not client.is_closed():
        for guild in on_cooldown:
            on_cooldown[guild] = on_cooldown[guild] - 1
            if on_cooldown[guild] < 0:
                on_cooldown[guild] = 0
        await asyncio.sleep(1)


async def await_message(message: discord.Message, content=None, embed=None):
    if content is None:
        await message.channel.send(embed=embed)
    elif embed is None:
        await message.channel.send(content=content)
    else:
        await message.channel.send(content=content+"!!", embed=embed)

    reset_cooldown(message)


async def await_channel(channel: discord.TextChannel, content=None, embed=None):
    if channel is not None:
        if content is None:
            await channel.send(embed=embed)
        elif embed is None:
            await channel.send(content=content)
        else:
            await channel.send(content=content, embed=embed)

    reset_cooldown(channel)


async def await_ctx(ctx: discord.ext.commands.Context, content=None, embed=None):
    if content is None:
        await ctx.send(embed=embed)
    elif embed is None:
        await ctx.send(content=content)
    else:
        await ctx.send(content=content, embed=embed)

    reset_cooldown(ctx.channel)


@client.event
async def on_message(message):
    if message.author.bot:
        return

    await client.process_commands(message)


@client.command()
async def add(ctx, *, user):
    user = user.lower()
    if ctx.guild.id not in server_users:
        server_users[ctx.guild.id] = []

    if ctx.guild.id not in server_channel:
        server_channel[ctx.guild.id] = ctx.channel.id

    if is_mal_user(user):
        if add_user(user, ctx.guild.id):
            await await_ctx(ctx=ctx, content=user + " successfully added")
        else:
            await await_ctx(ctx=ctx, content="User, " + user + ", already in list of users")
    else:
        await await_ctx(ctx=ctx, content="User, " + user + ", could not be found")


@client.command()
async def remove(ctx, *, user):
    user = user.lower()
    if user in mal_users:
        if remove_user(user, ctx.guild.id):
            await await_ctx(ctx=ctx, content="User successfully removed")
        else:
            await await_ctx(ctx=ctx, content="User, " + user + ", could not be removed")
    else:
        await await_ctx(ctx=ctx, content="User, " + user + ", could not be found")


@client.command()
async def set_channel(ctx):
    server_channel[ctx.guild.id] = ctx.channel.id
    mub_db.update_guild(ctx.guild.id, ctx.channel.id)
    await await_ctx(ctx=ctx, content="This channel will receive updates.")


@client.command()
async def users(ctx):
    if ctx.guild.id not in server_channel:
        server_channel[ctx.guild.id] = ctx.channel.id

    if ctx.guild.id not in server_users:
        server_users[ctx.guild.id] = []

    if len(server_users[ctx.guild.id]) > 0:
        embed = discord.Embed()
        value = ""
        for user in server_users[ctx.guild.id]:
            value += user + "\n"
        embed.add_field(name="List of users: ", value=value, inline=True)
        await await_ctx(ctx=ctx, embed=embed)
    else:
        await await_ctx(ctx=ctx, content="This server has not added any users")

client.remove_command('help')


@client.command()
async def help(ctx):
    embed = discord.Embed(title="MAL Update Bot", description="List of commands:", color=0xeee657)

    embed.add_field(name="MUB add *username*", value="Attempts to add a user to keep track of", inline=False)
    embed.add_field(name="MUB remove *username*", value="Attempts to remove a user", inline=False)
    embed.add_field(name="MUB users", value="Lists all users MUB keeps track of", inline=False)
    embed.add_field(name="MUB set_channel", value="Sets the current channel to receive updates")
    embed.add_field(name="MUB help", value="Gives this message", inline=False)

    await await_ctx(ctx=ctx, embed=embed)


@client.event
async def on_guild_join(guild):
    server_users[guild.id] = []
    server_channel[guild.id] = guild.textchannels[0]
    mub_db.add_guild(guild.id, guild.textchannels[0])


@client.event
async def on_guild_remove(guild):
    del server_users[guild.id]
    del server_channel[guild.id]
    mub_db.remove_guild(guild)
    remove_unnecessary_users()


@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

    for g in client.guilds:
        if g.id not in server_channel:
            server_channel[g.id] = g.text_channels[0].id

    client.loop.create_task(background_update())
    client.loop.create_task(cooldown())


client.run(TOKEN)
