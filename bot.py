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

# OpenAI Response Generation
def generate_openai_response(user_input):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant for a Mass Casualty Incident simulation game."},
                {"role": "user", "content": user_input}
            ],
            max_tokens=150,
            temperature=0.7,
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        logging.error(f"Error with OpenAI API: {e}")
        return "Sorry, I encountered an error generating a response."

# 1. Bot Event to Handle Voice Channel Join and Game Introduction
@bot.event
async def on_voice_state_update(member, before, after):
    if after.channel is not None and not member.bot:  # Ensure it's a non-bot user
        print(f"{member.name} joined {after.channel.name}")
        
        voice_client = discord.utils.get(bot.voice_clients, guild=after.channel.guild)
        if voice_client is None:
            # Bot joins the voice channel
            voice_client = await after.channel.connect()
        
        # Start the game introduction
        text_to_speech("Welcome to the Mass Casualty Incident simulation. Let's begin!")
        
        # Bot sends a message in the text channel that the session has started
        text_channel = discord.utils.get(after.channel.guild.text_channels, name='session-updates')  # Customize channel name
        if text_channel:
            await text_channel.send(f"Starting session in {after.channel.name}")
        
        # Start listening for the user's response
        await start_session(after.channel, voice_client)

# 2. Start Session and Handle 5-minute Timer
async def start_session(channel, voice_client):
    print(f"Starting session in {channel.name}")
    transcript = []
    
    # Listen for the user's response
    recognized_text = speech_to_text()
    if recognized_text:
        print(f"Recognized: {recognized_text}")
        transcript.append(f"User: {recognized_text}")
        
        # Generate a response from OpenAI GPT
        gpt_response = generate_openai_response(recognized_text)
        transcript.append(f"MCIBot: {gpt_response}")
        
        # Speak the response
        text_to_speech(gpt_response)
    
    # After 5 minutes (or shorter for demo), end the session
    await asyncio.sleep(300)  # Adjust this as needed for your testing
    
    # End the session
    await end_session(channel, transcript, voice_client)

# 3. End Session and Debrief
async def end_session(channel, transcript, voice_client):
    print("Session ending...")
    text_to_speech("Thank you for participating in the simulation. The session is now ending.")
    
    # Send the transcript to a text channel
    text_channel = discord.utils.get(channel.guild.text_channels, name='debriefing')
    if text_channel:
        await text_channel.send("Debriefing session is starting...")
        transcript_text = "\n".join(transcript)
        await text_channel.send(f"Transcript:\n{transcript_text}")
    
    # Safely disconnect from the voice channel
    if voice_client.is_connected():
        await voice_client.disconnect()

# Run the bot
bot.run(DISCORD_TOKEN)
