import discord
from discord.ext import commands, tasks
import os
import openai
import asyncio
from dotenv import load_dotenv

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
bot = commands.Bot(command_prefix="!", intents=intents)

# Dictionary to track user's current game stage and start time
user_game_status = {}
inactive_timeouts = {}  # To track last active time for each user

# GPT response function (focused on playing along naturally)
def generate_gpt_response(user_input, game_status):
    try:
        prompt = f"The player said: '{user_input}'. React and guide the player in a Mass Casualty Incident simulation. Adjust the scenario based on their actions. Current situation: {game_status}"
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

# Organic game flow without predefined stages
async def run_game_flow(channel, member, user_input):
    user_id = member.id
    game_status = user_game_status.get(user_id, "explosion has occurred, and you're the only medical professional available.")
    
    # Generate dynamic GPT response
    gpt_response = generate_gpt_response(user_input, game_status)
    
    # Update game status based on GPT's response
    user_game_status[user_id] = gpt_response
    await channel.send(f"**GPT Response**: {gpt_response}")

# Event: User sends a message in the #demo channel
@bot.event
async def on_message(message):
    if message.author == bot.user or message.author.id == 159985870458322944:  # Ignore bot and MEE6
        return

    # If a user sends a message in the #demo channel
    if message.channel.name == 'demo':
        user_id = message.author.id
        
        # Check if user is starting a new game or continuing
        if user_id not in user_game_status:
            user_game_status[user_id] = "explosion has occurred, and you're the only medical professional available."
            await message.channel.send(f"Welcome, {message.author.mention}, to the Mass Casualty Incident Simulation Demo!")
            await asyncio.sleep(5)
            await message.channel.send("You hear the sound of an **explosion**. The scene is chaotic, and people are injured all around. What will you do first?")
        else:
            # Continue the game flow based on user input
            await run_game_flow(message.channel, message.author, message.content)
        
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

# Task to check inactivity and reset the game if no activity for 10 minutes
@tasks.loop(minutes=1)
async def inactivity_check():
    current_time = asyncio.get_event_loop().time()
    for user_id, last_active_time in list(inactive_timeouts.items()):
        if current_time - last_active_time > 600:  # 10 minutes
            user_game_status.pop(user_id, None)
            inactive_timeouts.pop(user_id, None)
            channel = discord.utils.get(bot.get_all_channels(), name="demo")
            if channel:
                await channel.send(f"User {user_id}'s session has been reset due to inactivity.")

# Event when the bot is ready
@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")
    inactivity_check.start()  # Start the inactivity checker task

# Confirm quitting the game
@bot.command(name='quit')
async def quit_game(ctx):
    def check(m):
        return m.author == ctx.author and m.content.lower() in ['yes', 'no']

    await ctx.send(f"{ctx.author.mention}, are you sure you want to quit the simulation? Type 'yes' or 'no'.")

    try:
        msg = await bot.wait_for('message', check=check, timeout=30)
        if msg.content.lower() == 'yes':
            user_id = ctx.author.id
            user_game_status.pop(user_id, None)
            await ctx.send(f"{ctx.author.mention}, you have quit the simulation. Type anything to restart.")
        else:
            await ctx.send(f"{ctx.author.mention}, you have decided to continue the simulation.")
    except asyncio.TimeoutError:
        await ctx.send("You took too long to respond. Simulation will continue.")

# Error handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have the necessary permissions to run this command.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")

# Run the bot
bot.run(DISCORD_TOKEN)
