import os
import asyncio
import logging
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime

import discord
from discord.ext import tasks
from discord import app_commands
from mcstatus import JavaServer
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("TOKEN")

CHANNEL_ID = Your_Channel_ID_Here

SEASON = Your_Season_Here
RESTART_TIME = "Your_Restart_Time_Here"
STATUS_INTERVAL = 60
MC_TIMEOUT = 5

EMBED_COLOR = 0x2ECC71
OFFLINE_COLOR = 0xE74C3C

LOGO_URL = "Your_Logo_URL_Here"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
tree = app_commands.CommandTree(bot)

@dataclass
class ServerConfig:
    name: str
    host: str
    port: int
    max_players: int
    version: str

@dataclass
class ServerStatus:
    online: bool
    players_online: int = 0
    player_names: List[str] = None

SERVER = ServerConfig(
    name="Your_Server_Name_Here",
    host="Your_IP_Here",
    port=Your_Port_Here,
    max_players=Your_Max_Players_Here,
    version="Your_Version_Here"
)

def format_players(players: Optional[List[str]]) -> str:
    if not players:
        return "No players online"
    return ", ".join(players[:20])

async def fetch_status(server: ServerConfig) -> ServerStatus:
    try:
        mc = JavaServer(server.host, server.port)
        response = await asyncio.wait_for(
            asyncio.to_thread(mc.status),
            timeout=MC_TIMEOUT
        )

        return ServerStatus(
            online=True,
            players_online=response.players.online,
            player_names=[p.name for p in response.players.sample]
            if response.players.sample else []
        )
    except Exception:
        return ServerStatus(online=False, player_names=[])

def build_embed(status: ServerStatus) -> discord.Embed:
    online = status.online
    color = EMBED_COLOR if online else OFFLINE_COLOR

    embed = discord.Embed(
        title="Your_Server_Name • Server Status",
        description=f"**Season {SEASON}**",
        color=color,
        timestamp=datetime.utcnow()
    )

    embed.add_field(
        name="📡 Status",
        value="🟢 **Online**" if online else "🔴 **Offline**",
        inline=True
    )

    embed.add_field(
        name="👥 Players",
        value=f"`{status.players_online}/{SERVER.max_players}`" if online else "—",
        inline=True
    )

    embed.add_field(
        name="🧩 Version",
        value=SERVER.version,
        inline=True
    )

    embed.add_field(
        name="🌍 Server IP",
        value=f"`{SERVER.host}`",
        inline=False
    )

    embed.add_field(
        name="🔁 Next Restart",
        value=f"`{RESTART_TIME}`",
        inline=False
    )

    embed.add_field(
        name="🎮 Online Players",
        value=format_players(status.player_names) if online else "Server is offline",
        inline=False
    )

    embed.set_thumbnail(url=LOGO_URL)
    embed.set_footer(text="Live Server Monitor")

    return embed

@tasks.loop(seconds=STATUS_INTERVAL)
async def update_status_task():
    channel = bot.get_channel(CHANNEL_ID)
    if not channel:
        return

    status = await fetch_status(SERVER)
    embed = build_embed(status)

    if not hasattr(update_status_task, "message"):
        update_status_task.message = await channel.send(embed=embed)
    else:
        await update_status_task.message.edit(embed=embed)

@bot.event
async def on_ready():
    await tree.sync()
    logging.info(f"Bot logged in as {bot.user}")
    if not update_status_task.is_running():
        update_status_task.start()

bot.run(TOKEN)