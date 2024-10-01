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
SPEECH_KEY = os.getenv('SPEECH_KEY')
SPEECH_REGION = "uaenorth"  # Set to your Azure region (uaenorth)

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

# Continuous STT (Speech-to-Text) function
def speech_to_text_continuous():
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    
    # Set up audio configuration (default microphone, ensuring it's in the correct format)
    audio_format = speechsdk.audio.AudioStreamFormat(samples_per_second=16000, bits_per_sample=16, channels=1)
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True, audio_stream_format=audio_format)
    
    # Set up the recognizer
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    
    # Callback for recognized speech
    def recognized_cb(evt):
        print(f"RECOGNIZED: {evt.result.text}")
        return evt.result.text
    
    # Connect to the recognizer event
    speech_recognizer.recognized.connect(recognized_cb)

    print("Starting continuous recognition...")
    speech_recognizer.start_continuous_recognition()

    # Keep the recognition session active
    while True:
        asyncio.sleep(1)

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
            voice_client = await after.channel.connect()

        # Introduce the game
        text_to_speech("Welcome to the Mass Casualty Incident simulation. Please speak now.")

        # Start listening continuously for speech
        speech_to_text_continuous()

        # Keep the bot connected but stop active speech recognition after a while
        await asyncio.sleep(600)  # Keeps the bot listening for 10 minutes

        # Bot will remain connected to the voice channel unless disconnected manually

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
