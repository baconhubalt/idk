import discord
from discord.ext import commands
import os
import sys
import logging
import asyncio
import threading
import time
from flask import Flask

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
    if member == bot.user:
        if before.channel is None and after.channel is not None:
            print(f"🔊 Bot joined {after.channel.name}")
        elif before.channel is not None and after.channel is None:
            print(f"🔇 Bot left {before.channel.name}")

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
        
        if not interaction.user.voice:
            await interaction.followup.send("❌ You need to be in a voice channel to use this command!", ephemeral=True)
            return
        
        voice_channel = interaction.user.voice.channel
        
        if interaction.guild.voice_client:
            if interaction.guild.voice_client.channel == voice_channel:
                await interaction.followup.send(f"✅ Already connected to **{voice_channel.name}**!", ephemeral=True)
                return
            else:
                await interaction.guild.voice_client.move_to(voice_channel)
                await interaction.followup.send(f"✅ Moved to **{voice_channel.name}**!", ephemeral=True)
                return
        
        await voice_channel.connect()
        await interaction.followup.send(f"✅ Joined **{voice_channel.name}**!", ephemeral=True)
        
    except discord.errors.NotFound:
        print("⚠️ Interaction expired - user may have closed the command")
    except discord.Forbidden:
        await interaction.followup.send("❌ I don't have permission to join that voice channel!", ephemeral=True)
    except Exception as e:
        print(f"❌ Join command error: {e}")
        try:
            await interaction.followup.send(f"❌ Failed to join: {str(e)}", ephemeral=True)
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
        await interaction.followup.send(f"✅ Left **{channel_name}**!", ephemeral=True)
        
    except discord.errors.NotFound:
        print("⚠️ Interaction expired - user may have closed the command")
    except Exception as e:
        print(f"❌ Leave command error: {e}")
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
        await interaction.followup.send("✅ Force disconnected from voice channel!", ephemeral=True)
        
    except Exception as e:
        print(f"❌ Disconnect command error: {e}")
        try:
            await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
        except:
            pass

@bot.event
async def on_error(event, *args, **kwargs):
    print(f"❌ Error in {event}: {sys.exc_info()}")

@bot.event
async def on_disconnect():
    print("⚠️ Bot disconnected from Discord")

@bot.event
async def on_resumed():
    print("✅ Bot reconnected to Discord")

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
        sys.exit(1)
