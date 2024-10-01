import discord
from discord.ext import commands
import os
import openai
import azure.cognitiveservices.speech as speechsdk
from dotenv import load_dotenv

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
        # Use pre-recorded audio file instead of microphone for debugging purposes
        audio_config = speechsdk.AudioConfig(filename="test.wav")
    else:
        # Use default microphone
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
        print(f"Speech recognition canceled: {cancellation_details.reason}")
        print(f"Error details: {cancellation_details.error_details}")
    return None

# OpenAI GPT response function
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
        if voice_client is None:  # If bot is not already in the channel
            voice_client = await after.channel.connect()

        # Introduce the game
        text_to_speech("Welcome to the Mass Casualty Incident simulation. Please speak now.")
        
        # Listen for user speech and process it (change 'use_audio_file=True' for testing with an audio file)
        recognized_text = speech_to_text(use_audio_file=False)
        if recognized_text:
            gpt_response = generate_gpt_response(recognized_text)
            print(f"GPT Response: {gpt_response}")
            text_to_speech(gpt_response)  # Respond using TTS

        # Disconnect after responding
        await voice_client.disconnect()

# Start the bot
bot.run(DISCORD_TOKEN)
