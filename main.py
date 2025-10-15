# main.py
import os
import logging
import threading
from dotenv import load_dotenv

import discord
from discord.ext import commands

# --- tiny keep-alive web server for Render ---
from flask import Flask
app = Flask(__name__)

@app.get("/")
def home():
    return "RLBot is alive!"

def run_keepalive():
    # Render provides PORT as an env var. Default to 8080 locally.
    port = int(os.environ.get("PORT", 8080))
    # Must bind to 0.0.0.0 so Render can reach it from outside the container.
    app.run(host="0.0.0.0", port=port)

# start the web server in a background thread
threading.Thread(target=run_keepalive, daemon=True).start()
# ------------------------------------------------

load_dotenv()  # optional locally; on Render we use env vars

TOKEN = os.getenv("DISCORD_TOKEN")
if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN missing")

logging.basicConfig(level=logging.INFO)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"We are ready, {bot.user.name}")

@bot.event
async def on_member_join(member: discord.Member):
    try:
        await member.send(f"Welcome to the server {member.name}")
    except discord.Forbidden:
        pass

@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if "shit" in message.content.lower():
        try:
            await message.delete()
            await message.channel.send(
                f"{message.author.mention} - dont use that word!",
                delete_after=6
            )
        except discord.Forbidden:
            pass
    await bot.process_commands(message)

@bot.command()
async def hello(ctx: commands.Context):
    await ctx.send(f"Hello {ctx.author.mention}!")

@bot.command()
async def assign(ctx: commands.Context, *, role: discord.Role):
    me = ctx.guild.me
    if role >= me.top_role:
        return await ctx.send(
            "I can’t assign that role because it’s above my highest role. "
            "Move my role above it in **Server Settings → Roles**."
        )
    allowed = {"🏆 RL Pro", "⚽ FUT Legend", "🎧 DJ", "💬 Regular"}
    if role.name not in allowed:
        return await ctx.send("That role isn’t self-assignable.")
    try:
        await ctx.author.add_roles(role, reason="Self-assign via !assign")
        await ctx.send(f"{ctx.author.mention} is now assigned to **{role.name}**.")
    except discord.Forbidden:
        await ctx.send("I’m missing **Manage Roles** permission.")

@bot.command()
async def unassign(ctx: commands.Context, *, role: discord.Role):
    if role not in ctx.author.roles:
        return await ctx.send("You don’t have that role.")
    try:
        await ctx.author.remove_roles(role, reason="Self-unassign via !unassign")
        await ctx.send(f"Removed **{role.name}** from {ctx.author.mention}.")
    except discord.Forbidden:
        await ctx.send("I’m missing **Manage Roles** permission.")

bot.run(TOKEN)
