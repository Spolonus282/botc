'Bot for controlling moving users around in BOTC games'
import os
import asyncio
from uuid import uuid4

import discord
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")

bot = commands.Bot(command_prefix="!", intents=discord.Intents.all())

@bot.event
async def on_ready():
    'event when the bot turns on'
    guild: discord.guild.Guild = discord.utils.get(bot.guilds, id=int(GUILD))

    print(f'{bot.user} has connected to server {guild.name}')

@bot.tree.command()
async def summon(interaction: discord.Interaction, player: str):
    "Bring a user into the private chat"
    if player[0] == "<":
        user = interaction.guild.get_member(int(player[2:-1]))
    else:
        user = interaction.guild.get_member_named(player)

    role = interaction.guild.get_role(1085265560465584268)
    private_chat = interaction.guild.get_channel(1085265277597536416)

    if user is not None:
        await user.add_roles(role)
        await user.move_to(private_chat)
        await user.edit(mute=False)

        await interaction.response.send_message(f"Brought {player} to the chat", delete_after=5)
    else:
        sent = await interaction.response.send_message(
            f"Unable to summon {player}: Player doesn't exist", delete_after=5)
        await sent.delete(delay=5)

@bot.tree.command()
async def vacate(interaction: discord.Interaction, night: bool = True):
    "Remove all members from the private chat"

    role = interaction.guild.get_role(1085265560465584268)

    if night:
        to_chat = interaction.guild.get_channel(1127728166656557166)
    else:
        to_chat = interaction.guild.get_channel(1085264938722934907)

    for member in role.members:
        await member.move_to(to_chat)
        await member.remove_roles(role)

        if night:
            await member.edit(mute=True)

    await interaction.response.send_message("Cleared the chat", delete_after=5)

@bot.tree.command()
async def nighttime(interaction: discord.Interaction):
    "Set the game to the night phase"

    await interaction.response.defer(thinking=True)

    night_category =  interaction.guild.get_channel(1133025666846175303)

    public_chat = interaction.guild.get_channel(1085264938722934907)

    for member in public_chat.members:
        uid = uuid4().int

        channel = await interaction.guild.create_voice_channel(
            f"{uid}", category=night_category)
        await channel.set_permissions(interaction.guild.default_role,
                                      view_channel=False,
                                      connect=False)
        await channel.set_permissions(member, view_channel=True, connect=True)

        await member.move_to(channel)

    message = await interaction.followup.send(
        "Activated nighttime",
        wait=True, silent=False)
    await message.delete(delay=5)

@bot.tree.command()
async def daytime(interaction: discord.Interaction):
    "Set the game to the day phase"

    await interaction.response.defer(thinking=True)

    public_chat = interaction.guild.get_channel(1085264938722934907)

    night_category = interaction.guild.get_channel(1133025666846175303)

    for channel in night_category.channels:
        for member in channel.members:
            await member.move_to(public_chat)

        await channel.delete()

    message = await interaction.followup.send(
        "Activated daytime",
        wait=True, silent=False)
    await message.delete(delay=5)

@bot.tree.command()
async def vote_time(interaction: discord.Interaction, time: int = 30):
    """Sends a message preempting a move to start nominations
    Run with time = -1 to instantly summon all players back to the lobby"""

    room_one = interaction.guild.get_channel(1085266581371748453)
    room_two = interaction.guild.get_channel(1085266609192579185)
    room_three = interaction.guild.get_channel(1085266686787207290)
    public_chat = interaction.guild.get_channel(1085264938722934907)

    if time == -1:
        for member in room_one.members + room_two.members + room_three.members:
            await member.move_to(public_chat)

        await interaction.response.send_message("Players summoned to meeting", delete_after=5)
    else:
        await room_one.send(f"Voting time approaching in {time} seconds! Wrap up conversations",
                            delete_after=30)
        await room_two.send(f"Voting time approaching in {time} seconds! Wrap up conversations",
                            delete_after=30)
        await room_three.send(f"Voting time approaching in {time} seconds! Wrap up conversations",
                            delete_after=30)

        await interaction.response.defer(thinking=True)

        await asyncio.sleep(time)

        message = await interaction.followup.send(
            "Time has expired. Bring back all players? (run /vote_time -1>)",
            wait=True, silent=False)
        await message.delete(delay=10)

@bot.command(name="sync")
async def sync(context: commands.Context):
    "Sync the commands with discord (dev only)"

    await context.message.delete()

    await bot.tree.sync()

bot.tree.copy_global_to(guild=discord.Object(id=1085264938148307064))
bot.run(TOKEN)
