# 🚀 Raspberry Pi Control Bot

A bulletproof, remote administration Telegram bot for the Raspberry Pi 5. This system allows you to monitor performance, execute root-level commands securely via 2FA Email verification, and features an autonomous background radar that protects the Pi from severe weather/thunderstorms.

It runs as a native Linux `systemd` service, meaning it is immune to crashes, survives reboots, and alerts you the moment the Pi powers on or shuts down.

---

## ✨ Key Features

* **📊 Live Performance Telemetry:** Monitors CPU usage, RAM, Temperature, GPU Memory, Internet Speed (Ping/Down/Up), and hardware-level **Power Draw (Watts)** using the Pi 5's internal PMIC.
* **🔒 2FA Secure Commands:** Destructive commands (`/reboot`, `/shutdown`, `/clear cache`) are locked behind a Two-Factor Authentication system. The bot sends a 6-digit OTP to your configured email address, which you must enter in Telegram to authorize the action.
* **⛈️ Autonomous Thunderstorm Protection:** A background thread pings the OpenWeatherMap API every 15 minutes. 
  * If a thunderstorm is overhead, it checks if you are home (by pinging your phone's IP address) or actively working on the Pi via SSH. 
  * If you are away, it sends an emergency Telegram alert, safely stops Docker containers, and executes an emergency shutdown to protect your hardware from power surges.
* **🤖 Native Systemd Integration:** Automatically boots with the Pi. Sends "🟢 RASPBERRY PI ONLINE" and "🔴 RASPBERRY PI OFFLINE" messages to Telegram during startup and shutdown sequences.

---

## 🛠️ Prerequisites

Before installing, you will need:
1. **Telegram Bot Token:** Create a bot via [@BotFather](https://t.me/botfather) on Telegram.
2. **Your Telegram User ID:** Get your 9-10 digit ID from a bot like [@userinfobot](https://t.me/userinfobot) so the bot only talks to *you*.
3. **Gmail App Password:** A 16-character App Password from Google Account Security (used for sending the 2FA OTP emails).
4. **OpenWeatherMap API Key:** A free API key from [OpenWeatherMap](https://openweathermap.org/) for the storm radar.

## 🛠️ Prerequisites & API Setup

Before running the installation commands, you need to gather 4 unique credentials. Here is exactly how to get them for free.

### 1. Telegram Bot Token
This is the unique password that allows your Python script to control a Telegram bot.
1. Open the Telegram app on your phone or PC.
2. Search for the official [**@BotFather**](https://t.me/botfather) (look for the verified blue checkmark).
3. Send the command: `/newbot`
4. Choose a display name for your bot (e.g., "My Pi Server").
5. Choose a unique username. **It must end in 'bot'** (e.g., `nabil_server_bot`).
6. BotFather will reply with a massive message containing your **HTTP API Token** (it looks like `1234567890:ABCDefGhIjKlMnOpQrStUvWxYz`). Copy this and save it.

### 2. Your Telegram User ID
You need to hardcode your personal ID into the script so the bot ignores commands from strangers.
1. Open Telegram and search for [**@userinfobot**](https://t.me/userinfobot) (or @getmyid_bot).
2. Click **Start** or send it any message.
3. The bot will instantly reply with your `Id` (a 9 or 10-digit number like `1435882929`). 
4. Copy this exact number.

### 3. Gmail App Password (For 2FA)
Google blocks scripts from logging in with your normal email password. You need to generate a secure "App Password".
1. Go to your [Google Account Security page](https://myaccount.google.com/security).
2. Scroll down to **How you sign in to Google**. Ensure **2-Step Verification is turned ON**.
3. In the search bar at the top of the Google Account page, search for **"App passwords"**.
4. You may be prompted to enter your normal Google password to verify it's you.
5. In the "App name" text box, type something like "Pi Server 2FA" and click **Create**.
6. Google will display a **16-letter code** in a yellow box. Copy this code (you can remove the spaces when you paste it into your script). *Note: You will only see this code once!*

### 4. OpenWeatherMap API Key (For Radar)
This allows your Pi to check the live sky conditions over your house.
1. Go to [OpenWeatherMap.org](https://openweathermap.org/) and click **Sign Up** to create a free account.
2. Once logged in, click on your profile name in the top right corner and select **My API keys**.
3. You will see a "Default" key already generated for you (a long string of numbers and letters). 
4. Copy this key. *(Note: New OpenWeatherMap accounts sometimes take 1 to 2 hours for their API keys to officially activate. If the radar throws an error initially, just wait!)*
---

## 🚀 Installation & Setup Guide

Since this is a lightweight, 2-file architecture, we will build the files directly on the Raspberry Pi rather than cloning the whole repository. 

Run these commands in your Raspberry Pi terminal to implement the system from scratch.

### Step 1: Install Python Dependencies
The bot requirres a few Python libraries to interact with Telegram and read system stats. Run:

```
sudo apt update
sudo apt install python3-pip -y
pip3 install pyTelegramBotAPI psutil speedtest-cli requests
```

### Step 2: Create the Bot Script
This is the main brain of the operation. We will create it in your home directory.

Open a new file:

```
nano ~/pi_control_bot.py
```
Copy the Python code from the pi_control_bot.py file in this repository and paste it into the terminal.

Important: Edit the BOT_TOKEN, ADMIN_ID, SENDER_EMAIL, EMAIL_APP_PASSWORD, and WEATHER_API_KEY variables with your actual credentials.

Save and exit (Ctrl+X, then Y, then Enter).

### Step 3: Create the Boot Alert Helper (pi_alert)
The service file relies on a small bash script to push boot/shutdown messages instantly to your phone. Let's create it in the system's local binaries folder:

Open a new file:
```
sudo nano /usr/local/bin/pi_alert
```
Paste this code inside (Replace YOUR_BOT_TOKEN and YOUR_CHAT_ID with your actual Telegram details):

```
#!/bin/bash
TOKEN="YOUR_BOT_TOKEN"
CHAT_ID="YOUR_CHAT_ID"
curl -s -X POST "[https://api.telegram.org/bot$TOKEN/sendMessage](https://api.telegram.org/bot$TOKEN/sendMessage)" -d chat_id="$CHAT_ID" -d text="$1" > /dev/null
```

Make it an executable command:
```
sudo chmod +x /usr/local/bin/pi_alert
```

### Step 4: Create the Systemd Service
Now we will create the configuration file that tells Linux to treat your bot like native hardware. We will put this directly into the system's core service folder.

Open a new service file:

```
sudo nano /etc/systemd/system/telegram-notify.service
```

Copy the code from the `telegram-notify.service` file in this repository and paste it into the terminal.
(Note: Ensure the `WorkingDirectory` and `ExecStart` paths in the code perfectly match the username on your Pi, e.g., `/home/username/`).

Save and exit (Ctrl+X, then Y, then Enter).

### Step 5: Activate the Server
Tell Linux that new "hardware" has been installed, lock it into the boot sequence, and turn it on permanently:

1. Tell Linux to refresh its service list
```
sudo systemctl daemon-reload
```
2. Enable the bot to start automatically every time the Pi boots
```
sudo systemctl enable telegram-notify.service
```
3. Start the bot right now!
```
sudo systemctl start telegram-notify.service
```

You should instantly receive a "🟢 RASPBERRY PI ONLINE" message on your telegram bot!

### Step 5: Install and Activate the Server
Move the service file to the Linux system directory, lock it into the boot sequence, and turn it on permanently. Run these commands one by one:

```bash
# 1. Copy the service file to the systemd folder
sudo cp telegram-notify.service /etc/systemd/system/

# 2. Tell Linux to refresh its service list
sudo systemctl daemon-reload

# 3. Enable the bot to start automatically every time the Pi boots
sudo systemctl enable telegram-notify.service

# 4. Start the bot right now!
sudo systemctl start telegram-notify.service
```

### 📱 Bot Commands
Send these commands to your bot in Telegram:

`/performance` - Runs a diagnostic check and returns CPU, Temp, Power Draw, RAM, and Internet Speeds.

`/reboot` - Triggers the 2FA lock. Upon entering the OTP, safely reboots the Pi.

`/shutdown` - Triggers the 2FA lock. Upon entering the OTP, safely shuts down the Pi.

`/clear cache` - Triggers the 2FA lock. Clears OS updates, temp PDF files, Linux journals, and RAM cache to free up space.

### 🔍 Troubleshooting & Logs
Because this runs as a native system service, you do not use standard text files for logs. Instead, use the official Linux journal tool.

To view the live feed of the bot (and see any errors):
```
sudo journalctl -u telegram-notify.service -f
```
(Press Ctrl + C to exit the live log view)

To stop the bot manually:
```
sudo systemctl stop telegram-notify.service
```
