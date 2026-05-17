from flask import Flask
import discord
import threading
import os
import asyncio

app = Flask(__name__)

# ---------------- CONFIG ----------------
TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = int(os.environ["DISCORD_CHANNEL_ID"])

# ---------------- DISCORD SETUP ----------------
intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = discord.app_commands.CommandTree(client)

roblox_log = []
live_message_id = None
chat_active = False

# ---------------- FLASK ----------------
@app.route("/")
def home():
    return "Bot Running", 200

# ---------------- DISCORD READY ----------------
@client.event
async def on_ready():
    await tree.sync()  # THIS registers slash commands
    print(f"Logged in as {client.user}")
    print("Slash commands synced")

# ---------------- /setup ----------------
@tree.command(name="setup", description="Setup the Roblox chat bridge")
async def setup(interaction: discord.Interaction):
    global chat_active, live_message_id

    chat_active = True
    live_message_id = None

    await interaction.response.send_message(
        "✅ Roblox bridge setup complete! Use /rchat to start live session.",
        ephemeral=True
    )

# ---------------- /rchat ----------------
@tree.command(name="rchat", description="Start live Roblox chat session")
async def rchat(interaction: discord.Interaction):
    global live_message_id, chat_active

    chat_active = True

    channel = client.get_channel(CHANNEL_ID)

    msg = await channel.send("🎮 Loading Roblox Live Chat Session...")
    live_message_id = msg.id

    await interaction.response.send_message(
        "🎮 Live chat session started!",
        ephemeral=True
    )

    await update_discord_message()

# ---------------- ROBLOX → DISCORD ----------------
@app.route("/roblox-to-discord", methods=["POST"])
def roblox_to_discord():
    data = discord.utils._json_loads(request.data)
    user = data.get("user")
    message = data.get("message")

    roblox_log.append(f"{user}: {message}")

    if len(roblox_log) > 15:
        roblox_log.pop(0)

    if chat_active:
        asyncio.run_coroutine_threadsafe(update_discord_message(), client.loop)

    return "OK", 200

# ---------------- UPDATE EMBED ----------------
async def update_discord_message():
    global live_message_id

    if live_message_id is None:
        return

    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        return

    try:
        msg = await channel.fetch_message(live_message_id)

        content = "\n".join(roblox_log)

        embed = discord.Embed(
            title="🎮 ROBLOX LIVE CHAT",
            description=content if content else "No messages yet...",
            color=0x00ffcc
        )

        embed.set_footer(text="Roblox ↔ Discord Bridge")

        await msg.edit(embed=embed)

    except Exception as e:
        print("Update error:", e)

# ---------------- RUN FLASK ----------------
def run_flask():
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask).start()

# ---------------- RUN BOT ----------------
client.run(TOKEN)