import discord
from discord.ext import commands, tasks
import os
import openai
import asyncio
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
import random

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
AZURE_SPEECH_KEY = os.getenv('AZURE_SPEECH_KEY')
AZURE_REGION = os.getenv('AZURE_REGION')

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

# Inappropriate triggers that will count towards strikes
trigger_phrases = ["nap", "ignore", "kill all"]

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

# Function to transcribe speech to text using Azure
def transcribe_speech_to_text(audio_file):
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_REGION)
    audio_config = speechsdk.AudioConfig(filename=audio_file)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    result = speech_recognizer.recognize_once()
    
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    else:
        return "Sorry, I couldn't understand the audio."

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
    if message.author == bot.user or message.author.id == 159985870458322944:  # Ignore bot and MEE6
        return

    # Check if the message starts with "!ign" (ignoring case)
    if message.content.lower().startswith("!ign"):
        return  # Ignore the message without triggering any bot response

    # Simulate "quit" action
    if message.content.lower() == "quit":
        await handle_quit(message.channel, message.author.id)
        return

    # If a user sends a voice message in the #demo channel
    if message.channel.name == 'demo' and message.attachments:
        voice_file = message.attachments[0]
        
        if voice_file.filename.endswith(".wav") or voice_file.filename.endswith(".mp3"):
            await message.channel.send("Analyzing the audio...")  # Inform the player that analysis is in progress
            
            # Download the audio file locally
            await voice_file.save(f"./{voice_file.filename}")
            
            # Transcribe the audio
            transcription = transcribe_speech_to_text(voice_file.filename)
            
            # Handle transcription with GPT response
            await message.channel.send(f"Transcription: {transcription}")
            await handle_transcription(message, transcription)
        
    await bot.process_commands(message)

# Handle transcription with GPT
async def handle_transcription(message, transcription):
    gpt_response = generate_gpt_response(transcription, user_game_status.get(message.author.id, ""))
    await message.channel.send(f"**GPT Response**: {gpt_response}")

# Command to restart the game
@bot.command(name='restart')
async def restart_game(ctx):
    user_id = ctx.author.id
    user_game_status.pop(user_id, None)  # Remove previous game status
    await ctx.send(f"{ctx.author.mention}, the simulation has been restarted. Type anything to begin.")

# Command to clear messages
@bot.command(name='clear')
async def clear_messages(ctx, amount: int = 10):
    if ctx.author.guild_permissions.administrator:
        await ctx.channel.purge(limit=amount)
        await ctx.send(f"Cleared {amount} messages.")
    else:
        await ctx.send("You don't have permission to use this command.")

# Event when the bot is ready
@bot.event
async def on_ready():
    print(f"{bot.user.name} has connected to Discord!")

# Run the bot
bot.run(DISCORD_TOKEN)
