from modules.structure import setup_logging

setup_logging()

import logging

logger = logging.getLogger(__name__)
logger.info("Starting")

import discord, asyncio
from aredis import RedisError

import config
from modules import statics, apis, commands
from modules.redis_client import redis


class SpaceXLaunchBotClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Create asyncio tasks now
        # self.loop.create_task(func())

    async def on_ready(self):
        logger.info("Succesfully connected to Discord API")

        self.dbl = apis.DblApi(self.user.id, config.DBL_TOKEN)

        await self.change_presence(activity=discord.Game(name=config.BOT_GAME))
        await self.dbl.update_guild_count(len(self.guilds))

    async def on_guild_join(self, guild):
        logger.info(f"Joined guild, ID: {guild.id}")
        await self.dbl.update_guild_count(len(self.guilds))

    async def on_guild_remove(self, guild):
        logger.info(f"Removed from guild, ID: {guild.id}")
        await self.dbl.update_guild_count(len(self.guilds))

        deleted = await redis.delete_guild_mentions(guild.id)
        if deleted != 0:
            logger.info(f"Removed guild settings for {guild.id}")

    async def on_message(self, message):
        if (
            not message.content.startswith(config.COMMAND_PREFIX)
            or message.author.bot
            or not message.guild
        ):
            # Not a command, ignore it
            # Don't reply to bots (includes self)
            # Only reply to messages from guilds
            return

        # Remove the first occurance of the command prefix, it's not needed anymore
        message.content = message.content.replace(config.COMMAND_PREFIX, "", 1)

        # Commands can be in any case
        message.content = message.content.lower()

        # Gather permission related vars
        userIsOwner = message.author.id == int(config.OWNER_ID)
        try:
            userIsAdmin = message.author.permissions_in(message.channel).administrator
        except AttributeError:
            # AttributeError occurs if user has no roles
            userIsAdmin = False

        try:
            await commands.handleCommand(self, message, userIsOwner, userIsAdmin)
        except RedisError as e:
            logger.error(f"RedisError occurred: {type(e).__name__}: {e}")
            await self.safe_send(message.channel, statics.db_error_embed)

    async def safe_send(self, channel, to_send):
        """Send a text / embed message to a user, and if an error occurs, safely
        supress it so the bot doesen't crash
        On success returns what the channel.send method returns
        On failure, returns:
            -1 : Message too big (string is >2k chars or len(embed) > 2048)
            -2 : Nothing to send (to_send is not a string or Embed)
            -3 : Forbidden (No permission to message this channel)
            -4 : HTTPException (API down, Message too big, etc.)
            -5 : InvalidArgument (Invalid channel ID / cannot "see" that channel)
        """
        try:
            if type(to_send) == str:
                if len(to_send) > 2000:
                    return -1
                return await channel.send(to_send)
            elif type(to_send) == discord.Embed:
                if len(to_send) > 2048:
                    return -1
                return await channel.send(embed=to_send)
            else:
                return -2
        except discord.errors.Forbidden:
            return -3
        except discord.errors.HTTPException:
            return -4
        except discord.errors.InvalidArgument:
            return -5


async def startup():
    await redis.init_defaults()


if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(startup())

    client = SpaceXLaunchBotClient()
    client.run(config.DISCORD_TOKEN)
