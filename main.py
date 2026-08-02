#!/usr/bin/env python3
"""
ULTIMATE DISCORD RAID BOT - COMPLETE
ALL COMMANDS ARE SLASH COMMANDS (/)
NO CONFIRMATION REQUIRED FOR ANY COMMAND
"""

import discord
from discord.ext import commands
import asyncio
import random
import sys
import traceback
import io
import os

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("❌ ERROR: DISCORD_TOKEN environment variable not set!")
    print("Please set it in Railway: Settings → Variables")
    sys.exit(1)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
    help_command=None
)

dm_targets = []
whitelist = []
blacklist = []
whitelist_only = False
dm_log_channel_id = None
dm_forward_enabled = False

OWNER_ID = 1481722738451284161

voice_stay_tasks = {}

def trim_msg(text, max_len=1990):
    if not text:
        return ""
    if len(text) > max_len:
        return text[:max_len] + "..."
    return text

async def get_channel_by_id(channel_id):
    try:
        cid = int(channel_id)
        channel = bot.get_channel(cid)
        if channel is None:
            channel = await bot.fetch_channel(cid)
        return channel
    except:
        return None

def is_owner():
    async def predicate(interaction):
        if interaction.user.id == OWNER_ID:
            return True
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.\nOnly the bot owner can use this command.",
            ephemeral=True
        )
        return False
    return discord.app_commands.check(predicate)

def is_whitelisted():
    async def predicate(interaction):
        if interaction.user.id == OWNER_ID:
            return True
        if interaction.user.id in whitelist:
            return True
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.\nYou need to be whitelisted to use this command.",
            ephemeral=True
        )
        return False
    return discord.app_commands.check(predicate)

@bot.event
async def on_message(message):
    if isinstance(message.channel, discord.DMChannel) and message.author != bot.user:
        print(f"📩 DM from {message.author.name}: {message.content[:100]}")
        if dm_log_channel_id:
            log_channel = bot.get_channel(dm_log_channel_id)
            if log_channel:
                embed = discord.Embed(
                    title="📩 DM Received",
                    description=trim_msg(message.content, 4000),
                    color=discord.Color.blue()
                )
                embed.add_field(name="From", value=message.author.mention, inline=True)
                embed.add_field(name="ID", value=message.author.id, inline=True)
                embed.set_footer(text=f"Received at {message.created_at.strftime('%H:%M:%S')}")
                if dm_forward_enabled:
                    try:
                        await log_channel.send(embed=embed)
                        await log_channel.send(f"**{message.author}:** {message.content[:1900]}")
                    except:
                        await log_channel.send(embed=embed)
                else:
                    await log_channel.send(embed=embed)
        if message.content.lower() in ["!help", "help", "hi", "hello"]:
            await message.channel.send("👋 Hi! I'm a bot. Use /help for commands.")
        return
    if message.author == bot.user:
        return
    await bot.process_commands(message)

@bot.event
async def on_ready():
    print(f"\n{'='*50}")
    print(f"✅ Logged in as {bot.user} ({bot.user.id})")
    print(f"📡 Connected to {len(bot.guilds)} servers")
    print(f"{'='*50}\n")
    print("💀 RAID BOT!")
    print("  /help - Show all commands")
    print("  ⚠️ NO CONFIRMATION REQUIRED FOR ANY COMMAND!\n")
    print(f"👑 Bot Owner ID: {OWNER_ID}")
    print(f"📋 Whitelist: {len(whitelist)} users\n")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Failed to sync slash commands: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ You need **Administrator** permission.", ephemeral=True)
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send(f"❌ Missing argument. Use `/help`", ephemeral=True)
    elif isinstance(error, discord.Forbidden):
        await ctx.send("❌ I don't have permission to do that.", ephemeral=True)
    elif isinstance(error, discord.HTTPException):
        if "50035" in str(error) or "Must be 2000" in str(error):
            await ctx.send("❌ Message too long. Max 2000 characters.", ephemeral=True)
        elif "50278" in str(error):
            await ctx.send("❌ Cannot DM this user.", ephemeral=True)
        else:
            await ctx.send(f"❌ Discord error: {str(error)[:100]}", ephemeral=True)
    elif isinstance(error, commands.CheckFailure):
        await ctx.send("❌ You don't have permission to use this command.", ephemeral=True)
    else:
        await ctx.send(f"❌ Error: {str(error)[:100]}", ephemeral=True)
        print(f"Command error: {error}")

@bot.tree.command(name="ping", description="Check bot latency")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! {round(bot.latency * 1000)}ms")

@bot.tree.command(name="help", description="Show all commands")
async def slash_help(interaction: discord.Interaction):
    is_owner = interaction.user.id == OWNER_ID
    is_whitelisted = interaction.user.id in whitelist
    help_text = f"""
**💀 RAID BOT COMMANDS:**
⚠️ **NO CONFIRMATION REQUIRED FOR ANY COMMAND!**
**Your Status:** {'👑 **BOT OWNER**' if is_owner else '📋 **WHITELISTED**' if is_whitelisted else '❌ **NOT WHITELISTED**'}
Use `/ping` - Check latency
Use `/help` - Show this
"""
    await interaction.response.send_message(trim_msg(help_text))

if __name__ == "__main__":
    print("🔄 Connecting to Discord...")
    bot.run(TOKEN)
