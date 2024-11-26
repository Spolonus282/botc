'Bot for controlling moving users around in BOTC games'
import os
import asyncio
import discord
from discord import app_commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")
GUILD = os.getenv("DISCORD_GUILD")

client = discord.Client(intents=discord.Intents.all())
tree = app_commands.CommandTree(client=client)

CHANNELS: "dict[int, dict[str, discord.guild.GuildChannel]]" = {}

@client.event
async def on_ready():
    'event when the bot turns on'
    await tree.sync()

    CHANNELS.update({g.id:{c.name.lower():c for c in g.channels} for g in client.guilds})

    print(f'{client.user} has connected to {", ".join(str(g.id) for g in client.guilds)}')

@tree.command()
async def daytime(interaction:discord.Interaction):
    "Set the game to the day phase"

    night = CHANNELS[interaction.guild.id]["night"]

    await interaction.response.defer(thinking=True, ephemeral=True)

    for c in night.channels:
        await move_channel_members_to_day(interaction, c)

    await interaction.followup.send("Set the time to day")
    print(f"{interaction.guild_id}: set time to day")

async def move_channel_members_to_day(
        interaction:discord.Interaction,
        channel:"discord.guild.GuildChannel"
        ):
    "move a member of a guild to the night phase"
    for m in channel.members:
        await m.move_to(CHANNELS[interaction.guild.id]["town square"])
    await channel.delete()

@tree.command()
async def nighttime(interaction:discord.Interaction):
    "Set the game to the night phase"

    town_square = CHANNELS[interaction.guild.id]["town square"]

    await interaction.response.defer(thinking=True, ephemeral=True)

    for m in town_square.members:
        await move_member_to_night(interaction, m)

    await interaction.followup.send("Set the time to night")
    print(f"{interaction.guild_id}: set time to night")

async def move_member_to_night(interaction:discord.Interaction, member:discord.Member):
    "move a memer of a guild to the night phase"
    vc = await interaction.guild.create_voice_channel(
        f"{member.id}", category=CHANNELS[interaction.guild.id]["night"])
    await member.move_to(vc)

@tree.command()
async def vote_time(interaction:discord.Interaction, time:int=60, force:bool=False):
    "Send a message to call people back. Optionally force them back after timeout"

    chats = [c for n,c in CHANNELS[interaction.guild.id].items()
             if "room" in n and len(c.members) != 0]
    town_square = CHANNELS[interaction.guild.id]["town square"]

    if time < 0:
        for c in chats:
            for m in c.members:
                await m.move_to(town_square)
        await interaction.response.send_message("Called everyone back", ephemeral=True)
        return

    await interaction.response.defer(thinking=True, ephemeral=True)

    if time > 0:
        for c in chats:
            if force:
                await c.send(("Finish up conversations and head back to town square. "
                              f"You have {time} seconds. "
                              "If you are not back by then, you will be moved back."),
                              delete_after=time)
            else:
                await c.send(("Finish up conversations and head back to town square. "
                              f"You have {time} seconds."),
                              delete_after=time)
        await asyncio.sleep(time)

    if force:
        for c in chats:
            for m in c.members:
                await m.move_to(town_square)
        await interaction.followup.send("Called everyone back")
    else:
        await interaction.followup.send("The timer has expired")
    print(f"{interaction.guild_id}: triggered vote time for {time} seconds with force={force}")

@tree.command()
async def sync(interaction:discord.Interaction):
    "Trigger a command sync for the bot (dev only)"

    await interaction.response.defer(thinking=True, ephemeral=True)
    await tree.sync()
    print(f"{interaction.guild_id}: performed command sync")
    message = await interaction.followup.send("Synced commands", wait=True, silent=False)
    await message.delete(delay=2)

client.run(TOKEN)
