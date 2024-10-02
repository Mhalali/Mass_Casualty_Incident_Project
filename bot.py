import discord
from discord.ext import commands, tasks
import os
import openai
import asyncio
from dotenv import load_dotenv
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Set up OpenAI API key
openai.api_key = OPENAI_API_KEY

# Discord bot setup with intents
intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
intents.members = True  # Allow tracking members

bot = commands.Bot(command_prefix="!", intents=intents)

# MCI Master ID
MCI_MASTER_ID = 1283780903629357179

# Dictionary to track users' current game status and last activity time
user_game_status = {}
last_interaction_time = None

# GPT response function
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

# Reset game if no interaction after 10 minutes
@tasks.loop(minutes=1)
async def check_idle_time():
    global last_interaction_time
    if last_interaction_time and (datetime.now() - last_interaction_time > timedelta(minutes=10)):
        await reset_game(None)  # Reset the game for all players if no activity

# Organic game flow without predefined stages
async def run_game_flow(channel, member, user_input):
    global last_interaction_time
    last_interaction_time = datetime.now()  # Update the last interaction time

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
    if message.author == bot.user:
        return

    # Ignore the MCI master account for gameplay but listen to commands
    if message.author.id == MCI_MASTER_ID:
        await bot.process_commands(message)
        return

    # Handle messages in the #demo channel
    if message.channel.name == 'demo':
        user_id = message.author.id
        
        # Assign role if a new player joins
        if user_id not in user_game_status:
            user_game_status[user_id] = "explosion has occurred, and you're the only medical professional available."
            await message.channel.send(f"Welcome, {message.author.mention}, to the Mass Casualty Incident Simulation Demo!")
            await asyncio.sleep(5)
            await message.channel.send("You hear the sound of an **explosion**. The scene is chaotic, and people are injured all around. What will you do first?")
        else:
            # Continue the game flow based on user input
            await run_game_flow(message.channel, message.author, message.content)

# Command to restart the game for all players
@bot.command(name='reset')
@commands.has_permissions(administrator=True)
async def reset_game(ctx):
    global user_game_status
    user_game_status.clear()
    await ctx.send("The game has been reset for all players. Type anything to start again.")

# Command to change the scene
@bot.command(name='change_scene')
@commands.has_permissions(administrator=True)
async def change_scene(ctx, *, scene_description):
    for user_id in user_game_status:
        user_game_status[user_id] = scene_description
    await ctx.send(f"The scene has been changed to: {scene_description}")

# Error handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have the necessary permissions to run this command.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")

# Start the idle check loop
@bot.event
async def on_ready():
    check_idle_time.start()
    print(f'{bot.user.name} is connected to Discord!')

# Start the bot
bot.run(DISCORD_TOKEN)
