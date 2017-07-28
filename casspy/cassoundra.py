#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cassoundra
~~~~~~~~~~

A Discord bot allowing users to upload MP3 files to be played by the bot on command.

Created by Joshua Prince, 2017

v0.2.0 alpha
"""

import configparser
import logging
import asyncio

from django.db import connection
from django.db.utils import OperationalError

import discord
from discord import voice_client

from cassupload.models import Sound

from casspy import admin_commands

logger = logging.getLogger('casspy')
client = discord.Client()
players = {}  # server -> player
admins = None


def is_playing(server: discord.Server) -> bool:
    if players.get(server) is None:
        return False
    return players.get(server).is_playing()


async def move_to_channel(channel: discord.Channel):
    server = channel.server
    if is_playing(server):
        return  # don't stop in the middle of a sound

    if client.is_voice_connected(server):
        if client.voice_client_in(server).channel is not channel:  # connected to a different channel in this server
            await client.voice_client_in(server).move_to(channel)
    else:
        await client.join_voice_channel(channel)  # not connected to a channel in this server


async def disconnect(server: discord.Server):
    await client.voice_client_in(server).disconnect()
    players.pop(server)
    if len(players) == 0:
        connection.close()
        logger.info('No living connections; database going to sleep')


def stop(server: discord.Server):
    if players.get(server) is not None:
        if is_playing(server):
            players.get(server).stop()
        players.pop(server)


async def play_yt(url: str, server: discord.Server, channel: discord.Channel = None, overwrite: bool = False) -> bool:
    if overwrite:
        stop(server)
    elif is_playing(server):
        return False

    if channel is not None:
        await move_to_channel(channel)

    players[server] = await client.voice_client_in(server).create_ytdl_player(url=url, after=sound_end)
    players[server].start()

    return True


async def play(sound: str, server: discord.Server, channel: discord.Channel = None, overwrite: bool = False) -> bool:
    """
    Play a sound effect on a server
    :param sound: Sound file name, without .mp3
    :param server: Server to play to
    :param channel: Channel to swap to if necessary
    :param overwrite: Whether to interrupt a sound if it's already playing
    :return: True if the sound was played, False if something was already playing and overwrite was False
    """
    try:
        instance = Sound.objects.get(name=sound)  # type: Sound
    except Sound.DoesNotExist:
        return False
    except OperationalError:  # Django operational error; most likely 'MySQL server has gone away'
        connection.close()
        return False  # Restart a connection and let the user try again

    if overwrite:
        stop(server)
    elif is_playing(server):
        return False

    instance.play_count += 1
    instance.save()

    if channel is not None:
        await move_to_channel(channel)

    players[server] = client.voice_client_in(server).create_ffmpeg_player(instance.file.name, after=sound_end)
    players[server].start()

    return True


def sound_end(player: voice_client.ProcessPlayer):
    for p in players.items():
        if players[p] is player:
            players.pop(p)


def get_request_error(message: discord.Message):
    """
    Checks conditions on the sender and server to see if Cass can do anything from a request
    :param message: Message encoding the request
    :return: A string with an error message to print, or None if the request is valid
    """
    if message.author.voice_channel is None:
        return "You aren't in a channel."

    if message.author.voice.is_afk:
        return "I'm afraid of the AFK channel."

    if message.author.voice.deaf or message.author.voice.self_deaf:
        return "You have to suffer your own noise."

    # By here, we should just make sure we'll actually be able to join the channel, so stop now if we're already in it.
    if (client.voice_client_in(message.server) is not None and
            client.voice_client_in(message.server).channel is message.author.voice_channel):
        return None

    if 0 < message.author.voice_channel.user_limit <= len(message.author.voice_channel.voice_members):
        return "Your voice channel is full."

    if not (message.author.voice_channel.permissions_for(message.server.me).connect and
            message.author.voice_channel.permissions_for(message.server.me).speak):
        return "I'm not allowed into that channel."

    return None


def parse_server_message(string: str) -> {}:
    """
    Converts a message string to a dictionary with information about a command
    :param string: Unaltered message
    :return: 'cmd' = True if it should be parsed, False if otherwise.
    """
    ret = {'cmd': True, 'overwrite': False, 'name': '', 'youtube': False}

    # Special commands
    if string == '~':
        return {'cmd': True, 'overwrite': True, 'name': '', 'youtube': False}
    if string == '~~':
        return {'cmd': True, 'overwrite': True, 'name': 'record', 'youtube': False}
    if string == '~~~':
        return {'cmd': True, 'overwrite': True, 'name': 'dearsister', 'youtube': False}

    if string.startswith('!!'):
        ret['name'] = string[2:]
        ret['youtube'] = True
    elif string.startswith('~!!'):
        ret['overwrite'] = True
        ret['name'] = string[3:]
        ret['youtube'] = True
    elif string.startswith('!'):
        ret['name'] = string[1:]
    elif string.startswith('~!'):
        ret['overwrite'] = True
        ret['name'] = string[2:]

    if ret['name'] and (ret['name'].isalnum() or ret['youtube']):
        return ret

    return {'cmd': False}


def is_admin(user: discord.User) -> bool:
    return user.id in admins


@client.event
async def on_ready():
    print('Logged in as ' + client.user.name + ' with ID ' + client.user.id)
    logger.info('Login as ' + client.user.name + ' with ID ' + client.user.id)


async def handle_direct_message(message: discord.Message):
    if not is_admin(message.author):
        await client.send_message(message.author, "Slide out of my DMs, please.")
        logger.info('{} sent DM "{}"'.format(message.author.name, message.content))
        return

    try:
        response = await admin_commands.handle(message.content)
    except Exception as e:
        response = "Seems like I had some kind of problem fulfilling that command:\n" + str(e)

    if response is not None:
        await client.send_message(message.author, response)


async def handle_server_message(message: discord.Message):
    msg = parse_server_message(message.content)
    if not msg['cmd']:
        return

    error = get_request_error(message)
    if error is not None:
        await client.send_message(message.channel, error)
        return

    if msg['overwrite'] and not msg['name']:
        stop(message.server)
        return

    if msg['youtube']:
        if await play_yt(msg['name'], message.server, message.author.voice_channel, msg['overwrite']):
            logger.info('Playing YOUTUBE:' + msg['name'] + 'into [' +
                        message.server.name + ':' + message.author.voice_channel.name + '] by ' +
                        message.author.name)
    else:
        if await play(msg['name'], message.server, message.author.voice_channel, msg['overwrite']):
            logger.info('Playing \'' + msg['name'] + '.mp3\' into [' +
                        message.server.name + ':' + message.author.voice_channel.name + '] by ' +
                        message.author.name)


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    await handle_direct_message(message) if message.server is None else await handle_server_message(message)


@client.event
async def on_voice_state_update(before: discord.Member, after: discord.Member):
    # If the Member is leaving the Channel I'm in
    if before.server.voice_client is not None and before.server.voice_client.channel is before.voice.voice_channel:
        if len(before.server.voice_client.channel.voice_members) == 1:
            await disconnect(before.server)


async def process_input():
    while True:
        command = await client.loop.run_in_executor(None, input, "> ")
        if str(command).split(" ")[0].lower() == "shutdown":
            return
        print(await admin_commands.handle(command))


def main():
    global admins
    config = configparser.ConfigParser()
    try:
        config.read('config.ini')

        apitoken = config['Cassoundra']['apitoken']
        admins = str(config['Cassoundra']['admins']).split(sep=',')
    except configparser.ParsingError:
        logger.fatal('Could not parse config.ini!')
        exit(1)

    try:
        client.loop.run_until_complete(  # thank you discord message 306962625923645441 by robbie0630#9712
            asyncio.wait([
                client.start(apitoken),
                process_input()
            ], return_when=asyncio.FIRST_COMPLETED)
        )
    except KeyboardInterrupt:
        pass

    try:
        client.loop.run_until_complete(client.logout())
        pending = asyncio.Task.all_tasks(loop=client.loop)
        gathered = asyncio.gather(*pending, loop=client.loop)
        gathered.cancel()
        client.loop.run_until_complete(gathered)

        # we want to retrieve any exceptions to make sure that
        # they don't nag us about it being un-retrieved.
        gathered.exception()
    except:
        pass
    finally:
        client.loop.close()
