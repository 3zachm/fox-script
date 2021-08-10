import discord
import configparser
import os
import io
import asyncio
import json
import time
import twitchAPI
from twitchAPI.twitch import Twitch
from pprint import pprint
import utils.file_manager as files
import utils.log_manager as logs
from discord.ext import commands
import utils.commands as cmds
import utils.utils as utils

boot_time = time.time()
files.script_dir = os.path.dirname(os.path.realpath(__file__))
files.make_config(files.config_loc())

with open(files.config_loc()) as c:
    discord_config = c.read()
config = configparser.RawConfigParser(allow_no_value=True)
config.read_file(io.StringIO(discord_config))

try:
    default_prefix = config.get('discord', 'default_prefix')
    bot_token = config.get('discord', 'token')
    channel_id = config.get('discord', 'channel_id')
    guild_id = config.get('discord', 'guild_id')
    role_id = config.get('discord', 'role_id')
    twitch_token = config.get('twitch', 'token')
    twitch_key = config.get('twitch', 'key')
    twitch_user = config.get('twitch', 'user_id')
    generate_logs = config.getboolean('python', 'generate_logs')
except (configparser.NoSectionError, configparser.NoOptionError) as e:
    print(e)
    print("Ensure config file has all entries present. If you recently pulled an update, consider regenerating the config")
    quit()

#logging
if generate_logs:
    logger = logs.init_logs(files.logs_dir())

bot = commands.Bot(command_prefix = default_prefix)
bot.remove_command('help')

twitch = Twitch(twitch_key, twitch_token)

twitch_exceptions = (twitchAPI.types.TwitchAuthorizationException, twitchAPI.types.TwitchAPIException, twitchAPI.types.TwitchBackendException,
                    twitchAPI.types.UnauthorizedException, twitchAPI.types.NotFoundException, twitchAPI.types.InvalidTokenException, twitchAPI.types.MissingAppSecretException,
                    twitchAPI.types.MissingScopeException, twitchAPI.types.InvalidRefreshTokenException)

@bot.event
async def on_ready():
    bot.presence_routine = asyncio.create_task(update_minecraft())
    print("\n\nRunning...")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandNotFound):
        return
    if isinstance(error, commands.errors.CheckFailure):
        return
    if isinstance(error, commands.errors.MissingPermissions) and ctx.guild is None:
        return
    if isinstance(error, commands.errors.MissingRequiredArgument):
        return
    # unhandled exception occurred
    if generate_logs:
        logs.exception(ctx, error, logger)
    else:
        raise error

@bot.group(name="system", aliases=["sys"], invoke_without_command=True)
@commands.check(cmds.owner_check)
async def system(ctx):
    pass

@system.command(name="pt")
@commands.check(cmds.owner_check)
async def system_pt(ctx):
    if cmds.owner_check(ctx):
        await ctx.send("You have owner permissions.")

@bot.command(name="uptime")
@commands.check(cmds.owner_check)
async def uptime(ctx):
    await ctx.send("**Uptime**: `{0}`\n**Server**: `{1}`".format(utils.get_uptime(boot_time), utils.get_sysuptime()))

@bot.command(name="game_test")
@commands.check(cmds.owner_check)
async def game_test(ctx, userid, *index):
    try:
        if len(index) < 1:
            await ctx.send(twitch.get_channel_information(userid)['data'][0])
        else:
            await ctx.send(twitch.get_channel_information(userid)['data'][0][index[0]])
    except twitch_exceptions as e:
        await ctx.send(str(e))

@bot.command(name="live_test")
@commands.check(cmds.owner_check)
async def live_test(ctx, userid):
    try:
        rtn = twitch.get_streams(user_id=userid)
        await ctx.send(rtn['data'] != [])
    except twitch_exceptions as e:
        await ctx.send(str(e))

async def update_minecraft():
    userid =  twitch_user
    last_state = None
    last_game = None
    c = channel_id
    guild = await bot.fetch_guild(guild_id)
    role = guild.get_role(int(role_id))

    while True:
        try:
            channel = await bot.fetch_channel(c)
            try:
                channel_info = twitch.get_streams(user_id=userid)['data'][0]
                key = 'user_name'
                is_live = True
            except IndexError:
                channel_info = twitch.get_channel_information(userid)['data'][0]
                key = 'broadcaster_name'
                is_live = False
            except twitch_exceptions as e:
                print(e)
                logger.log(e)
                channel.send("Something bad happened :( <@!106188449643544576>")
                quit()

            current_game = channel_info['game_name']
            new_game = (last_game != current_game)
            new_state = (last_state != is_live)

            if (last_state is None) or new_game or new_state:
                is_minecraft = (current_game == 'Minecraft')
                if is_live and is_minecraft:
                    message = '{0} is live and playing minecraft! This channel will now lock for discord users until she changes games'.format(channel_info[key])
                    await channel.set_permissions(role, send_messages=False)
                elif is_live:
                    message = '{0} is live not playing minecraft, just {1}. This channel will stay open/now be accessible'.format(channel_info[key], current_game)
                    await channel.set_permissions(role, send_messages=True)
                elif is_minecraft:
                    message = '{0} is not live, this channel will stay open/now be accessible'.format(channel_info[key])
                    await channel.set_permissions(role, send_messages=True)
                else:
                    message = '{0} is not/no longer live, this channel will stay open/now be accessible'.format(channel_info[key])
                    await channel.set_permissions(role, send_messages=True)
                await channel.send(message)
                last_state = is_live
                last_game = current_game
        except twitch_exceptions as e: # bleh
            print(e)
            logger.log(e)
            channel.send("Something bad happened :( <@!106188449643544576>")
            quit()
        await asyncio.sleep(300)

bot.run(bot_token)