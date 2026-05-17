from flask import Flask, request, jsonify
import discord
import threading
import os

app = Flask(__name__)

# ---------------- CONFIG ----------------
TOKEN = os.environ["DISCORD_TOKEN"]
CHANNEL_ID = int(os.environ["DISCORD_CHANNEL_ID"])

# ---------------- DISCORD BOT ----------------
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

message_buffer = []

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    if message.author.bot:
        return

    message_buffer.append({
        "user": message.author.name,
        "message": message.content
    })

    if len(message_buffer) > 50:
        message_buffer.pop(0)

# ---------------- ROBLOX → DISCORD ----------------
@app.route("/roblox-to-discord", methods=["POST"])
def roblox_to_discord():
    data = request.json
    user = data.get("user")
    message = data.get("message")

    channel = client.get_channel(CHANNEL_ID)

    if channel:
        asyncio = __import__("asyncio")
        asyncio.run_coroutine_threadsafe(
            channel.send(f"🎮 {user}: {message}"),
            client.loop
        )

    return "OK", 200

# ---------------- DISCORD → ROBLOX ----------------
@app.route("/discord-messages", methods=["GET"])
def discord_messages():
    return jsonify(message_buffer)

# ---------------- START FLASK ----------------
def run_flask():
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask).start()

# ---------------- START DISCORD ----------------
client.run(TOKEN)