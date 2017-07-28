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

async def process_input(loop):
    while True:
        command = await loop.run_in_executor(None, input, "> ")
        if str(command).split(" ")[0].lower() == "shutdown":
            return
        print(await handle(command))


async def handle(cmd: str) -> str:
    tok = cmd.split(' ')

    try:
        if tok[0].lower() == 'shutdown':
            return await cmd_shutdown()
        elif tok[0].lower() == 'say':
            return await cmd_say(tok[1], ' '.join(tok[2:]))
        else:
            return "Unknown command " + tok[0] + "."
    except IndexError:
        pass


async def cmd_shutdown() -> str:
    raise KeyboardInterrupt


async def cmd_say(channel: str, content: str) -> str:
    ch = cassoundra.client.get_channel(channel)

    if ch is None:
        return '<#{}>: I couldn\'t find that channel!'.format(channel)

    if ch.type == discord.ChannelType.voice:
        return '<#{}>: Is a voice channel.'.format(channel)

    await cassoundra.client.send_message(ch, content)
    return '<#{}>: "{}"'.format(channel, content)
