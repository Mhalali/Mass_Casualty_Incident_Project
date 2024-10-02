# MCI Bot (Mass Casualty Incident Bot)

The MCI Bot is designed to assist in training healthcare professionals for Mass Casualty Incidents (MCI) through immersive, text-based simulations. It simulates real-time triage, treatment, and transport scenarios, helping users make critical decisions under stress. The bot operates within a Discord environment and aims to create an engaging and realistic training tool for professionals in emergency healthcare.

## Table of Contents
- [Key Features](#key-features)
- [Latest Changes](#latest-changes)
- [How It Works](#how-it-works)
  - [Joining the Demo](#joining-the-demo)
  - [Game Master Setup](#game-master-setup)
- [Powering the MCI Bot](#powering-the-mci-bot)
- [Future Goals](#future-goals)
- [License](#license)


<img width="327" alt="thmb" src="https://github.com/user-attachments/assets/13840a5e-3192-4238-a4ee-0c6462eae095">


[![Watch the video](https://github.com/user-attachments/assets/ab489e57-ffcb-4d15-9d6d-5815fdaa5652)


## Key Features

- **Interactive Scenarios**: The bot presents various triage, treatment, and transport situations that challenge users to think critically and respond effectively.
  
- **Demo Mode**: An interactive 5-minute demo allows users to experience a condensed version of the full simulation. The player must navigate decisions and communicate effectively during a high-stress scenario.

- **Real-time Analysis**: The bot evaluates user performance and provides feedback on key decisions, analyzing the user’s ability to manage time, resources, and communication during the simulation.

- **Natural Language Processing**: Enhanced NLP provides a more immersive, game-like experience as the bot responds organically to user inputs without guiding them step-by-step.

- **Post-Scenario Debriefing**: After each scenario, the bot sends an analysis of the player’s performance, highlighting strengths and areas for improvement. This feedback is sent via PM and saved in a log channel for review.

## Latest Changes


- **Removed Time Restrictions**: Players now have more freedom to explore the simulation, ask questions, and make decisions at their own pace without a rigid time limit.
  
- **Scenario Flexibility**: Players are no longer rushed through stages. The bot will provide adequate time for responses and will only advance when the player is ready, allowing for a more organic experience.

- **Highlight Key Words**: The bot highlights key words (e.g., "victims," "accident type") to make the scenarios more engaging and to help players focus on critical information.

- **Enhanced Commands**: The bot includes additional commands like `!reset` to give facilitators more control over the game flow, allowing them to restart or pause the simulation when needed.

## How It Works

### Joining the Demo

1. Players can join the `#demo` channel on Discord.
2. The bot will introduce a scenario and provide instructions to simulate a real-world MCI.
3. Players make decisions, and the bot adjusts the scenario dynamically based on their responses.
4. The demo ends with a post-scenario debrief, including a performance review.

### Game Master Setup

The Game Master can set up full training sessions using custom commands to control the simulation. Channels and roles for different parts of the simulation (triage, transport, treatment, etc.) can be configured, allowing for realistic, full-scale MCI training exercises.

## Powering the MCI Bot

The MCI Bot is powered by:

- **Microsoft Azure**: For infrastructure management and potential future integration of Speech-to-Text (STT) and Text-to-Speech (TTS) capabilities.
- **OpenAI GPT API**: Provides advanced NLP to create dynamic and realistic conversational experiences during the simulation.
- **Raspberry Pi**: The bot runs on a Raspberry Pi for low-cost, continuous operation with minimal resource consumption.

## Future Goals

- **Voice Integration**: While the current version is text-based, we plan to reintroduce voice functionality using Azure’s Speech Services for a fully voice-activated experience.
  
- **Biometric Sensor Integration**: Exploring the possibility of integrating biometric data (e.g., heart rate) into the game using health applications or sensors.

- **Expanded Scenarios**: Additional scenarios focusing on different types of emergencies and more roles for users to take on during training.

## License [![License](https://img.shields.io/badge/license-Proprietary-red)](./LICENSE)
This project is proprietary. You may not use, distribute, or modify this project without explicit permission from the owner.

For more details or collaboration inquiries, please contact:

**Mohamed Alali**  
mhalali@dubaihealth.ae




