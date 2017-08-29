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
import typing

import django.db
import discord

from cassupload.models import Sound

from casspy import admin_commands, cass_client

client = cass_client.CassClient()
admins = None


def get_sound(sound: str, increase_play_count: bool=True) -> typing.Optional[str]:
    """
    Returns the filepath of a named sound
    :param sound: Name of the sound to play
    :param increase_play_count: If True, the database will track an additional play of this sound
    :return: Full path of sound. None if the sound does not exist.
    """
    try:
        instance = Sound.objects.get(name=sound)  # type: Sound
    except Sound.DoesNotExist:
        return None
    except django.db.utils.OperationalError:  # Django operational error; most likely 'MySQL server has gone away'
        django.db.connection.close()
        return None  # Restart a connection and let the user try again

    if increase_play_count:
        instance.play_count += 1
        instance.save()

    return instance.file.name


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
    ret = {'cmd': True, 'overwrite': False, 'name': '', 'youtube': False, 'volume': 50}

    # Special commands
    if string == '~':
        return {'cmd': True, 'overwrite': True, 'name': '', 'youtube': False, 'volume': 0.0}
    if string == '~~':
        return {'cmd': True, 'overwrite': True, 'name': 'record', 'youtube': False, 'volume': 0.0}
    if string == '~~~':
        return {'cmd': True, 'overwrite': True, 'name': 'dearsister', 'youtube': False, 'volume': 0.0}

    if string.startswith('!!'):
        ret['name'] = string[2:]
        ret['youtube'] = True
    elif string.startswith('~!!'):
        ret['overwrite'] = True
        ret['name'] = string[3:]
        ret['youtube'] = True
    elif string.startswith('!'):
        spl = string[1:].split(' ')
        ret['name'] = spl[0]
        if len(spl) > 1 and spl[1].isdigit():
            ret['volume'] = min(int(spl[1]), 100)
    elif string.startswith('~!'):
        ret['overwrite'] = True
        spl = string[2:].split(' ')
        ret['name'] = spl[0]
        if len(spl) > 1 and spl[1].isdigit():
            ret['volume'] = min(int(spl[1]), 100)

    if ret['name'] and (ret['name'].isalnum() or ret['youtube']):
        return ret

    return {'cmd': False}


def is_admin(user: discord.User) -> bool:
    return user.id in admins


async def handle_direct_message(message: discord.Message):
    if not is_admin(message.author):
        await client.send_message(message.author, "Slide out of my DMs, please.")
        logging.getLogger('cassoundra.console').info('{} sent DM "{}"'.format(message.author.name, message.content))
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
        client.stop(message.server)
        return

    if msg['youtube']:
        if await client.play_yt(msg['name'], message.server, message.author.voice_channel, msg['overwrite']):
            logging.getLogger('cassoundra.play.ytdl').info('Streaming {} into [{}:{}/{}] by [{}/{}].'.format(
                msg['name'], message.server.name, message.author.voice_channel.name, message.author.voice_channel.id,
                message.author.name, message.author.id
            ))
    else:
        if await client.play(msg['name'], message.server, message.author.voice_channel, msg['overwrite'], msg['volume']):
            logging.getLogger('cassoundra.play.file').info('Playing {}.mp3 into [{}:{}/{}] by [{}/{}].'.format(
                msg['name'], message.server.name, message.author.voice_channel.name, message.author.voice_channel.id,
                message.author.name, message.author.id
            ))


@client.event
async def on_ready():
    ready_str = 'Logged in successfully as [{}/{}].'.format(client.user.name, client.user.id)
    print(ready_str)
    logging.getLogger('cassoundra').info(ready_str)


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
            await client.disconnect(before.server)


def main():
    global admins
    config = configparser.ConfigParser()
    try:
        config.read('config.ini')

        token = config['Cassoundra']['apitoken']
        admins = str(config['Cassoundra']['admins']).split(sep=',')
    except configparser.ParsingError:
        logging.getLogger('cassoundra.error').fatal('Could not parse config.ini!')
        return

    try:
        client.loop.run_until_complete(  # thank you discord message 306962625923645441 by robbie0630#9712
            asyncio.wait([
                client.start(token),
                admin_commands.process_input(client.loop)
            ], return_when=asyncio.FIRST_COMPLETED)
        )
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logging.getLogger('cassoundra.error').critical('Encountered an unhandled exception.\n' + str(e))
    finally:
        logging.getLogger('cassoundra').info('Shutting down.')

        try:
            client.loop.run_until_complete(client.logout())
            pending = asyncio.Task.all_tasks(loop=client.loop)
            gathered = asyncio.gather(*pending, loop=client.loop)
            gathered.cancel()
            client.loop.run_until_complete(gathered)

            # we want to retrieve any exceptions to make sure that
            # they don't nag us about it being un-retrieved.
            gathered.exception()
        except Exception as e:
            logging.getLogger('cassoundra.error').debug('Caught exception while gathering tasks:\n' + str(e))
        finally:
            client.loop.close()
