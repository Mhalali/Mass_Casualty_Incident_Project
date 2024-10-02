import discord
from discord.ext import commands
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

# Discord bot setup with intents
intents = discord.Intents.default()
intents.messages = True  # Enable messages intent
intents.message_content = True  # Enable reading message content
bot = commands.Bot(command_prefix="!", intents=intents)

# Dictionary to track user's current game stage and start time
user_game_status = {}
game_active = False  # Tracks whether the game is active

MEE6_BOT_ID = 159985870458322944  # Mee6 bot ID to ignore

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
    global game_active
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
    global game_active
    if message.author == bot.user or message.author.id == MEE6_BOT_ID:
        return

    # If a user sends a message in the #demo channel
    if message.channel.name == 'demo' and game_active:
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

    # Process other commands or responses normally
    await bot.process_commands(message)

# Command to reset the game and stop it
@bot.command(name='reset')
async def reset_game(ctx):
    global game_active
    game_active = False  # Set game to inactive
    user_game_status.clear()  # Clear the game state for all users
    await ctx.send(f"{ctx.author.mention}, the simulation has been reset and stopped. The game is now inactive. Type anything to begin a new session.")

# Command to start the game manually
@bot.command(name='start')
async def start_game(ctx):
    global game_active
    if not game_active:
        game_active = True
        await ctx.send(f"{ctx.author.mention}, the simulation has been started. Players can now join and interact.")
    else:
        await ctx.send(f"{ctx.author.mention}, the simulation is already active!")

# Command to clear messages from the #demo channel
@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)  # Only allow those with permissions
async def clear_messages(ctx, limit: int = 100):
    await ctx.channel.purge(limit=limit)
    await ctx.send(f"Cleared {limit} messages from the channel.", delete_after=5)

# Command to set a 10-minute inactivity timer to reset the game
async def inactivity_timer():
    global game_active
    await asyncio.sleep(600)  # 10 minutes
    if game_active:
        game_active = False
        print("Game reset due to inactivity.")

# Error handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have the necessary permissions to run this command.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")

# Start the bot
bot.run(DISCORD_TOKEN)
