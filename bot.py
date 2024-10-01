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
async def run_demo_stages(channel, member):
    # Stage 1: Welcome Message
    welcome_message = (
        f"Welcome, {member.mention}, to the Mass Casualty Incident Simulation Demo! "
        "You are now participating in a critical response scenario where your decisions will shape the outcome. "
        "Let's begin!"
    )
    await channel.send(welcome_message)

    # Stage 2: Simulated Scenario Start
    scenario_intro = (
        "You hear the sound of an explosion. The scene is chaotic, and people are injured all around. "
        "You are the only medical professional available. What will you do first?"
    )
    await channel.send(scenario_intro)

    # Wait for user response (as if it was a real scenario)
    def check(m):
        return m.author == member and m.channel == channel

    try:
        user_message = await bot.wait_for('message', check=check, timeout=60)
    except asyncio.TimeoutError:
        await channel.send("Time's up! In a real scenario, delays can be costly.")
        return

    # Stage 3: GPT Response to User Action
    gpt_response = generate_gpt_response(user_message.content)
    await channel.send(f"**GPT Response**: {gpt_response}")

    # Stage 4: Scenario Escalation
    escalation_message = (
        "Suddenly, the weather worsens. Rain is pouring, and some of the patients are at risk of hypothermia. "
        "You must make critical decisions quickly. How will you handle the situation?"
    )
    await channel.send(escalation_message)

    try:
        user_message = await bot.wait_for('message', check=check, timeout=60)
    except asyncio.TimeoutError:
        await channel.send("Time's up! The situation has worsened.")
        return

    # Stage 5: GPT Response to User's Second Action
    gpt_response = generate_gpt_response(user_message.content)
    await channel.send(f"**GPT Response**: {gpt_response}")

    # Stage 6: Scenario Conclusion
    conclusion_message = (
        "The emergency services have arrived. The patients are being transported to the hospital, and the scene is stabilizing. "
        "Great job handling the situation under pressure!"
    )
    await channel.send(conclusion_message)

    # Send a PM to the user with a summary and link to GitHub
    summary_message = (
        f"Thank you for participating in the demo, {member.mention}. "
        "You can review the scenario in the `#demo` channel, and check out our GitHub for more details:\n"
        "https://github.com/Mhalali/Mass_Casualty_Incident_Project"
    )
    try:
        await member.send(summary_message)
    except discord.Forbidden:
        await channel.send(f"Could not send a PM to {member.mention}, but here’s the GitHub link: https://github.com/Mhalali/Mass_Casualty_Incident_Project")

# Event: User joins the #demo channel
@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    # If a user sends a message in #demo channel
    if message.channel.name == 'demo':
        await run_demo_stages(message.channel, message.author)

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
