import asyncio
from pyrogram import Client, enums
api_id = 25960001
api_hash = "86da715ea0ed76925b740c209710626f"

async def vecher_v_hatu(chat_id):
    async with Client("project_hockey", api_id, api_hash) as app:
        returned_list = []
        async for member in app.get_chat_members(chat_id):
            if member.user.is_bot:
                continue
            returned_list.append([member.user.id, member.user.first_name, '@'+member.user.username])
        return returned_list



