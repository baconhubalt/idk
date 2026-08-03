import discord
from discord.ext import commands
import os
import sys
import logging
from flask import Flask
import threading

# Setup logging for Railway
logging.basicConfig(level=logging.INFO)

# Create a simple Flask app for Railway's health checks
app = Flask(__name__)

@app.route('/')
def health_check():
    return "Bot is running!", 200

def run_web_server():
    port = int(os.getenv('PORT', 8080))
    app.run(host='0.0.0.0', port=port)

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    print("ERROR: DISCORD_TOKEN not set!")
    sys.exit(1)

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

@bot.tree.command(name="ping", description="Check bot latency")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"Pong! {round(bot.latency * 1000)}ms")

@bot.tree.command(name="join", description="Make the bot join your voice channel")
async def join(interaction: discord.Interaction):
    if not interaction.user.voice:
        await interaction.response.send_message("❌ You need to be in a voice channel to use this command!", ephemeral=True)
        return
    
    voice_channel = interaction.user.voice.channel
    
    if interaction.guild.voice_client:
        if interaction.guild.voice_client.channel == voice_channel:
            await interaction.response.send_message(f"✅ Already connected to **{voice_channel.name}**!")
            return
        else:
            await interaction.guild.voice_client.move_to(voice_channel)
            await interaction.response.send_message(f"✅ Moved to **{voice_channel.name}**!")
            return
    
    try:
        await voice_channel.connect()
        await interaction.response.send_message(f"✅ Joined **{voice_channel.name}**!")
    except Exception as e:
        await interaction.response.send_message(f"❌ Failed to join: {str(e)}", ephemeral=True)

@bot.tree.command(name="leave", description="Make the bot leave the voice channel")
async def leave(interaction: discord.Interaction):
    if not interaction.guild.voice_client:
        await interaction.response.send_message("❌ I'm not in a voice channel!", ephemeral=True)
        return
    
    await interaction.guild.voice_client.disconnect()
    await interaction.response.send_message("✅ Left the voice channel!")

@bot.tree.command(name="status", description="Check bot's voice connection status")
async def status(interaction: discord.Interaction):
    voice_client = interaction.guild.voice_client
    
    if not voice_client or not voice_client.is_connected():
        await interaction.response.send_message("🔇 Not connected to any voice channel")
    else:
        channel = voice_client.channel
        await interaction.response.send_message(f"🔊 Connected to **{channel.name}**")

if __name__ == "__main__":
    print("🚀 Starting bot...")
    
    # Start web server in a separate thread
    web_thread = threading.Thread(target=run_web_server, daemon=True)
    web_thread.start()
    
    # Run the Discord bot
    bot.run(TOKEN)
