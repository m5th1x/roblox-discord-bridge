from flask import Flask, request, jsonify
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
intents.message_content = True
client = discord.Client(intents=intents)

chat_log = []
live_message_id = None

# ---------------- ROBLOX STORAGE ----------------
roblox_log = []

# ---------------- DISCORD READY ----------------
@client.event
async def on_ready():
    global live_message_id

    print(f"Logged in as {client.user}")

    channel = client.get_channel(CHANNEL_ID)

    msg = await channel.send("🎮 **ROBLOX LIVE CHAT LOADING...**")
    live_message_id = msg.id

    print("Live chat box created")

# ---------------- OPTIONAL: Discord messages (NOT chat injection, just logging) ----------------
@client.event
async def on_message(message):
    if message.author.bot:
        return

    # We can still log Discord messages if you want later
    pass

# ---------------- ROBLOX → DISCORD ----------------
@app.route("/roblox-to-discord", methods=["POST"])
def roblox_to_discord():
    data = request.json
    user = data.get("user")
    message = data.get("message")

    roblox_log.append(f"{user}: {message}")

    if len(roblox_log) > 15:
        roblox_log.pop(0)

    asyncio.run_coroutine_threadsafe(update_discord_message(), client.loop)

    return "OK", 200

# ---------------- UPDATE DISCORD MESSAGE ----------------
async def update_discord_message():
    global live_message_id

    if live_message_id is None:
        return

    channel = client.get_channel(CHANNEL_ID)
    if not channel:
        return

    try:
        msg = await channel.fetch_message(live_message_id)

        content = "🎮 **ROBLOX LIVE CHAT**\n\n"
        content += "\n".join(roblox_log)

        await msg.edit(content=content)

    except Exception as e:
        print("Update error:", e)

# ---------------- OPTIONAL: Discord → Roblox API ----------------
@app.route("/discord-messages", methods=["GET"])
def discord_messages():
    return jsonify([])

# ---------------- RUN FLASK ----------------
def run_flask():
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask).start()

# ---------------- RUN DISCORD BOT ----------------
client.run(TOKEN)