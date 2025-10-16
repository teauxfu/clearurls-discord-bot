import asyncio
import os
import re
import discord
import logging
from discord.ext import commands
from dotenv import load_dotenv
from unalix import clear_url
from prometheus_client import start_http_server, Summary, Counter, Gauge
from database.util import get_dbcon
from database.guildsettings import ensure_settings_table, get_automod_setting, set_automod_setting

class ClearUrlsBot(commands.Bot):
    async def setup_hook(self):
        with get_dbcon() as con:
            ensure_settings_table(con)
        con.close()

        synced = await self.tree.sync()
        logger.info(f"Synced {len(synced)} command(s)")
        
        self.loop.create_task(count_servers_members())

intents = discord.Intents.default()
intents.message_content = True
bot = ClearUrlsBot(command_prefix="/", intents=intents, activity=discord.Activity(type=discord.ActivityType.watching, name='for tracking links'));

logger = logging.getLogger(__name__)

process_message_time = Summary('process_message_time', 'Time spent processing message')
process_react_time = Summary('process_react_time', 'Time spent processing react')
messages = Counter('messages', 'Total number of messages processed')
cleaned_messages = Counter('cleaned_messages', 'Number of messages with tracking links cleaned')
deleted_messages = Counter('deleted_messages', 'Number of cleaned messages that were deleted with the trash react')
servers = Gauge('servers', 'Number of servers the bot is in')
members = Gauge('members', 'Combined member count of all servers the bot is in')

async def count_servers_members():
    while True:
        servers.set(len(bot.guilds))
        members.set(sum([guild.member_count for guild in bot.guilds]))
        await asyncio.sleep(60)

@process_message_time.time()
@bot.event
async def on_message(message: discord.Message):
    messages.inc()
    permissions = message.channel.permissions_for(message.guild.me)
    can_add_reactions = (permissions.add_reactions 
                         and permissions.read_message_history 
                         and permissions.manage_messages)
    if message.author == bot.user:
        # Suppress embeds for bot messages if unable to suppress embeds for original message to avoid visual clutter
        if not permissions.manage_messages:
            await message.edit(suppress=True)
        # Add :wastebasket: emoji for easy deletion if necessary, but not for responses to slash commands (check for interaction metadata)
        message_is_command_response = message.interaction_metadata is not None
        if can_add_reactions and not message_is_command_response:
            await message.add_reaction('🗑')
    # Though this else is not necessary since the bot should never send
    # links with tracking parameters, include it anyways to be safe
    # against infinite recursion
    else:
        # Extract links and clean
        urls = re.findall('(?P<url>https?://[^\s]+)', message.content)
        cleaned = []
        for url in urls:
            # Ignore trailing & in comparing, as these are not used for tracking
            # This is to fix a bug where right clicking on an image in the Discord *app* (not browser) > Copy Link on context menu would create a link ending in &
            # Pasting this link into Discord would then trigger the bot since the cleaned link removed the &, even though the image link didn't have tracking parameters
            if clear_url(url).strip('&') != url.strip('&'):
                cleaned.append(clear_url(url))

        if not cleaned:
            return
        
        with get_dbcon() as con:
            should_replace_message = get_automod_setting(con, message.guild.id)
        con.close()
        # there are two paths we can take in response
        # if the automod setting is disabled we simply add a new message with the links removed
        whats_this = f"([what's this?](https://danielzting.github.io/clearurls-discord-bot/))"
        if not should_replace_message:
            # Suppress embeds for original message to avoid visual clutter
            if permissions.manage_messages:
                await message.edit(suppress=True)
            # Send message and add reactions
            text = f"It appears that you have sent one or more links with tracking parameters. Below are the same links with those fields removed {whats_this}:\n{"\n".join(cleaned)}"
            await message.reply(text, mention_author=False, silent=True)
        else :
            # if the automod setting is enabled we delete the offending message and repost the cleaned one
            cleaned_content = message.content
            for url in urls:
                cleaned_content = cleaned_content.replace(url, clear_url(url))
            text = f"User {message.author.mention} sent the following message, which was deleted and has automatically been cleaned from tracking links {whats_this}:\n\n{cleaned_content}"
            await message.reply(text, mention_author=False, silent=True)
            await message.delete()
            deleted_messages.inc()

        cleaned_messages.inc()

@process_react_time.time()
@bot.event
async def on_raw_reaction_add(payload: discord.RawReactionActionEvent):
    # Delete messages if the original sender clicks the trash can react
    if payload.emoji.name != '🗑' or payload.user_id == bot.user.id:
        return

    channel = await bot.fetch_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    original_author = message.mentions[0];
    if message.reference is None or message.author != bot.user:
        return

    # determine if the user reacting is the one whose message we are working with
    permissions = message.channel.permissions_for(message.guild.me)
    original_channel = await bot.fetch_channel(message.reference.channel_id)
    reacting_user = await bot.fetch_user(payload.user_id)
    # before we check the API to do this "auth check", see if this is a message we deleted
    if permissions.manage_messages and original_author.id == reacting_user.id:
        await message.delete()
        deleted_messages.inc()
        return
    
    # it doesn't look like this is a message we deleted during automod, so check the API
    original_message = await original_channel.fetch_message(message.reference.message_id)
    if permissions.manage_messages and original_message.author == reacting_user:
        await message.delete()
        deleted_messages.inc()
        logger.info(f"Deleted message {message.id} via reaction by user {payload.user_id}")

@bot.tree.command(name="linkautomod", description="Enable or disable automatic delete/repost of messages with dirty links removed")
@commands.has_permissions(administrator=True)
@commands.guild_only()
async def set_automod_behavior(interaction: discord.Interaction, enabled: bool):
    """Enable or disable link automoderation for this server"""
    
    # check if user is guild owner or bot owner
    is_guild_owner = interaction.guild.owner_id == interaction.user.id
    
    if not (is_guild_owner):
        await interaction.response.send_message("❌ You must be the server owner to use this command.", ephemeral=True)
        return
    
    try:
        with get_dbcon() as con:
            set_automod_setting(con, interaction.guild.id, enabled)
        con.close()
        status = "enabled" if enabled else "disabled"
        await interaction.response.send_message(f"✅ Link automod has been **{status}** for this server.")
        logger.info(f"set replace messages setting to {status} for {interaction.guild.id}")
        
    except Exception as e:
        await interaction.response.send_message(f"❌ An error occurred: {str(e)} \n\n You can open a bug report [here](https://github.com/danielzting/clearurls-discord-bot/issues) 🪳", ephemeral=True)
        logger.exception(f"Error in linkautomod command: {e}", e)

if __name__ == '__main__':
    start_http_server(8000)
    load_dotenv()
    bot.run(os.environ['TOKEN'])
