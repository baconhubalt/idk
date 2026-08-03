import discord
from discord.ext import commands
import os
import sys
import logging

# Setup logging for Railway
logging.basicConfig(level=logging.INFO)

# Print ALL environment variables for debugging
print("📋 ALL ENVIRONMENT VARIABLES:")
for key in sorted(os.environ.keys()):
    if "TOKEN" in key.upper() or "KEY" in key.upper() or "SECRET" in key.upper():
        # Mask sensitive values
        value = os.environ[key]
        masked = f"{value[:5]}...{value[-5:]}" if len(value) > 10 else "***"
        print(f"  {key} = {masked}")
    else:
        print(f"  {key} = {os.environ[key]}")

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
    print("🔍 Checked: DISCORD_TOKEN, token, TOKEN, DISCORD_TOKEN_SHARED, RAILWAY_TOKEN, DISCORD")
    sys.exit(1)

# Mask the token for security (show only first/last few chars)
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
    try:
        bot.run(TOKEN)
    except discord.LoginFailure as e:
        print(f"❌ Login failed: {e}")
        print("Please check your token is valid")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
