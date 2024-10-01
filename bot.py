import discord
from discord.ext import commands, tasks
import os
import openai
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv
import asyncio

# Load environment variables
load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
SPEECH_KEY = os.getenv('SPEECH_KEY')
SPEECH_REGION = os.getenv('SPEECH_REGION')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Set up OpenAI API key
openai.api_key = OPENAI_API_KEY

# Discord bot setup with intents
intents = discord.Intents.default()
intents.voice_states = True
bot = commands.Bot(command_prefix="!", intents=intents)

# TTS (Text-to-Speech) function
def text_to_speech(text):
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    result = speech_synthesizer.speak_text_async(text).get()
    
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesis completed.")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"Speech synthesis canceled: {cancellation_details.reason}")

# STT (Speech-to-Text) function with optional audio file for testing
def speech_to_text(use_audio_file=False):
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    
    if use_audio_file:
        audio_config = speechsdk.AudioConfig(filename="test.wav")  # For testing with audio file
    else:
        audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)  # Using microphone
    
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
        print(f"Speech recognition canceled: {cancellation_details.reason}")
    return None

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

# Voice event handler
@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel is not None and not member.bot:  # If a real user joins
        print(f"{member.name} joined {after.channel.name}")
        
        voice_client = discord.utils.get(bot.voice_clients, guild=after.channel.guild)
        if voice_client is None:
            # Bot joins the voice channel
            voice_client = await after.channel.connect()

        # Introduce the game
        text_to_speech("Welcome to the Mass Casualty Incident simulation. Please speak now.")
        
        # Start idle timer (10 minutes)
        idle_timer.start(after.channel.guild)

        # Listen for user speech
        recognized_text = speech_to_text()
        if recognized_text:
            gpt_response = generate_gpt_response(recognized_text)
            text_to_speech(gpt_response)
            idle_timer.stop()  # Stop the idle timer when interaction happens

# Idle timer task to check for inactivity
@tasks.loop(minutes=10)
async def idle_timer(guild):
    # After 10 minutes of no activity, the bot sends a message to the text channel and stops listening
    text_channel = discord.utils.get(guild.text_channels, name='session-updates')
    if text_channel:
        await text_channel.send(f"Bot has been idle in the voice channel for 10 minutes. Feel free to ask questions here.")
    
    # The bot stays connected to the voice channel but relocates its interactions to the text channel

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
