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

# Dictionary to track user's current demo stage, start time, and performance
user_stage = {}
game_start_time = {}
user_performance = {}

# GPT response function (focused on playing along without guidance)
def generate_gpt_response(user_input, stage):
    try:
        if stage == 1:
            prompt = f"There has been an explosion. The player said: '{user_input}'. React based on the situation."
        elif stage == 2:
            prompt = f"The weather is worsening, and patients are at risk of hypothermia. The player said: '{user_input}'. Continue based on the scenario."
        else:
            prompt = f"The emergency services are arriving. The player said: '{user_input}'. End the scenario."

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an NPC in a mass casualty simulation. Play along naturally."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return "There was an error generating a response."

# Performance evaluation
def evaluate_performance(user_input, user_id):
    if user_id not in user_performance:
        user_performance[user_id] = {"good": 0, "bad": 0}

    # Evaluate based on certain keywords
    if any(keyword in user_input.lower() for keyword in ["help", "treat", "triage", "assist", "call", "manage"]):
        user_performance[user_id]["good"] += 1
    else:
        user_performance[user_id]["bad"] += 1

# Demo stages function
async def run_demo_stages(channel, member, stage):
    # Check if game has reached 10 minutes and end it if so
    if game_start_time.get(member.id) and (asyncio.get_event_loop().time() - game_start_time[member.id]) > 600:
        await channel.send("The demo has ended. Thank you for participating!")
        await end_game(member, channel)
        return

    # Stage 1: Welcome and initial prompt
    if stage == 1:
        welcome_message = (
            f"Welcome, {member.mention}, to the Mass Casualty Incident Simulation Demo! "
            "You hear the sound of an **explosion**. The scene is chaotic, and people are injured all around. "
            "You are the only medical professional available. What will you do first?"
        )
        await channel.send(welcome_message)
        user_stage[member.id] = 2  # Move to next stage

    # Stage 2: Weather worsening
    elif stage == 2:
        await channel.send("The weather worsens. **Rain** is pouring, and some of the **patients** are at risk of **hypothermia**. "
                           "What is your next move?")
        user_stage[member.id] = 3  # Move to next stage

    # Stage 3: Scenario Conclusion
    elif stage == 3:
        conclusion_message = (
            "The **emergency services** have arrived. The **patients** are being transported to the hospital, and the scene is stabilizing. "
            "Great job handling the situation under pressure!"
        )
        await channel.send(conclusion_message)
        user_stage[member.id] = 4  # End demo

        await end_game(member, channel)  # End the game

# End the game and send performance feedback
async def end_game(member, channel):
    if member.id in user_performance:
        performance = user_performance[member.id]
        feedback_message = f"Performance Summary for {member.mention}:\n"
        feedback_message += f"Good decisions: {performance['good']}\n"
        feedback_message += f"Bad decisions: {performance['bad']}\n"

        # Provide feedback based on performance
        if performance["good"] > performance["bad"]:
            feedback_message += "Overall: You made good decisions under pressure!"
        else:
            feedback_message += "Overall: There were several critical errors. Keep practicing!"

        try:
            await member.send(feedback_message)
        except discord.Forbidden:
            await channel.send(f"Could not send a PM to {member.mention}, but here’s your performance summary:\n{feedback_message}")
    else:
        await channel.send(f"No performance data available for {member.mention}.")

# Event: User sends a message in the #demo channel
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    # If a user sends a message in #demo channel
    if message.channel.name == 'demo':
        user_id = message.author.id

        # Initialize user stage and start time if it's the first interaction
        if user_id not in user_stage:
            user_stage[user_id] = 1
            game_start_time[user_id] = asyncio.get_event_loop().time()  # Start game timer

        current_stage = user_stage[user_id]

        # Evaluate performance based on user input
        evaluate_performance(message.content, user_id)

        # Proceed to the next stage based on the current stage
        if current_stage == 1:
            await run_demo_stages(message.channel, message.author, 1)
        elif current_stage == 2:
            # Process user input and generate GPT response
            gpt_response = generate_gpt_response(message.content, 2)
            await message.channel.send(f"**GPT Response**: {gpt_response}")
            await asyncio.sleep(30)  # 30-second delay before moving to next stage
            await run_demo_stages(message.channel, message.author, 2)
        elif current_stage == 3:
            # Process user input and generate GPT response
            gpt_response = generate_gpt_response(message.content, 3)
            await message.channel.send(f"**GPT Response**: {gpt_response}")
            await asyncio.sleep(30)  # 30-second delay before concluding
            await run_demo_stages(message.channel, message.author, 3)

    # Process other commands or responses normally
    await bot.process_commands(message)

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
