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
curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" -d chat_id="$CHAT_ID" -d text="$1" > /dev/null
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


### Step 5: Install and Activate the Server
Move the service file to the Linux system directory, lock it into the boot sequence, and turn it on permanently. Run these commands one by one:

```bash

# 1. Tell Linux to refresh its service list
sudo systemctl daemon-reload

# 2. Enable the bot to start automatically every time the Pi boots
sudo systemctl enable telegram-notify.service

# 3. Start the bot right now!
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

---

## 💾 Automated Raspberry Pi Backup (SD → USB → Google Drive)

This project includes an optional “full SD card image” backup system that:

1. Creates a compressed image of your SD card (`dd` + `pigz`)
2. Saves it to an external USB drive
3. Uploads it to Google Drive using `rclone`
4. Sends Telegram notifications on start/success/failure

### 📁 Where to put the backup README

Place the detailed reference document here (recommended):

- `docs/backup/README.md`

And link to it from this main README (example link path):

- `docs/backup/README.md`

### 🧩 Architecture Overview

```
┌──────────────┐       dd + pigz        ┌──────────────────┐
│  SD Card     │ ─────────────────────▶  │  USB Drive       │
│ /dev/mmcblk0 │                         │ /mnt/usb_backup  │
└──────────────┘                         └──────┬───────────┘
                                                │  rclone copy
                                                ▼
                                         ┌──────────────────┐
                                         │  Google Drive     │
                                         │  pi_backups/      │
                                         └──────────────────┘

Telegram notifications are sent at:
  🔄 Backup start
  ✅ Backup success (with file size and duration)
  ❌ Backup failure (with error context)
```

### ⚙️ Script Configuration Reference

All configuration lives at the top of:

- `scripts/auto_backup.sh`

| Variable | Default | Description |
|---|---|---|
| `SOURCE_DEVICE` | `/dev/mmcblk0` | Block device to image (your SD card) |
| `USB_MOUNT` | `/mnt/usb_backup` | Mount point of external USB drive |
| `LOCAL_BACKUP_DIR` | `${USB_MOUNT}/pi_backups` | Folder on USB for backup images |
| `RCLONE_REMOTE` | `gdrive` | Name of your rclone remote |
| `CLOUD_BACKUP_DIR` | `pi_backups` | Folder on Google Drive |
| `LOCAL_RETENTION_DAYS` | `30` | Auto-delete local backups older than N days |
| `CLOUD_RETENTION_DAYS` | `60` | Auto-delete cloud backups older than N days |
| `LOG_FILE` | `/var/log/pi_backup.log` | Path to log file |
| `SECRETS_FILE` | `~/.backup_secrets` | Path to file with Telegram credentials |

### 🔐 Secrets File Format

Create `~/.backup_secrets` with:

```bash
BACKUP_BOT_TOKEN="123456:ABC-your-token-here"
BACKUP_CHAT_ID="your_numeric_chat_id"
```

Then lock it down:

```bash
chmod 600 ~/.backup_secrets
```

> **⚠️ Never commit this file to Git.** Your `.gitignore` should exclude it.

### ♻️ Restore Procedure (Write image to a new SD card)

1. Insert the new SD card into a PC/Mac/other Pi.
2. Find the device name (`/dev/sdX` or `/dev/mmcblk0`):
   ```bash
   lsblk
   ```
3. Decompress and write:
   ```bash
   sudo gunzip -c /mnt/usb_backup/pi_backups/FILENAME.img.gz | sudo dd of=/dev/sdX bs=4M status=progress
   ```
4. Eject, insert into your Pi, and boot.

### 🧯 Troubleshooting

| Problem | Solution |
|---|---|
| `pigz: command not found` | `sudo apt install pigz` |
| `rclone: command not found` | `sudo apt install rclone` |
| USB drive not mounted | Check `lsblk` and re-mount; verify `/etc/fstab` |
| rclone auth expired | Re-run `rclone config reconnect gdrive:` |
| Telegram messages not arriving | Verify token/chat ID; test with `curl` manually |
| Backup takes too long | Use `-1` (fast) compression; consider excluding boot partition |
| Disk full on USB | Reduce `LOCAL_RETENTION_DAYS` or use a larger drive |


# 🗑️ Auto-Empty Google Drive Trash (Daily)

This guide sets up an automatic daily job that empties your **Google Drive Trash** using **Google Apps Script**.

> This is useful if your backup workflow (e.g., via `rclone`) frequently deletes/overwrites files and you want to reclaim Google Drive space automatically.

---

## ✅ What this does

- Runs a Google Apps Script function once per day
- Permanently empties your Google Drive Trash

---

## 🧠 Script Code (Google Apps Script)

Create a script with this function:

```javascript
function emptyMyTrash() {
  Drive.Files.emptyTrash();
}
```

---

## 🛠️ Step-by-step Setup (Google Apps Script)

### 1) Open Google Apps Script
- In Google Drive: **New → More → Google Apps Script**
- Or open Apps Script from the Google Workspace launcher.

### 2) Create a new project
- Name it something like: **Drive Trash Auto Empty**

### 3) Enable the Advanced Drive Service (Required)
`Drive.Files.emptyTrash()` requires enabling the **Advanced Drive Service**.

In the Apps Script editor:

1. Click **Services** (puzzle-piece icon or “+” icon on the left sidebar)
2. Add **Drive API**
3. Open **Project Settings** (gear icon) and make sure a **Google Cloud Platform project** is linked (Apps Script will guide you if needed)

### 4) Paste the code
- Open `Code.gs` (or create it if needed)
- Paste the code:

```javascript
function emptyMyTrash() {
  Drive.Files.emptyTrash();
}
```

### 5) Run once manually (Authorize permissions)
1. At the top toolbar, select function: **emptyMyTrash**
2. Click **Run**
3. Approve the permissions prompts (it needs access to manage your Drive)

### 6) Create the daily trigger
1. Left sidebar → **Triggers** (clock icon)
2. Click **Add Trigger**
3. Configure:
   - **Choose which function to run:** `emptyMyTrash`
   - **Select event source:** `Time-driven`
   - **Select type of time based trigger:** `Day timer`
   - Choose a time window (example: **03:00–04:00**)

### 7) Confirm it’s working
After it runs at least once:

- Open Apps Script → **Executions** (or “Runs”) to see status
- Check Google Drive → Trash should be empty after a successful run

---

## ⚠️ Notes / Warnings

- This empties Trash for the **Google account that owns the Apps Script project** (the one you authorize with).
- If your backups are stored in a **different Google account** or in a **Shared Drive**, you must create/authorize the script under that correct account (or use a different approach).
- Emptying trash is **permanent** (cannot be undone).

---
