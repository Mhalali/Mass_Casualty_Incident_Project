# MCI Bot (Mass Casualty Incident Bot) - Developer Documentation

This document contains all the technical details needed for setting up, running, and maintaining the MCI Bot. It is intended for developers who need to manage the bot, including setting up Speech-to-Text (STT), Text-to-Speech (TTS), and deploying it to a server.

## Setup Instructions

### Prerequisites

- **Microsoft Azure Account**: Sign up for a free Azure account if you don't already have one. Enable Speech Services for STT and TTS.
- **Python 3.x**: Ensure Python 3.x is installed on your machine.
- **Git**: Ensure Git is installed for version control.

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
    AZURE_SPEECH_KEY=your-azure-speech-key
    AZURE_REGION=your-azure-region
    ```

    These environment variables are required to authenticate with Discord and Azure.

3. **Install Required Packages:**
    Install the required Python packages by running:
    ```bash
    pip install -r requirements.txt
    ```

### Running the Bot Locally

1. **Start the Bot:**
    Once you've set up the environment variables and installed the dependencies, you can start the bot by running:
    ```bash
    python MCIBot.py
    ```

2. **Admin Setup Command:**
    - Run `!setupadmin` in Discord to create all the necessary roles and channels for the bot.

### Hosting the Bot

The bot can be hosted on various platforms to ensure it runs continuously. Below are some recommended hosting solutions:

#### **Option 1: Heroku (Free Tier)**
1. Push your code to a Heroku app.
2. Set environment variables (`DISCORD_TOKEN`, `AZURE_SPEECH_KEY`, etc.) through the Heroku dashboard.
3. Set up **GitHub integration** for automatic deployments when the repository is updated.

#### **Option 2: Microsoft Azure App Service**
1. Use Azure App Service for hosting. This offers tight integration with other Azure services (like STT and TTS).
2. Deploy the bot code to Azure using **GitHub Actions** or **Azure CLI**.
3. Set environment variables through Azure’s configuration options.

#### **Option 3: DigitalOcean (Paid Hosting)**
1. Set up a **Virtual Private Server (VPS)** on DigitalOcean for more control.
2. Use SSH to connect to the server, and run the bot using a process manager like **pm2** to keep it online 24/7.

### Deployment Integration (Optional)

You can set up **automatic deployment** from GitHub using platforms like **Heroku** or **Azure App Service**. When you push changes to your GitHub repository, the hosting service will automatically update the live version of the bot.

## License

This project is proprietary. Developers may not use, modify, or distribute the code without explicit permission from the owner.

For inquiries or collaboration, please contact:
**Mohamed Alali**  
Email: Mhalali@dubaihealth.ae
