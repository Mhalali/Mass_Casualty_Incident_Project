import discord
from discord.ext import commands
import os
import openai
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Set up OpenAI API key
openai.api_key = OPENAI_API_KEY

# Discord bot setup with intents
intents = discord.Intents.default()
intents.voice_states = True  # Enable voice state tracking
intents.messages = True      # Enable message tracking
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# GPT response function
def generate_gpt_response(user_input):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are assisting with a simulation."},
                {"role": "user", "content": user_input}
            ]
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return "There was an error generating a response."

# TTS (Text-to-Speech) function
def text_to_speech(text):
    # Simulated TTS, prints the message to console for now
    print(f"TTS: {text}")

# Handle voice state updates for the demo
@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel and after.channel.name == "demo" and not member.bot:
        # Send welcome message when a user joins the demo channel
        text_channel = discord.utils.get(after.channel.guild.text_channels, name='demo')
        if text_channel:
            await text_channel.send(f"Welcome {member.name} to the Mass Casualty Incident simulation.")
            await text_channel.send("You're the only doctor on the scene. The weather is bad, and you're the first responder.")
            text_to_speech("Welcome to the Mass Casualty Incident simulation. You're the only doctor on the scene.")

        # Start the demo stages
        await run_demo_stages(member, text_channel)

# Demo stages
async def run_demo_stages(member, text_channel):
    stages = [
        "Stage 1: A massive car accident has just happened. Multiple patients need assistance.",
        "Stage 2: You approach the victims. Some are more critical than others.",
        "Stage 3: The weather worsens, making it difficult to treat patients.",
        "Stage 4: You prioritize patients and call for help.",
        "Stage 5: The ambulance arrives and takes over."
    ]
    
    for stage in stages:
        await text_channel.send(stage)
        text_to_speech(stage)
        await asyncio.sleep(10)  # Pause between stages for realism
    
    await end_demo(member, text_channel)

# End demo and PM the summary
async def end_demo(member, text_channel):
    await text_channel.send(f"Demo finished. Thank you for participating, {member.name}!")
    
    summary = "You successfully completed the Mass Casualty Incident simulation. You prioritized patients under extreme conditions and coordinated the response. Well done!"
    github_link = "https://github.com/Mhalali/Mass_Casualty_Incident_Project"
    
    # Send a PM with the summary and GitHub link
    try:
        await member.send(f"Thank you for participating in the demo, {member.name}.\n\n{summary}\n\nFor more information, visit: {github_link}")
    except discord.Forbidden:
        await text_channel.send(f"Could not send PM to {member.name}.")

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
