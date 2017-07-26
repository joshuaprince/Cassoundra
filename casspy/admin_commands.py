#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Cassoundra: admin-commands
~~~~~~~~~~

Module to handle special commands to control the bot once it is already running.

Created by Joshua Prince, 2017
"""


import discord

from casspy import cassoundra

async def handle(cmd: str) -> str:
    tok = cmd.split(' ')

    try:
        if tok[0] == 'shutdown':
            return await cmd_shutdown()
        if tok[0] == 'say':
            return await cmd_say(tok[1], ' '.join(tok[2:]))
    except IndexError:
        pass


async def cmd_shutdown() -> str:
    await cassoundra.client.logout()
    return "Shutting down."


async def cmd_say(channel: str, content: str) -> str:
    ch = cassoundra.client.get_channel(channel)

    if ch is None:
        return '<#{}>: I couldn\'t find that channel!'.format(channel)

    if ch.type == discord.ChannelType.voice:
        return '<#{}>: Is a voice channel.'.format(channel)

    await cassoundra.client.send_message(ch, content)
    return '<#{}>: "{}"'.format(channel, content)
