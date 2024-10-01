import discord
from discord.ext import commands
import os
import openai
import azure.cognitiveservices.speech as speechsdk
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
intents.voice_states = True
intents.messages = True  # Enable message intent for text logging
intents.message_content = True  # Enable reading message content
bot = commands.Bot(command_prefix="!", intents=intents)

# Function for text-to-speech (TTS)
def text_to_speech(text, voice_channel):
    # TTS using Azure (we can use a dummy function for now)
    print(f"Bot says: {text}")

# Generate GPT response
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

# Send welcome message
async def send_welcome_message(channel):
    text_to_speech("Welcome to the Mass Casualty Incident simulation. You are the only doctor on the scene due to severe weather conditions. Multiple casualties have occurred, and your job is to triage and manage the situation.", channel)
    await channel.send("Welcome to the Mass Casualty Incident simulation. You are the only doctor on the scene due to severe weather conditions. Multiple casualties have occurred, and your job is to triage and manage the situation.")

# Stage 1 - Assess the situation
async def stage_1(channel):
    await asyncio.sleep(2)
    text_to_speech("Stage 1: You have five casualties. Start with the most critically injured. Use basic triage protocols.", channel)
    await channel.send("Stage 1: You have five casualties. Start with the most critically injured. Use basic triage protocols.")
    await asyncio.sleep(10)  # Simulate time for the user to respond or think
    return "Stage 1 complete"

# Stage 2 - New injuries arise
async def stage_2(channel):
    await asyncio.sleep(2)
    text_to_speech("Stage 2: More injuries are occurring due to worsening weather conditions. Prioritize transporting the most critical patients.", channel)
    await channel.send("Stage 2: More injuries are occurring due to worsening weather conditions. Prioritize transporting the most critical patients.")
    await asyncio.sleep(10)
    return "Stage 2 complete"

# Stage 3 - Final stage
async def stage_3(channel):
    await asyncio.sleep(2)
    text_to_speech("Stage 3: The ambulance has arrived. You must quickly decide who gets transported first.", channel)
    await channel.send("Stage 3: The ambulance has arrived. You must quickly decide who gets transported first.")
    await asyncio.sleep(10)
    return "Stage 3 complete"

# Ending the demo
async def end_demo(channel, member):
    await asyncio.sleep(2)
    text_to_speech("This concludes the demo. Thank you for participating!", channel)
    await channel.send("This concludes the demo. Thank you for participating!")
    
    # Send a PM to the user with a summary and GitHub link
    summary_message = (
        f"Thank you for playing, {member.name}!\n"
        "Here is a summary of the demo:\n"
        "- Stage 1: Triage the critically injured.\n"
        "- Stage 2: Manage new injuries and prioritize transportation.\n"
        "- Stage 3: Decide on ambulance transport.\n"
        "\nFor more details, visit the GitHub repository: https://github.com/Mhalali/Mass_Casualty_Incident_Project"
    )
    try:
        await member.send(summary_message)
    except discord.Forbidden:
        print(f"Could not send PM to {member.name}. Sending message in text channel.")
        await channel.send(summary_message)

# Handle voice session with stages
async def handle_voice_session(channel, member, voice_client):
    await send_welcome_message(channel)
    await asyncio.sleep(5)
    
    # Stage 1
    stage_1_result = await stage_1(channel)
    print(stage_1_result)
    
    # Stage 2
    stage_2_result = await stage_2(channel)
    print(stage_2_result)
    
    # Stage 3
    stage_3_result = await stage_3(channel)
    print(stage_3_result)
    
    # End the demo
    await end_demo(channel, member)
    
    # Disconnect the bot from the voice channel
    if voice_client.is_connected():
        await voice_client.disconnect()

# Voice event handler
@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel is not None and not member.bot:  # If a real user joins
        print(f"{member.name} joined {after.channel.name}")
        
        voice_client = discord.utils.get(bot.voice_clients, guild=after.channel.guild)
        if voice_client is None:
            voice_client = await after.channel.connect()

        # Start handling the voice session (staged demo)
        await handle_voice_session(after.channel, member, voice_client)

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
