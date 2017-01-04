#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cassoundra
~~~~~~~~~~

A Discord bot allowing users to upload MP3 files to be played by the bot on command.

Created by Joshua Prince, 2017

v0.1.0 alpha
"""

import os
import configparser

import discord
from discord import voice_client

client = discord.Client()
players = {}  # server -> player


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


def stop(server: discord.Server):
    if players.get(server) is not None:
        if is_playing(server):
            players.get(server).stop()
        players.pop(server)


async def play(sound: str, server: discord.Server, channel: discord.Channel = None, overwrite: bool = False) -> bool:
    """
    Play a sound effect on a server
    :param sound: Sound file name, without .mp3
    :param server: Server to play to
    :param channel: Channel to swap to if necessary
    :param overwrite: Whether to interrupt a sound if it's already playing
    :return: True if the sound was played, False if something was already playing and overwrite was False
    """
    if not os.path.isfile(sound_dir % sound):
        return False

    if overwrite:
        stop(server)
    elif is_playing(server):
        return False

    if channel is not None:
        await move_to_channel(channel)

    players[server] = client.voice_client_in(server).create_ffmpeg_player(sound_dir % sound, after=sound_end)
    players[server].start()

    return True


def sound_end(player: voice_client.ProcessPlayer):
    for p in players.items():
        if players[p] is player:
            players.pop(p)
            print('pop')


def is_request_valid(message: discord.Message):
    """
    Checks conditions on the sender and server to see if Cass can do anything from a request
    :param message: Message encoding the request
    :return: A string with an error message to print, or None if the request is valid
    """
    if message.server is None:
        return "Slide out of my DMs, please."

    if message.author.voice_channel is None:
        return "You aren't in a channel."

    if message.author.voice.is_afk:
        return "I'm afraid of the AFK channel."

    if message.author.voice.deaf or message.author.voice.self_deaf:
        return "You have to suffer your own noise."

    if 0 < message.author.voice_channel.user_limit <= len(message.author.voice_channel.voice_members) and not \
            (client.voice_client_in(message.server) is not None and  # these 2 lines = "and not in the channel already"
             client.voice_client_in(message.server).channel is message.author.voice_channel):
        return "Your voice channel is full."

    return None


def parse_message(string: str) -> {}:
    """
    Converts a message string to a dictionary with information about a command
    :param string: Unaltered message
    :return: 'cmd' = True if it should be parsed, False if otherwise.
    """
    ret = {'cmd': True, 'overwrite': False, 'name': ''}

    # Special commands
    if string == '~':
        return {'cmd': True, 'overwrite': True, 'name': ''}
    if string == '~~':
        return {'cmd': True, 'overwrite': True, 'name': 'record'}
    if string == '~~~':
        return {'cmd': True, 'overwrite': True, 'name': 'dearsister'}

    if string.startswith('!'):
        ret['name'] = string[1:]
    elif string.startswith('~!'):
        ret['overwrite'] = True
        ret['name'] = string[2:]

    if ret['name'] and ret['name'].isalnum():
        return ret

    return {'cmd': False}


@client.event
async def on_ready():
    print('Logged in as ' + client.user.name + ' with ID ' + client.user.id)


@client.event
async def on_message(message: discord.Message):
    msg = parse_message(message.content)
    if msg['cmd']:
        valid = is_request_valid(message)
        if valid is not None:
            await client.send_message(message.channel, valid)
            return

        if msg['overwrite'] and not msg['name']:
            stop(message.server)
            return

        if await play(msg['name'], message.server, message.author.voice_channel, msg['overwrite']):
            print('Playing \'' + message.content[1:] + '.mp3\' into [' +
                  message.server.name + ':' + message.author.voice_channel.name + '] by ' + message.author.name)


if __name__ == '__main__':
    # configuration
    config = configparser.ConfigParser()
    # TODO checking for existence of config.ini
    try:
        config.read('config.ini')
    except configparser.ParsingError as err:
        print('Could not parse config.ini!')
        exit(1)

    sound_dir = config['Sound Information']['SoundDir']
    client.run(config['Bot Information']['APIToken'])
