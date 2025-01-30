import nextcord
from nextcord.ext import tasks, commands
import json
from mcstatus import JavaServer
from flask import Flask
from threading import Thread
from collections import defaultdict
import asyncio
import os  # Import os untuk environment variables
MC_PC_IP = os.getenv("MC_PC_IP", "Hidden")
MC_PC_PORT = os.getenv("MC_PC_PORT", "Hidden")
MC_PE_IP = os.getenv("MC_PE_IP", "Hidden")
MC_PE_PORT = os.getenv("MC_PE_PORT", "Hidden")

# Gunakan environment variables
TOKEN = os.getenv("TOKEN")  
SERVER_IP = os.getenv("SERVER_IP", "25.ip.gl.ply.gg")  
SERVER_PORT = int(os.getenv("SERVER_PORT"))  
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))

intents = nextcord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

status_message = None
current_status = "Unknown"
DB_FILE = "player_times.json"
player_times = defaultdict(int)

def load_player_times():
    global player_times
    try:
        with open(DB_FILE, "r") as f:
            data = json.load(f)
            for player, time in data.items():
                player_times[player] = time
    except FileNotFoundError:
        print("File database JSON tidak ditemukan, menggunakan data awal.")
        save_player_times()

def save_player_times():
    with open(DB_FILE, "w") as f:
        json.dump(player_times, f, indent=4)

async def get_server_status():
    global player_times
    try:
        server = JavaServer.lookup(f"{SERVER_IP}:{SERVER_PORT}")
        status = server.status()
        current_players = {player.name for player in status.players.sample} if status.players.sample else set()
        for player in current_players:
            player_times[player] += 60  
        save_player_times()

        player_list = ', '.join(current_players) if current_players else "Tidak ada pemain yang online"
        sorted_players = sorted(player_times.items(), key=lambda x: x[1], reverse=True)
        leaderboard_message = "**Player Time Leaderboard**\n"
        for rank, (player, time) in enumerate(sorted_players[:5], start=1):
            hours, remainder = divmod(time, 3600)
            minutes, seconds = divmod(remainder, 60)
            leaderboard_message += f"{rank}. {player}: {hours}h {minutes}m {seconds}s\n"

        return f"🟢 Server Minecraft online!\nPemain Online: {status.players.online}/{status.players.max}\nPemain yang sedang online: {player_list}\n\n{leaderboard_message}"
    except Exception:
        return "🔴 Server Minecraft offline."

@bot.slash_command(name="servermc", description="Menampilkan rincian server Minecraft")
async def servermc(interaction: nextcord.Interaction):
    message_content = f"""
    **Minecraft Server TMJeh**
    Minecraft PC: {MC_PC_IP}:{MC_PC_PORT}
    Minecraft PE: {MC_PE_IP} Port: {MC_PE_PORT}
    Status: {current_status}
    Server Version: 1.21.3 - 1.21.4
    Yang raid bakal diganyang
    """
    await interaction.response.send_message(content=message_content)

@bot.slash_command(name="pingmc", description="Cek ping server Minecraft")
async def pingmc(interaction: nextcord.Interaction):
    try:
        server = JavaServer.lookup(f"{SERVER_IP}:{SERVER_PORT}")
        latency = server.ping()
        await interaction.response.send_message(content=f"🏓 Ping ke server Minecraft: {latency:.2f} ms")
    except Exception:
        await interaction.response.send_message(content="⚠️ Tidak dapat menghubungi server Minecraft untuk ping.")

@tasks.loop(seconds=60)
async def check_server_status():
    global status_message, current_status
    new_status = await get_server_status()
    current_status = new_status
    channel = bot.get_channel(CHANNEL_ID)
    if channel is None:
        print("Channel tidak ditemukan. Pastikan ID saluran sudah benar.")
        return
    if status_message is None:
        status_message = await channel.send(new_status)
    else:
        await status_message.edit(content=new_status)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    load_player_times()
    check_server_status.start()

# Flask Server
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run():
    app.run(host="0.0.0.0", port=8080)

def run_bot():
    bot.run(TOKEN)

# Jalankan Flask & Bot di thread masing-masing
Thread(target=run_bot).start()
Thread(target=run).start()
