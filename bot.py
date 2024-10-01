import discord
from discord.ext import commands
import os
import openai
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

# GPT response function
def generate_gpt_response(user_input):
    try:
        response = openai.chat_completions.create(
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

# Handle incoming text messages
@bot.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author == bot.user:
        return
    
    # Process user messages
    if message.content:
        # Simulate transcription by using the message content
        user_input = message.content
        
        # Generate a GPT response based on the user's input
        gpt_response = generate_gpt_response(user_input)

        # Respond in the same text channel
        await message.channel.send(f"**GPT Response**: {gpt_response}")

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
