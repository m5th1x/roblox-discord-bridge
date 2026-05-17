from flask import Flask, request, jsonify
import discord
import threading
import os
import asyncio

app = Flask(__name__)

# ---------------- CONFIG ----------------
TOKEN = os.environ["DISCORD_TOKEN"]

# server-specific storage
server_config = {}  # guild_id -> channel_id
roblox_log = {}

live_message = {}

# ---------------- DISCORD SETUP ----------------
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

# ---------------- FLASK ----------------
@app.route("/")
def home():
    return "Bot Running", 200

# ---------------- /setup ----------------
@tree.command(name="setup", description="Show setup instructions")
async def setup(interaction: discord.Interaction):
    msg = """
🎮 **Roblox Bridge Setup**

1. Run `/chatchannel` in the channel you want chat logs sent to.
2. Copy your Render URL from your hosting dashboard.
3. Add Roblox scripts with that URL.

Then you're done!
"""
    await interaction.response.send_message(msg, ephemeral=True)

# ---------------- /chatchannel ----------------
@tree.command(name="chatchannel", description="Set this channel for Roblox chat logs")
async def chatchannel(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    channel_id = interaction.channel.id

    server_config[guild_id] = channel_id
    roblox_log[guild_id] = []

    await interaction.response.send_message(
        f"✅ This channel is now set for Roblox chat logs.",
        ephemeral=True
    )

# ---------------- DISCORD READY ----------------
@client.event
async def on_ready():
    await tree.sync()
    print(f"Logged in as {client.user}")
    print("Slash commands synced")

# ---------------- ROBLOX → DISCORD ----------------
@app.route("/roblox-to-discord", methods=["POST"])
def roblox_to_discord():
    data = request.json
    guild_id = data.get("guild_id")  # OPTIONAL if multi-server later
    user = data.get("user")
    message = data.get("message")

    # fallback: if no guild system yet, use first server
    if not server_config:
        return "No channel set", 200

    for gid, channel_id in server_config.items():

        if gid not in roblox_log:
            roblox_log[gid] = []

        roblox_log[gid].append(f"{user}: {message}")

        if len(roblox_log[gid]) > 15:
            roblox_log[gid].pop(0)

        asyncio.run_coroutine_threadsafe(
            update_message(gid),
            client.loop
        )

    return "OK", 200

# ---------------- UPDATE MESSAGE ----------------
async def update_message(guild_id):
    channel_id = server_config.get(guild_id)
    if not channel_id:
        return

    channel = client.get_channel(channel_id)
    if not channel:
        return

    try:
        content = "\n".join(roblox_log.get(guild_id, []))

        embed = discord.Embed(
            title="🎮 ROBLOX LIVE CHAT",
            description=content if content else "No messages yet...",
            color=0x00ffcc
        )

        embed.set_footer(text="Roblox ↔ Discord Bridge")

        # create or reuse message
        if guild_id not in live_message:
            msg = await channel.send(embed=embed)
            live_message[guild_id] = msg.id
        else:
            msg = await channel.fetch_message(live_message[guild_id])
            await msg.edit(embed=embed)

    except Exception as e:
        print("Update error:", e)

# ---------------- FLASK ----------------
def run_flask():
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask).start()

# ---------------- BOT ----------------
client.run(TOKEN)