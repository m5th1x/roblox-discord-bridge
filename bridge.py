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

roblox_log = []
live_message_id = None
chat_active = False

# ---------------- DISCORD READY ----------------
@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

# ---------------- COMMAND: /rchat ----------------
@client.event
async def on_message(message):
    global live_message_id, chat_active

    if message.author.bot:
        return

    # COMMAND TRIGGER
    if message.content.lower() == "/rchat":
        chat_active = True

        channel = client.get_channel(CHANNEL_ID)

        msg = await channel.send("🎮 Loading Roblox Chat Session...")
        live_message_id = msg.id

        await update_discord_message()
        return

# ---------------- ROBLOX → DISCORD ----------------
@app.route("/roblox-to-discord", methods=["POST"])
def roblox_to_discord():
    data = request.json
    user = data.get("user")
    message = data.get("message")

    roblox_log.append(f"{user}: {message}")

    if len(roblox_log) > 15:
        roblox_log.pop(0)

    # Only update if /rchat was used
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
            title="🎮 ROBLOX LIVE CHAT (SESSION)",
            description=content if content else "No messages yet...",
            color=0x00ffcc
        )

        embed.set_footer(text="Type /rchat to load session")

        await msg.edit(embed=embed)

    except Exception as e:
        print("Update error:", e)

# ---------------- ROBLOX API ----------------
@app.route("/discord-messages", methods=["GET"])
def discord_messages():
    return jsonify([])

# ---------------- FLASK ----------------
def run_flask():
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port)

threading.Thread(target=run_flask).start()

# ---------------- BOT ----------------
client.run(TOKEN)