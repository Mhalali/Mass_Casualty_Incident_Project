import discord
from discord.ext import commands, tasks
import os
import openai
import asyncio
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Set up OpenAI API key
openai.api_key = OPENAI_API_KEY

# Set up Discord bot with intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.guilds = True
intents.members = True  # Required for assigning roles
bot = commands.Bot(command_prefix="!", intents=intents)

# Dictionary to track user's current game stage, start time, and strikes
user_game_status = {}
inactive_timeouts = {}  # To track last active time for each user
user_timers = {}  # Track timers for warnings and resets
user_strikes = {}  # Track user strikes for inappropriate behavior

# Inappropriate triggers that will count towards strikes
trigger_phrases = ["nap", "ignore", "kill all", "quit"]

# Hospital setup
hospitals = {
    "Rashid Hospital Trauma Center": "Helicopter pad available, full ER capabilities.",
    "Latifa Hospital": "No helipad, limited ER.",
    "Dubai Hospital": "Helipad available, limited ER.",
    "Al Jalila Children?s Hospital": "No helipad, ER only for children."
}

# GPT response function (focused on playing along naturally)
def generate_gpt_response(user_input, game_status):
    try:
        prompt = f"The player said: '{user_input}'. React and guide the player in a Mass Casualty Incident simulation. Current situation: {game_status}"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an AI orchestrating a Mass Casualty Incident simulation. Play along with the player and make the scenario immersive."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return "There was an error generating a response."

# Assign roles to new players
async def assign_role(member):
    available_roles = ["Commander", "Triage Leader", "Transport Leader", "Safety Officer", "Treatment Leader"]
    assigned_role = random.choice(available_roles)
    
    role = discord.utils.get(member.guild.roles, name=assigned_role)
    if role:
        await member.add_roles(role)
        return assigned_role
    return None

# Organic game flow without predefined stages
async def run_game_flow(channel, member, user_input):
    user_id = member.id
    game_status = user_game_status.get(user_id, "A car accident has occurred, and you're part of the medical team arriving on the scene.")
    
    # Generate dynamic GPT response
    gpt_response = generate_gpt_response(user_input, game_status)
    
    # Update game status based on GPT's response
    user_game_status[user_id] = gpt_response
    await channel.send(f"**GPT Response**: {gpt_response}")

# Warning and inactivity handling
async def start_inactivity_timer(channel, user_id):
    user_timers[user_id] = 600  # Timer set to 10 minutes (600 seconds)
    while user_timers[user_id] > 0:
        await asyncio.sleep(1)
        user_timers[user_id] -= 1
        
        if user_timers[user_id] == 60:  # Warn when 1 minute is left
            await channel.send(f"Warning: You have 1 minute left to respond.")

    # End game if timer reaches 0
    if user_timers[user_id] == 0:
        await channel.send(f"Your time is up. The game will reset.")
        # Send logs to `session-logs` and `report-logs`
        session_logs_channel = discord.utils.get(channel.guild.channels, name="session-logs")
        report_logs_channel = discord.utils.get(channel.guild.channels, name="report-logs")
        if session_logs_channel:
            await session_logs_channel.send(f"Session for <@{user_id}> ended due to inactivity. Summary: (transcript)")
        if report_logs_channel:
            await report_logs_channel.send(f"Performance analysis for <@{user_id}>: Could improve responsiveness and task handling.")
        
        # Send DM to user
        user = bot.get_user(user_id)
        if user:
            await user.send(f"Your session has ended due to inactivity. Check the logs for details. For more information, visit: [GitHub link]")

        # Reset the game status
        user_game_status.pop(user_id, None)
        inactive_timeouts.pop(user_id, None)
        user_timers.pop(user_id, None)

# Handle end game based on the number of players
async def handle_end_game(message, user_id, is_multi_player=False):
    if is_multi_player:
        if "GameMaster" in [role.name for role in message.author.roles]:
            await message.channel.send(f"Game ended by GameMaster.")
            await restart_game(message)
        else:
            await message.channel.send(f"Only the GameMaster can end the game in multiplayer mode.")
    else:
        await message.channel.send(f"Game ended.")
        await restart_game(message)

# Event: User sends a message in the #demo channel
@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.id == 159985870458322944:  # Ignore bot and MEE6
        return

    # Check if the message is "end game"
    if message.content.lower() == "end game":
        is_multi_player = len(message.channel.members) > 1
        await handle_end_game(message, message.author.id, is_multi_player)
        return
    
    # If a user sends a message in the #demo channel
    if message.channel.name == 'demo':
        user_id = message.author.id

        # Check if user is starting a new game or continuing
        if user_id not in user_game_status:
            role_assigned = await assign_role(message.author)
            user_game_status[user_id] = "You are part of the medical team responding to a car accident."
            await message.channel.send(f"Welcome, {message.author.mention}, to the Mass Casualty Incident Simulation Demo! You have been assigned the role: **{role_assigned}**.")
            await asyncio.sleep(5)
            await message.channel.send("You receive a debrief: You're heading to the site of a severe accident. There's chaos, and victims require immediate attention. What will you do first?")
            await start_inactivity_timer(message.channel, user_id)  # Start the inactivity timer
        else:
            # Continue the game flow based on user input
            await run_game_flow(message.channel, message.author, message.content)
            # Reset timer
            if user_id in user_timers:
                user_timers[user_id] = 600  # Reset to 10 minutes
        
        # Update last active time
        inactive_timeouts[user_id] = asyncio.get_event_loop().time()

    # Process other commands or responses normally
    await bot.process_commands(message)

# Command to restart the game
@bot.command(name='restart')
async def restart_game(ctx):
    user_id = ctx.author.id
    user_game_status.pop(user_id, None)  # Remove previous game status
    await ctx.send(f"{ctx.author.mention}, the simulation has been restarted. Type anything to begin.")

# Command to clear messages
@bot.command(name='clear')
async def clear_messages(ctx, amount: int = 10):
    await ctx.channel.purge(limit=amount)
    await ctx.send(f"Cleared {amount} messages.")

# Event when the bot is ready
@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")

# Run the bot
bot.run(DISCORD_TOKEN)
