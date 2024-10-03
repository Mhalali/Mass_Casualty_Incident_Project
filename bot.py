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
interaction_logs = {}  # To store complete interaction for session logs

# Inappropriate triggers that will count towards strikes (quit removed from this)
trigger_phrases = ["nap", "ignore", "kill all"]

# Hospital setup
hospitals = {
    "Rashid Hospital Trauma Center": "Helicopter pad available, full ER capabilities.",
    "Latifa Hospital": "No helipad, limited ER.",
    "Dubai Hospital": "Helipad available, limited ER.",
    "Al Jalila Children’s Hospital": "No helipad, ER only for children."
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

# MCI or False Alarm check
async def mci_or_false_alarm_check(channel, user_id):
    mci_thresholds = {
        "victims": 10,
        "deaths": 6,
        "critical_injuries": 10
    }

    # Simulating uncertainty in victim numbers
    reported_victims = random.randint(8, 15)
    reported_deaths = random.randint(4, 8)
    reported_critical_injuries = random.randint(5, 12)

    # Players need to ask questions about what they are seeing
    await channel.send(f"You see {reported_victims} victims, {reported_deaths} deaths, and {reported_critical_injuries} critically injured patients. What do you think? Is this an MCI or a false alarm?")
    
    if reported_victims >= mci_thresholds["victims"] or reported_deaths >= mci_thresholds["deaths"] or reported_critical_injuries >= mci_thresholds["critical_injuries"]:
        await channel.send("This is a Mass Casualty Incident (MCI). Proceed with the MCI protocol.")
    else:
        await channel.send("This might be a false alarm. Proceed with caution and reassess the situation.")

# Organic game flow without predefined stages
async def run_game_flow(channel, member, user_input):
    user_id = member.id
    game_status = user_game_status.get(user_id, "A car accident has occurred, and you're part of the medical team arriving on the scene.")
    
    # Generate dynamic GPT response
    gpt_response = generate_gpt_response(user_input, game_status)
    
    # Update game status based on GPT's response
    user_game_status[user_id] = gpt_response
    interaction_logs.setdefault(user_id, []).append(f"**User**: {user_input}\n**GPT**: {gpt_response}")
    await channel.send(f"**GPT Response**: {gpt_response}")

# Warning and inactivity handling
async def start_inactivity_timer(channel, user_id):
    user_timers[user_id] = 600  # Timer set to 10 minutes (600 seconds)
    while user_timers[user_id] > 0:
        await asyncio.sleep(1)
        user_timers[user_id] -= 1
        
        if user_timers[user_id] == 60:  # Warn when 1 minute is left
            await channel.send(f"Warning: You have 1 minute left to respond.")

    if user_timers[user_id] == 0:
        await end_game_due_to_inactivity(channel, user_id)

# End game due to inactivity or quit
async def end_game_due_to_inactivity(channel, user_id):
    await channel.send(f"Your time is up. The game will reset.")
    
    session_logs_channel = discord.utils.get(channel.guild.channels, name="session-logs")
    report_logs_channel = discord.utils.get(channel.guild.channels, name="report-logs")
    full_transcript = "\n".join(interaction_logs.get(user_id, []))
    
    if session_logs_channel:
        await session_logs_channel.send(f"Session for <@{user_id}> ended. Transcript:\n{full_transcript}")
    
    if report_logs_channel:
        await report_logs_channel.send(f"Performance analysis for <@{user_id}>: Interaction summary sent via DM.")

    # Send DM report
    user = bot.get_user(user_id)
    if user:
        await user.send(f"Your session ended. Here's a summary:\n{full_transcript}")

    # Reset user data
    user_game_status.pop(user_id, None)
    user_timers.pop(user_id, None)
    interaction_logs.pop(user_id, None)

# Event when player quits
async def handle_quit(channel, user_id):
    await channel.send("Player has quit. Predicting the outcome based on their interactions.")
    # Simulate a GPT-based predicted ending
    final_response = "Based on your actions, the accident site was partially managed. However, delays in decision-making caused casualties to worsen."
    await channel.send(f"**GPT Ending**: {final_response}")
    
    await end_game_due_to_inactivity(channel, user_id)

# Event: User sends a message in the #demo channel
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # Simulate "quit" action
    if message.content.lower() == "quit":
        await handle_quit(message.channel, message.author.id)
        return

    # Handle debrief based on roles
    if message.channel.name == 'demo':
        user_id = message.author.id

        if user_id not in user_game_status:
            role_assigned = await assign_role(message.author)
            user_game_status[user_id] = "A severe accident with 3 cars and 5 victims. We need to allocate a safe zone immediately."
            
            if role_assigned == "Safety Officer":
                await message.channel.send(f"Welcome, {message.author.mention}, to the MCI Simulation Demo! You are assigned as **{role_assigned}**. Your role involves ensuring safety zones are established.")
            else:
                await message.channel.send(f"Welcome, {message.author.mention}, to the MCI Simulation Demo! You are assigned as **{role_assigned}**. GPT will assist in roles not assigned to players.")
            
            # After debrief, perform MCI or False Alarm check
            await mci_or_false_alarm_check(message.channel, user_id)
            
            await start_inactivity_timer(message.channel, user_id)
        else:
            await run_game_flow(message.channel, message.author, message.content)

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
