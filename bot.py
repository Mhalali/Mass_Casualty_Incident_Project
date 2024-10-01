# 1. Imports and Token Loading
import discord
from discord.ext import commands
import os
import openai
import azure.cognitiveservices.speech as speechsdk
import asyncio
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("mcibot.log"),
        logging.StreamHandler()
    ]
)

# Load environment variables from .env file
load_dotenv()

# Get the necessary tokens directly from environment variables
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
SPEECH_KEY = os.getenv('SPEECH_KEY')
SPEECH_REGION = os.getenv('SPEECH_REGION')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Set up OpenAI API key
openai.api_key = OPENAI_API_KEY

# Discord intents
intents = discord.Intents.default()
intents.voice_states = True  # Enable voice state tracking
intents.members = True       # Enable member tracking
intents.messages = True      # Enable message tracking
intents.message_content = True  # Enable message content intent

bot = commands.Bot(command_prefix="!", intents=intents)

# Azure Speech Configurations
def speech_to_text():
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    
    print("Listening for speech...")
    result = speech_recognizer.recognize_once()
    
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print(f"Recognized: {result.text}")
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"Speech Recognition canceled: {cancellation_details.reason}")
        print(f"Error details: {cancellation_details.error_details}")
    return None

# TTS Function
def text_to_speech(text):
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    
    print(f"Saying: {text}")
    result = speech_synthesizer.speak_text_async(text).get()
    
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesis completed.")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"Speech synthesis canceled: {cancellation_details.reason}")
        print(f"Error details: {cancellation_details.error_details}")

# 2. Bot Events and Automation

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    for guild in bot.guilds:
        print(f'Bot is connected to the guild: {guild.name}')

# Respond to mentions
@bot.event
async def on_message(message):
    # Ignore bot's own messages
    if message.author == bot.user:
        return
    
    # Check if the bot is mentioned in the message
    if bot.user in message.mentions:
        # Extract the message content excluding the bot mention
        user_message = message.content
        for mention in message.mentions:
            if mention == bot.user:
                user_message = user_message.replace(f"<@!{bot.user.id}>", "")
                user_message = user_message.replace(f"<@{bot.user.id}>", "")
        user_message = user_message.strip()

        if user_message:
            # Generate response using OpenAI's ChatCompletion
            gpt_response = generate_openai_response(user_message)
            await message.channel.send(f"{gpt_response}")
        
    # Process other commands as usual
    await bot.process_commands(message)

def generate_openai_response(user_input):
    response = openai.chat_completions.create(
        model="gpt-3.5-turbo",  # Or "gpt-4" if you have access
        messages=[
            {"role": "system", "content": "You are a helpful assistant for a Mass Casualty Incident simulation game."},
            {"role": "user", "content": user_input}
        ],
        max_tokens=150,
        temperature=0.7,  # Adjust for creativity
    )
    return response['choices'][0]['message']['content'].strip()

# Automatically start the session when a user joins the voice channel
@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel is not None and not member.bot:  # Ensure it's a non-bot user
        print(f"{member.name} joined {after.channel.name}")
        
        voice_client = discord.utils.get(bot.voice_clients, guild=after.channel.guild)
        if voice_client is None:
            # Bot joins the voice channel
            voice_client = await after.channel.connect()
        
        # Start the session
        await start_session(after.channel, voice_client)

# Start session and set up 5-minute timer for automatic debrief
async def start_session(channel, voice_client):
    print(f"Starting session in {channel.name}")
    
    # Bot sends a message in text channel that the session has started
    text_channel = discord.utils.get(channel.guild.text_channels, name='session-updates')  # Customize this
    if not text_channel:
        print("Text channel 'session-updates' not found! Using a default text channel.")
        text_channel = channel.guild.text_channels[0]  # Fallback to the first available text channel
    
    if text_channel:
        await text_channel.send(f"Starting 5-minute session in {channel.name}")
    
    transcript = []
    # Bot listens for 5 minutes (300 seconds)
    end_time = asyncio.get_event_loop().time() + 300  # 5 minutes
    while asyncio.get_event_loop().time() < end_time:
        recognized_text = speech_to_text()
        if recognized_text:
            await text_channel.send(f"Recognized: {recognized_text}")
            transcript.append(f"Guest: {recognized_text}")
            
            # Pass the recognized text to OpenAI GPT to generate a response
            gpt_response = generate_openai_response(recognized_text)
            await text_channel.send(f"MCIBot: {gpt_response}")
            transcript.append(f"MCIBot: {gpt_response}")
            
            text_to_speech(gpt_response)  # Convert GPT response to speech output
        
        await asyncio.sleep(2)  # Avoid overwhelming loops
    
    # End the session and debrief
    await end_session(channel, transcript, voice_client)

# End session and start debriefing
async def end_session(channel, transcript, voice_client):
    print("Session ending...")
    text_to_speech("Thank you for playing. This concludes the session.")
    
    # Send debriefing to text channel
    text_channel = discord.utils.get(channel.guild.text_channels, name='debriefing')  # Customize this
    if text_channel:
        await text_channel.send("Debriefing session is starting...")
        await text_channel.send("Summary: Great job! Here are your stats...")  # Customize the debrief message
    
    # Optionally send PM to users with the transcript
    transcript_text = "\n".join(transcript)
    for member in channel.members:
        if not member.bot:
            try:
                await member.send(f"Thank you for playing, {member.name}. Here is your session transcript:\n{transcript_text}")
            except discord.Forbidden:
                await text_channel.send(f"Could not send PM to {member.name}")
    
    # Safely disconnect the bot from the voice channel
    if voice_client.is_connected():
        await voice_client.disconnect()

# Error handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command does not exist.")
    elif isinstance(error, commands.MissingPermissions):
        await ctx.send("You do not have the correct permissions to run this command.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")

# 3. Test STT Command
@bot.command(name='test_stt')
async def test_stt(ctx):
    recognized_text = speech_to_text()
    if recognized_text:
        await ctx.send(f"Recognized: {recognized_text}")
    else:
        await ctx.send("No speech recognized or an error occurred.")

# 4. OpenAI Integration for NLP Responses (manual command, still available)
@bot.command(name='ask')
async def ask(ctx, *, query: str):
    response = generate_openai_response(query)
    await ctx.send(response)

# 5. Run the bot using the secure token from environment variables
bot.run(DISCORD_TOKEN)
