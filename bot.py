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

# Dictionary to track user's current demo stage
user_stage = {}

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

# Demo stages function
async def run_demo_stages(channel, member, stage):
    # Stage 1: Welcome Message
    if stage == 1:
        welcome_message = (
            f"Welcome, {member.mention}, to the Mass Casualty Incident Simulation Demo! "
            "You are now participating in a critical response scenario where your decisions will shape the outcome. "
            "Let's begin! You hear the sound of an explosion. The scene is chaotic, and people are injured all around. "
            "You are the only medical professional available. What will you do first?"
        )
        await channel.send(welcome_message)
        user_stage[member.id] = 2  # Move to next stage

    # Stage 2: Response to First Action
    elif stage == 2:
        await channel.send("Suddenly, the weather worsens. Rain is pouring, and some of the patients are at risk of hypothermia. "
                           "You must make critical decisions quickly. How will you handle the situation?")
        user_stage[member.id] = 3  # Move to next stage

    # Stage 3: Scenario Conclusion
    elif stage == 3:
        conclusion_message = (
            "The emergency services have arrived. The patients are being transported to the hospital, and the scene is stabilizing. "
            "Great job handling the situation under pressure!"
        )
        await channel.send(conclusion_message)
        user_stage[member.id] = 4  # End demo

        # Send a PM with a summary and link to GitHub
        summary_message = (
            f"Thank you for participating in the demo, {member.mention}. "
            "You can review the scenario in the `#demo` channel, and check out our GitHub for more details:\n"
            "https://github.com/Mhalali/Mass_Casualty_Incident_Project"
        )
        try:
            await member.send(summary_message)
        except discord.Forbidden:
            await channel.send(f"Could not send a PM to {member.mention}, but here’s the GitHub link: https://github.com/Mhalali/Mass_Casualty_Incident_Project")

# Event: User sends a message in the #demo channel
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # If a user sends a message in #demo channel
    if message.channel.name == 'demo':
        user_id = message.author.id

        # Initialize user stage if it's the first interaction
        if user_id not in user_stage:
            user_stage[user_id] = 1

        current_stage = user_stage[user_id]

        # Proceed to the next stage based on the current stage
        if current_stage == 1:
            await run_demo_stages(message.channel, message.author, 1)
        elif current_stage == 2:
            # Process user input and generate GPT response
            gpt_response = generate_gpt_response(message.content)
            await message.channel.send(f"**GPT Response**: {gpt_response}")
            await run_demo_stages(message.channel, message.author, 2)
        elif current_stage == 3:
            # Process user input and generate GPT response
            gpt_response = generate_gpt_response(message.content)
            await message.channel.send(f"**GPT Response**: {gpt_response}")
            await run_demo_stages(message.channel, message.author, 3)

    # Process other commands or responses normally
    await bot.process_commands(message)

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
