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
intents.messages = True  # Enable message intent for text logging
intents.message_content = True  # Enable reading message content
bot = commands.Bot(command_prefix="!", intents=intents)

# TTS (Text-to-Speech) function
def text_to_speech(text, voice_channel):
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=True)
    
    speech_synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    result = speech_synthesizer.speak_text_async(text).get()
    
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        print("Speech synthesis completed.")
    elif result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = result.cancellation_details
        print(f"Speech synthesis canceled: {cancellation_details.reason}")

# STT (Speech-to-Text) function
def speech_to_text():
    speech_config = speechsdk.SpeechConfig(subscription=SPEECH_KEY, region=SPEECH_REGION)
    audio_config = speechsdk.audio.AudioConfig(use_default_microphone=True)

    # Set up recognizer for the microphone input
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    print("Listening for speech...")
    result = speech_recognizer.recognize_once()

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print(f"Recognized: {result.text}")
        return result.text
    else:
        print("No speech could be recognized")
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

# Capture voice, transcribe it, log, and respond
async def handle_voice_session(channel, voice_client):
    # Capture voice and transcribe it
    transcribed_text = speech_to_text()
    
    # Log the transcription in a text channel
    text_channel = discord.utils.get(channel.guild.text_channels, name='session-logs')  # Ensure a text channel named 'session-logs' exists
    if text_channel:
        await text_channel.send(f"**Transcription**: {transcribed_text}")
    
    if transcribed_text:
        # Pass the transcription to GPT for analysis
        gpt_response = generate_gpt_response(transcribed_text)

        # Log the GPT response
        await text_channel.send(f"**GPT Response**: {gpt_response}")

        # Play the GPT response back in the voice channel
        text_to_speech(gpt_response, channel)

# Voice event handler
@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel is not None and not member.bot:  # If a real user joins
        print(f"{member.name} joined {after.channel.name}")
        
        voice_client = discord.utils.get(bot.voice_clients, guild=after.channel.guild)
        if voice_client is None:
            voice_client = await after.channel.connect()

        # Start handling the voice session (transcribe, log, GPT analyze, and respond)
        await handle_voice_session(after.channel, voice_client)

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
