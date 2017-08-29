
import logging

import discord

from youtube_dl.utils import ExtractorError

from casspy import cassoundra


class CassClient(discord.Client):
    def __init__(self):
        super().__init__()
        self.players = {}

    def is_playing(self, server: discord.Server) -> bool:
        if self.players.get(server) is None:
            return False
        return self.players.get(server).is_playing()

    async def move_to_channel(self, channel: discord.Channel):
        server = channel.server
        if self.is_playing(server):
            return  # don't stop in the middle of a sound

        if self.is_voice_connected(server):
            if self.voice_client_in(server).channel is not channel:  # connected to a different channel in this server
                await self.voice_client_in(server).move_to(channel)
        else:
            await self.join_voice_channel(channel)  # not connected to a channel in this server

    async def disconnect(self, server: discord.Server):
        await self.voice_client_in(server).disconnect()
        self.players.pop(server)

    def stop(self, server: discord.Server):
        if self.players.get(server) is not None:
            if self.is_playing(server):
                self.players.get(server).stop()
            self.players.pop(server)

    async def play_yt(self, url: str, server: discord.Server, channel: discord.Channel = None,
                      overwrite: bool = False) -> bool:
        if overwrite:
            self.stop(server)
        elif self.is_playing(server):
            return False

        if channel is not None:
            await self.move_to_channel(channel)

            try:
                self.players[server] = await self.voice_client_in(server).create_ytdl_player(
                        url, after=self.on_sound_end,
                        ytdl_options={
                            'default_search': 'ytsearch',
                            'logger': logging.getLogger('cassoundra.ytdl')
                        })
            except ExtractorError:
                logging.getLogger('cassoundra.ytdl').warning('No search results for {}.'.format(url))
                return False

        self.players[server].start()

        return True

    async def play(self, sound: str, server: discord.Server, channel: discord.Channel = None,
                   overwrite: bool = False) -> bool:
        """
        Play a sound effect on a server
        :param sound: Sound file name, without .mp3
        :param server: Server to play to
        :param channel: Channel to swap to if necessary
        :param overwrite: Whether to interrupt a sound if it's already playing
        :return: True if the sound was played, False if something was already playing and overwrite was False
        """
        if self.is_playing(server) and not overwrite:
            return False

        sound_path = cassoundra.get_sound(sound)  # play count increases here

        if sound_path is None:
            return False

        if channel is not None:
            await self.move_to_channel(channel)

        self.players[server] = self.voice_client_in(server).create_ffmpeg_player(sound_path, after=self.on_sound_end)
        self.players[server].start()

        return True

    def on_sound_end(self, player: discord.voice_client.ProcessPlayer):
        for p in self.players.items():
            if self.players[p] is player:
                self.players.pop(p)
