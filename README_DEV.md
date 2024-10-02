# MCI Bot (Mass Casualty Incident Bot) - Developer Documentation

This document contains all the technical details needed for setting up, running, and maintaining the MCI Bot. It is intended for developers who need to manage the bot, focusing on its current text-based implementation, bot commands, and setup for running locally or on a Raspberry Pi.

## Setup Instructions

### Prerequisites

- **Python 3.x**: Ensure Python 3.x is installed on your machine or Raspberry Pi.
- **Git**: Ensure Git is installed for version control.
- **OpenAI API Key**: Obtain an OpenAI API key for the bot’s GPT integration.
- **Discord Developer Account**: Set up a Discord bot and obtain the token for authentication.

### Installation Steps

1. **Clone the Repository:**
    ```bash
    git clone https://github.com/MightyP00/MCI-Bot.git
    cd MCI-Bot
    ```

2. **Set Up Environment Variables:**
    Create a `.env` file in the root directory of the project with the following contents:
    ```bash
    DISCORD_TOKEN=your-discord-bot-token
    OPENAI_API_KEY=your-openai-api-key
    ```

    These environment variables are required to authenticate with Discord and OpenAI.

3. **Install Required Packages:**
    Install the required Python packages by running:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Bot Locally or on Raspberry Pi

1. **Start the Bot:**
    Once you've set up the environment variables and installed the dependencies, you can start the bot by running:
    ```bash
    python MCIBot.py
    ```

2. **Admin Setup Command:**
    - Run `!setupadmin` in Discord to create all the necessary roles and channels for the bot.
  
3. **Bot Commands:**
    - `!reset`: Resets the game and stops the simulation, waiting for players to start again.
    - More control commands are planned for future updates.

### Hosting the Bot

The bot can be hosted on various platforms to ensure it runs continuously. Below are the current hosting preferences:

#### **Option 1: Raspberry Pi (Preferred Solution)**
1. **Setup on Raspberry Pi**: Raspberry Pi 5 or similar hardware can be used to run the bot 24/7.
2. **Process Manager**: Use `pm2` or `systemd` to manage the bot process and ensure it remains running after reboots or failures.
3. **Port Forwarding**: Set up port forwarding if remote access is required, and use a dynamic DNS service for access via a public URL if needed.

#### **Option 2: Microsoft Azure App Service**
1. **Azure Hosting**: You can still host the bot on Azure using Azure App Service.
2. **GitHub Integration**: Set up GitHub Actions for CI/CD, allowing automatic deployments on push.
3. **Environment Variables**: Configure environment variables through Azure’s configuration settings for seamless bot operation.

### Deployment Integration (Optional)

You can set up **automatic deployment** from GitHub using **GitHub Actions** or **Azure App Service**. This will automatically update the live version of the bot whenever changes are pushed to the GitHub repository.

### Future Enhancements

- **Voice Re-Integration**: Although voice functionality has been removed for now, future versions may reintroduce Speech-to-Text (STT) and Text-to-Speech (TTS) using Azure's Speech Services.
- **Biometric Integration**: Exploring integration with health apps or sensors (e.g., heart rate monitors) to enhance the realism of the MCI scenarios.
- **Expanded Game Features**: Additional commands and control mechanisms for the bot to allow more flexibility and customization during simulations.

## License

This project is proprietary. Developers may not use, modify, or distribute the code without explicit permission from the owner.

For inquiries or collaboration, please contact:
**Mohamed Alali**  
Email: Mhalali@dubaihealth.ae