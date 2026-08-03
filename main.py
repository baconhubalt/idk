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
import logging
import os
import time
import threading
from flask import Flask

# Setup logging
logging.basicConfig(level=logging.INFO)

# Flask app for Railway health checks
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running!", 200

@app.route('/health')
def health():
    return {"status": "healthy"}, 200

def run_web_server():
    port = int(os.getenv('PORT', 8080))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=False,
        use_reloader=False,
        threaded=True
    )

# Get token from environment variable
TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("❌ ERROR: DISCORD_TOKEN environment variable not set!")
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

# ===== YOUR DISCORD USER ID =====
OWNER_ID = 1481722738451284161  # <--- YOUR CORRECT USER ID

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

# ===== PERMISSION CHECKS =====
def is_owner():
    async def predicate(interaction):
        if interaction.user.id == OWNER_ID:
            return True
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.\n"
            "Only the bot owner can use this command.",
            ephemeral=True
        )
        return False
    return discord.app_commands.check(predicate)

def is_whitelisted():
    async def predicate(interaction):
        # Bot owner can always use commands
        if interaction.user.id == OWNER_ID:
            return True
        # Check whitelist
        if interaction.user.id in whitelist:
            return True
        await interaction.response.send_message(
            "❌ You don't have permission to use this command.\n"
            "You need to be whitelisted to use this command.",
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
async def on_voice_state_update(member, before, after):
    """Log voice state changes for debugging"""
    if member.id == bot.user.id:
        print(f"🔊 VOICE: {before.channel} -> {after.channel}")
        if before.channel is None and after.channel is not None:
            print(f"✅ Bot joined {after.channel.name}")
        elif before.channel is not None and after.channel is None:
            print(f"❌ Bot left {before.channel.name}")

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

# ========================================
# ===== VOICE COMMANDS =====
# ========================================

@bot.tree.command(name="join", description="Make the bot join your voice channel")
@is_whitelisted()
async def slash_join(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True)
        
        # Check if user is in a voice channel
        if not interaction.user.voice:
            await interaction.followup.send("❌ You need to be in a voice channel to use this command!", ephemeral=True)
            return
        
        voice_channel = interaction.user.voice.channel
        
        # Check permissions
        permissions = voice_channel.permissions_for(interaction.guild.me)
        if not permissions.connect:
            await interaction.followup.send("❌ I don't have permission to connect to that voice channel!", ephemeral=True)
            return
        if not permissions.speak:
            await interaction.followup.send("❌ I don't have permission to speak in that voice channel!", ephemeral=True)
            return
        
        # Check existing voice client
        voice_client = interaction.guild.voice_client
        
        if voice_client:
            # If already connected and in the same channel
            if voice_client.is_connected() and voice_client.channel == voice_channel:
                await interaction.followup.send(f"✅ Already connected to **{voice_channel.name}**!", ephemeral=True)
                return
            
            # If connected to a different channel, move
            if voice_client.is_connected():
                try:
                    await voice_client.move_to(voice_channel)
                    await interaction.followup.send(f"✅ Moved to **{voice_channel.name}**!", ephemeral=True)
                    return
                except Exception as e:
                    print(f"❌ Move error: {e}")
                    # Try disconnecting and reconnecting
                    try:
                        await voice_client.disconnect(force=True)
                    except:
                        pass
            else:
                # Stale client, clean it up
                try:
                    await voice_client.disconnect(force=True)
                except:
                    pass
        
        # Connect to voice channel with timeout
        try:
            print(f"🔊 Attempting to connect to {voice_channel.name}...")
            await asyncio.wait_for(
                voice_channel.connect(
                    reconnect=True,
                    self_deaf=False,
                    self_mute=False
                ),
                timeout=30
            )
            print(f"✅ Successfully connected to {voice_channel.name}")
            await interaction.followup.send(f"✅ Joined **{voice_channel.name}**!", ephemeral=True)
            
        except asyncio.TimeoutError:
            print("❌ Voice connection timed out")
            await interaction.followup.send("❌ Timed out while connecting to the voice channel.", ephemeral=True)
        except discord.Forbidden:
            await interaction.followup.send("❌ I don't have permission to join that voice channel!", ephemeral=True)
        except Exception as e:
            print(f"❌ Voice connection error: {e}")
            traceback.print_exc()
            await interaction.followup.send(f"❌ Failed to join: {str(e)}", ephemeral=True)
        
    except Exception as e:
        print(f"❌ Join command error: {e}")
        traceback.print_exc()
        try:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        except:
            pass

@bot.tree.command(name="leave", description="Make the bot leave the voice channel")
@is_whitelisted()
async def slash_leave(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.guild.voice_client:
            await interaction.followup.send("❌ I'm not in a voice channel!", ephemeral=True)
            return
        
        channel_name = interaction.guild.voice_client.channel.name
        await interaction.guild.voice_client.disconnect()
        print(f"🔇 Bot left {channel_name}")
        await interaction.followup.send(f"✅ Left **{channel_name}**!", ephemeral=True)
        
    except Exception as e:
        print(f"❌ Leave command error: {e}")
        traceback.print_exc()
        try:
            await interaction.followup.send(f"❌ Failed to leave: {str(e)}", ephemeral=True)
        except:
            pass

@bot.tree.command(name="voicekick", description="Kick a user from voice channel")
@is_whitelisted()
async def slash_voicekick(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer(ephemeral=True)
    if not member.voice:
        await interaction.followup.send(f"❌ {member.mention} is not in a voice channel.", ephemeral=True)
        return
    try:
        await member.move_to(None)
        await interaction.followup.send(f"👢 Kicked {member.mention} from voice channel.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="voicemoveall", description="Move ALL users to a specific voice channel")
@is_whitelisted()
async def slash_voicemoveall(interaction: discord.Interaction, channel: discord.VoiceChannel):
    await interaction.response.defer(ephemeral=True)
    count = 0
    for vc in interaction.guild.voice_channels:
        if vc == channel:
            continue
        for member in vc.members:
            try:
                await member.move_to(channel)
                count += 1
                await asyncio.sleep(0.05)
            except:
                pass
    await interaction.followup.send(f"✅ Moved {count} users to {channel.name}", ephemeral=True)

@bot.tree.command(name="voicedisconnectall", description="Disconnect ALL users from voice channels")
@is_whitelisted()
async def slash_voicedisconnectall(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    count = 0
    for channel in interaction.guild.voice_channels:
        for member in channel.members:
            try:
                await member.move_to(None)
                count += 1
                await asyncio.sleep(0.05)
            except:
                pass
    await interaction.followup.send(f"✅ Disconnected {count} users from voice channels.", ephemeral=True)

# ========================================
# ===== REST OF YOUR COMMANDS GO HERE =====
# ========================================
# (All your existing commands - ghostping, say, nuke, banall, etc.)
# I'm omitting them for brevity but they should all be here

# ========================================
# ===== RUN =====
# ========================================
if __name__ == "__main__":
    print("""
╔═══════════════════════════════════════════════════════════════╗
║         RAID BOT - SLASH COMMANDS                          ║
║        ALL COMMANDS USE /                                  ║
║        WHITELIST SYSTEM ENABLED                           ║
╚═══════════════════════════════════════════════════════════════╝
""")

    # Start web server for Railway
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    print(f"✅ Web server started on port {os.getenv('PORT', 8080)}")

    try:
        print("🔄 Connecting to Discord...")
        bot.run(TOKEN)
    except discord.LoginFailure:
        print("❌ TOKEN INVALID! Go to Developer Portal → Reset Token")
    except discord.PrivilegedIntentsRequired:
        print("❌ ENABLE INTENTS! Enable: ✅ Message Content Intent")
    except Exception as e:
        print(f"\n❌ ERROR: {e}\n")
        traceback.print_exc()
