import discord
from discord.ext import commands
import os
import sys
import logging
import asyncio
import threading
import time
import traceback
from flask import Flask

# Enable detailed voice logging
discord.utils.setup_logging(level=logging.DEBUG)
logging.getLogger("discord.voice_state").setLevel(logging.DEBUG)
logging.getLogger("discord.voice_client").setLevel(logging.DEBUG)

# Setup logging for Railway
logging.basicConfig(level=logging.INFO)

# Create a simple Flask app for Railway's health checks
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

# Try multiple possible variable names
TOKEN = (
    os.getenv("DISCORD_TOKEN") or 
    os.getenv("token") or 
    os.getenv("TOKEN") or
    os.getenv("DISCORD_TOKEN_SHARED") or
    os.getenv("RAILWAY_TOKEN") or
    os.getenv("DISCORD")
)

if not TOKEN:
    print("❌ ERROR: No token found!")
    sys.exit(1)

# Mask the token for security
token_preview = f"{TOKEN[:5]}...{TOKEN[-5:]}" if len(TOKEN) > 10 else "***"
print(f"✅ Token found: {token_preview}")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True
intents.voice_states = True

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print(f"✅ Connected to {len(bot.guilds)} servers")
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands")
    except Exception as e:
        print(f"❌ Failed to sync: {e}")

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
async def on_error(event, *args, **kwargs):
    print(f"❌ Error in {event}: {sys.exc_info()}")
    traceback.print_exc()

@bot.event
async def on_disconnect():
    print("⚠️ Bot disconnected from Discord")

@bot.event
async def on_resumed():
    print("✅ Bot reconnected to Discord")

@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    try:
        await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)}ms")
    except Exception as e:
        print(f"❌ Ping command error: {e}")

@bot.tree.command(name="join", description="Make the bot join your voice channel")
async def join(interaction: discord.Interaction):
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
                    traceback.print_exc()
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
        
    except discord.errors.NotFound:
        print("⚠️ Interaction expired - user may have closed the command")
    except Exception as e:
        print(f"❌ Join command error: {e}")
        traceback.print_exc()
        try:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        except:
            pass

@bot.tree.command(name="leave", description="Make the bot leave the voice channel")
async def leave(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.guild.voice_client:
            await interaction.followup.send("❌ I'm not in a voice channel!", ephemeral=True)
            return
        
        channel_name = interaction.guild.voice_client.channel.name
        await interaction.guild.voice_client.disconnect()
        print(f"🔇 Bot left {channel_name}")
        await interaction.followup.send(f"✅ Left **{channel_name}**!", ephemeral=True)
        
    except discord.errors.NotFound:
        print("⚠️ Interaction expired - user may have closed the command")
    except Exception as e:
        print(f"❌ Leave command error: {e}")
        traceback.print_exc()
        try:
            await interaction.followup.send(f"❌ Failed to leave: {str(e)}", ephemeral=True)
        except:
            pass

@bot.tree.command(name="status", description="Check bot's voice connection status")
async def status(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True)
        voice_client = interaction.guild.voice_client
        
        if not voice_client or not voice_client.is_connected():
            await interaction.followup.send("🔇 Not connected to any voice channel", ephemeral=True)
        else:
            channel = voice_client.channel
            members = len(channel.members)
            await interaction.followup.send(f"🔊 Connected to **{channel.name}** ({members} members)", ephemeral=True)
            
    except discord.errors.NotFound:
        print("⚠️ Interaction expired - user may have closed the command")
    except Exception as e:
        print(f"❌ Status command error: {e}")
        traceback.print_exc()
        try:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        except:
            pass

@bot.tree.command(name="disconnect", description="Force disconnect from voice (admin)")
async def disconnect(interaction: discord.Interaction):
    try:
        await interaction.response.defer(ephemeral=True)
        
        if not interaction.user.guild_permissions.administrator:
            await interaction.followup.send("❌ You need administrator permissions to use this command!", ephemeral=True)
            return
        
        if not interaction.guild.voice_client:
            await interaction.followup.send("❌ I'm not in a voice channel!", ephemeral=True)
            return
        
        await interaction.guild.voice_client.disconnect(force=True)
        print("🔇 Force disconnected by admin")
        await interaction.followup.send("✅ Force disconnected from voice channel!", ephemeral=True)
        
    except Exception as e:
        print(f"❌ Disconnect command error: {e}")
        traceback.print_exc()
        try:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        except:
            pass

if __name__ == "__main__":
    print("🚀 Starting bot...")
    
    # Start web server in a separate thread
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    print(f"✅ Web server started on port {os.getenv('PORT', 8080)}")
    
    try:
        bot.run(TOKEN, reconnect=True)
    except discord.LoginFailure as e:
        print(f"❌ Login failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        traceback.print_exc()
        sys.exit(1)
