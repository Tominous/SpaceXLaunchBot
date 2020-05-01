from typing import Dict

import aiohttp

import config


async def _post_count_to_bot_list(bl_data: Dict[str, str], guild_count: int) -> None:
    async with aiohttp.ClientSession() as session:
        await session.post(
            bl_data["url"],
            json={bl_data["guild_count_parameter"]: guild_count},
            headers={
                "Authorization": bl_data["token"],
                "Content-Type": "application/json",
            },
        )


async def post_all_bot_lists(guild_count: int) -> None:
    for d in config.BOT_LIST_DATA:
        await _post_count_to_bot_list(d, guild_count)
