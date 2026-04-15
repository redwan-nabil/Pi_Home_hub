# 🖨️ Ultimate Raspberry Pi Cloud Print & Scan Server + Automated Backup System

Turn a standard USB printer/scanner into a global, cloud-connected powerhouse **and** keep your entire Raspberry Pi backed up automatically to a USB drive and Google Drive. This system allows you to print and scan from anywhere in the world using your phone, your Windows PC, or an automated Telegram Bot—complete with payment verification, intelligent duplexing, and a rock-solid automated backup pipeline.

---

## 📑 Table of Contents

1. [Features](#-features)
2. [Phase 1 — Cloud Network (Tailscale)](#-phase-1-the-cloud-network-tailscale)
3. [Phase 2 — Print Server (CUPS)](#-phase-2-the-print-server-cups)
4. [Phase 3 — Connecting Your Devices](#-phase-3-connecting-your-devices)
5. [Phase 4 — Cloud Scanner (Scanservjs)](#-phase-4-cloud-scanner-scanservjs)
6. [Phase 5 — Telegram Credentials](#-phase-5-get-your-telegram-credentials-bot-token--admin-id)
7. [Phase 6 — Telegram Automation Bot](#-phase-6-the-telegram-automation-bot)
8. [How to Use the Bot & Cautions](#-how-to-use-the-bot--cautions)
9. [Emergency Commands Cheat Sheet](#-essential--emergency-commands-cheat-sheet)
10. [Automated Raspberry Pi Backup System](#-automated-raspberry-pi-backup-system)
11. [Security — Protecting Your Secrets](#-security--protecting-your-secrets)

---

## ✨ Features

* **🌍 Global Access:** Print from any network in the world via Tailscale VPN.
* **💻 Windows Native Printing:** Uses "Raw Mode" so your Windows PC controls all printing preferences (paper type, quality, margins) perfectly.
* **📱 Mobile Printing:** Seamlessly connect Android devices via the Mopria Print app.
* **🤖 Telegram Business Bot:** Let customers send PDFs to a Telegram bot, select color/duplex options, and verify payments before printing.
* **📄 Smart Duplexing:** The bot automatically injects blank pages into odd-numbered PDFs to prevent CUPS duplexing bugs—you just flip the stack!
* **📸 Cloud Scanner:** Scan documents directly to your browser using `scanservjs`.
* **💾 Automated Backups:** Full SD-card image backup to USB + Google Drive with Telegram notifications, local & cloud retention, and logging.

---

## 🛠️ Phase 1: The Cloud Network (Tailscale)

To access your printer from outside your house securely, we use Tailscale.

1. **Install Tailscale on the Pi:**
   ```bash
   curl -fsSL https://tailscale.com/install.sh | sh
   ```
2. **Connect the Pi to your account:**
   ```bash
   sudo tailscale up
   ```
   (Click the link provided in the terminal to log in and authorize the Pi).

3. **Find your Magic IP:**
   ```bash
   tailscale ip -4
   ```
   Save this IP Address! We will use it for everything. (Example: `100.x.x.x`)

4. **Install Tailscale on your other devices:** Download the Tailscale app on your Windows PC and Android phone, log in, and leave it running in the background.

---

## 🖨️ Phase 2: The Print Server (CUPS)

CUPS is the engine that drives Linux printing.

1. **Install CUPS:**
   ```bash
   sudo apt update
   sudo apt install cups -y
   sudo usermod -a -G lpadmin $USER
   sudo cupsctl --remote-any
   sudo systemctl restart cups
   ```

2. **Access the CUPS Web Interface:**
   Open a browser on your PC or phone (while connected to Tailscale) and go to:
   👉 `https://YOUR_TAILSCALE_IP:631`
   > **Note:** Your browser will say "Warning: Not Secure". Click **Advanced → Proceed anyway**. Log in with your Pi's username and password.

3. **Add Printer #1 (For Mobile & Telegram Bot):**
   - Go to **Administration** → **Add Printer**.
   - Select your USB Printer from the list.
   - Name it: **`EpsonMobile`** *(Make sure to check "Share This Printer")*.
   - Select your printer's Make and Model to install the standard driver.
   - Set the default paper size to **A4**.

4. **Add Printer #2 (For Windows RAW Mode):**
   We need a second "virtual" printer for Windows so Windows can handle the complex printing preferences (like glossy photo paper).
   - Go to **Administration** → **Add Printer**.
   - Select the exact same USB Printer again.
   - Name it: **`EpsonWindows`** *(Make sure to check "Share This Printer")*.
   - **CRITICAL STEP:** For the "Make", scroll to the very top and select **Raw**.
   - Click **Add Printer**.

---

## 💻 Phase 3: Connecting Your Devices

### Adding to Windows (Via Tailscale)

1. Open **Windows Settings** → **Printers & Scanners** → **Add a printer or scanner**.
2. Wait 3 seconds, then click **The printer that I want isn't listed**.
3. Select **Select a shared printer by name**.
4. Type this exact URL:
   ```
   http://YOUR_TAILSCALE_IP:631/printers/EpsonWindows
   ```
5. Click **Next**. Windows will ask for a driver. Select your printer brand and model from the Windows list (or click "Have Disk" to install official drivers).
6. Print a test page! You can now edit all printer preferences via Windows.

### Adding to Android Mobile (Via Mopria)

1. Install the **Mopria Print Service** app from the Google Play Store.
2. Open Mopria → Click the **3 dots** (Menu) → **Add Printer**.
3. Click the **+** button to add manually.
4. **Name:** `Pi Printer`
5. **Printer URL:**
   ```
   http://YOUR_TAILSCALE_IP:631/printers/EpsonMobile
   ```
6. You can now print directly from any app on your phone!

---

## 📸 Phase 4: Cloud Scanner (Scanservjs)

Turn your USB scanner into a web app accessible from anywhere.

1. **Install dependencies and the app:**
   ```bash
   sudo apt install sane sane-utils imagemagick tesseract-ocr -y
   curl -sL https://raw.githubusercontent.com/sbs20/scanservjs/main/install.sh | sudo bash
   ```

2. **Access your scanner:**
   Open a browser (connected to Tailscale) and go to:
   👉 `http://YOUR_TAILSCALE_IP:8080`

   You can now scan documents directly to your phone/PC browser!

---

## 🔑 Phase 5: Get Your Telegram Credentials (Bot Token + Admin ID)

Before running the Telegram bot, you need two values:

### 1) Bot Token (from @BotFather)

1. Open Telegram and search for [**@BotFather**](https://t.me/botfather) (look for the verified blue checkmark).
2. Send:
   ```
   /newbot
   ```
3. Follow the prompts to set a name and username for your bot.
4. BotFather will give you a long API token like:
   ```
   123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   ```

✅ Save this token — you'll paste it into `businessbot.py` as `BOT_TOKEN`.

### 2) Admin ID (from @userinfobot)

1. Open Telegram and search for [**@userinfobot**](https://t.me/userinfobot).
2. Tap **Start**.
3. It will reply with your Telegram numeric ID (usually 9–10 digits).

✅ Save this ID — you'll paste it into `businessbot.py` as `ADMIN_ID`.

---

## 🤖 Phase 6: The Telegram Automation Bot

This bot handles customer PDF files, automated duplexing, and payment verification.

1. **Install Python Dependencies:**
   ```bash
   sudo apt install python3-pip -y
   pip3 install pyTelegramBotAPI psutil PyPDF2 --break-system-packages
   ```

2. **Create the Bot Script:**
   ```bash
   nano /home/redwannabil/businessbot.py
   ```
   Paste your complete Python bot code into this file. Save and exit (`Ctrl+X`, `Y`, `Enter`).

   > **⚠️ Security:** Never hard-code your `BOT_TOKEN` or `ADMIN_ID` directly in source files you push to GitHub. See the [Security](#-security--protecting-your-secrets) section below.

3. **Verify Your Printer Name:**
   ```bash
   lpstat -p
   ```
   The output should show your printer(s). Use the exact name in your bot code (e.g., `EpsonMobile`).

4. **Create the System Service (Runs Bot Forever):**
   ```bash
   sudo nano /etc/systemd/system/printerbot.service
   ```
   Paste this exact code:
   ```ini
   [Unit]
   Description=Telegram Printer and Scanner Bot
   After=network.target

   [Service]
   User=redwannabil
   WorkingDirectory=/home/redwannabil
   ExecStart=/usr/bin/python3 /home/redwannabil/businessbot.py
   Restart=always
   RestartSec=10

   [Install]
   WantedBy=multi-user.target
   ```
   Save and exit (`Ctrl+X`, `Y`, `Enter`).

5. **Activate the Bot:**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable printerbot.service
   sudo systemctl start printerbot.service
   ```

Your bot is now live and will survive system reboots automatically!

---

## 💡 How to Use the Bot & Cautions

### User Flow

1. Customer sends a PDF to the bot.
2. Bot asks for **Color vs. B/W**, and **One-Sided vs. Both-Sided**.
3. Bot asks for payment details.
4. Admin receives the file, payment proof, and exact printing preferences.
5. Admin clicks **"Verify"**.
6. If Both-Sided, the bot automatically prints odd pages, injects a blank page (if needed), pauses, and tells the admin to flip the stack and click **"Done"**.

### ⚠️ Important Cautions for Reliability

* **Never separate pages manually:** When the bot asks you to reverse the stack for duplexing, grab the entire stack, flip it, and put it in the tray. The bot's PyPDF2 blank-page-injection handles the math for you.
* **Paper Jams:** If the printer jams, clear the jam physically. You may need to use the `cancel -a` command (see below) to clear the broken job out of CUPS before trying again.
* **Keep Printer On:** For the best UX, keep the printer powered on during business hours. If it is off, the bot will kindly place customer jobs in a "waiting room" until you turn the printer on.

---

## 🚨 Essential & Emergency Commands Cheat Sheet

Keep these commands handy. They are all you need to maintain the server.

### 🤖 Bot Management

| Action | Command |
|---|---|
| Check if Bot is running/crashing | `sudo systemctl status printerbot.service` |
| View Live Bot Logs/Errors | `sudo journalctl -u printerbot.service -f` |
| Edit Bot Code | `nano /home/redwannabil/businessbot.py` |
| Restart Bot (Apply Code Changes) | `sudo systemctl restart printerbot.service` |
| Stop Bot | `sudo systemctl stop printerbot.service` |
| Start Bot | `sudo systemctl start printerbot.service` |

### 🖨️ Printer Emergencies

| Action | Command |
|---|---|
| Cancel ALL stuck print jobs | `cancel -a` |
| See what the printer is doing | `lpstat -p EpsonMobile` |
| Restart CUPS Print Engine | `sudo systemctl restart cups` |

### 📸 Scanner Emergencies

| Action | Command |
|---|---|
| See if Pi detects the scanner | `scanimage -Lv` |
| Restart Scanner Web App | `sudo systemctl restart scanservjs` |

---

## 💾 Automated Raspberry Pi Backup System

This section covers the **`auto_backup.sh`** script located in [`scripts/auto_backup.sh`](scripts/auto_backup.sh). It creates a compressed full-disk image of your Raspberry Pi's SD card, saves it to an external USB drive, uploads it to Google Drive via `rclone`, sends Telegram notifications at every stage, and automatically rotates old backups.

### Prerequisites

| Requirement | Purpose |
|---|---|
| External USB drive mounted at a known path (e.g., `/mnt/usb_backup`) | Local backup storage |
| [`pigz`](https://zlib.net/pigz/) | Parallel gzip compression (much faster than `gzip`) |
| [`rclone`](https://rclone.org/) | Uploads backups to Google Drive (or any cloud) |
| A Telegram Bot Token + Chat ID | Sends status notifications |

Install `pigz` and `rclone`:

```bash
sudo apt update
sudo apt install pigz rclone -y
```

### Step 1: Mount Your USB Drive

1. Plug in a USB drive and find its device name:
   ```bash
   lsblk
   ```
2. Create a mount point and mount it:
   ```bash
   sudo mkdir -p /mnt/usb_backup
   sudo mount /dev/sda1 /mnt/usb_backup
   ```
3. **Make it permanent** by adding a line to `/etc/fstab`:
   ```bash
   echo '/dev/sda1 /mnt/usb_backup auto defaults,nofail 0 2' | sudo tee -a /etc/fstab
   ```

### Step 2: Configure rclone for Google Drive

Run the interactive configuration wizard:

```bash
rclone config
```

1. Choose **`n`** for a new remote.
2. Name it **`gdrive`** (or whatever you prefer — update the script to match).
3. Choose **Google Drive** from the list.
4. Follow the OAuth prompts (you may need to paste a URL into a browser on another machine if you are running headless).
5. Choose **Full access** when asked about scope.
6. Verify with:
   ```bash
   rclone lsd gdrive:
   ```
   You should see your Google Drive folders listed.

### Step 3: Set Up Telegram Notifications

The backup script sends Telegram messages at the start, on success, and on failure.

1. You already have a Bot Token and your Chat ID from [Phase 5](#-phase-5-get-your-telegram-credentials-bot-token--admin-id).
2. Create a **private config file** on your Pi (this file must **never** be committed to Git):
   ```bash
   nano ~/.backup_secrets
   ```
   Add:
   ```bash
   BACKUP_BOT_TOKEN="123456:ABC-your-token-here"
   BACKUP_CHAT_ID="your_numeric_chat_id"
   ```
   Save and lock it down:
   ```bash
   chmod 600 ~/.backup_secrets
   ```

### Step 4: Install the Backup Script

Copy the script from this repository to your Pi:

```bash
sudo cp scripts/auto_backup.sh /usr/local/bin/auto_backup.sh
sudo chmod +x /usr/local/bin/auto_backup.sh
```

> **Important:** Open the script and review the configuration variables at the top (mount path, rclone remote name, retention days). Adjust them to match your setup.

### Step 5: Schedule with systemd Timer (Recommended) or Cron

#### Option A — systemd Timer

Create the service unit:

```bash
sudo nano /etc/systemd/system/pi-backup.service
```

```ini
[Unit]
Description=Automated Raspberry Pi SD Card Backup
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/auto_backup.sh
User=root
```

Create the timer unit:

```bash
sudo nano /etc/systemd/system/pi-backup.timer
```

```ini
[Unit]
Description=Run Pi Backup Weekly

[Timer]
OnCalendar=Sun *-*-* 03:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:

```bash
sudo systemctl daemon-reload
sudo systemctl enable pi-backup.timer
sudo systemctl start pi-backup.timer
```

Verify it's scheduled:

```bash
systemctl list-timers --all | grep pi-backup
```

#### Option B — Cron

```bash
sudo crontab -e
```

Add this line to run every Sunday at 3 AM:

```
0 3 * * 0 /usr/local/bin/auto_backup.sh >> /var/log/pi_backup.log 2>&1
```

### Logging

The script writes detailed logs to **`/var/log/pi_backup.log`** by default. View them with:

```bash
sudo tail -f /var/log/pi_backup.log
```

Or see the last backup run:

```bash
sudo tail -50 /var/log/pi_backup.log
```

### Retention Settings

| Setting | Default | Description |
|---|---|---|
| `LOCAL_RETENTION_DAYS` | `30` | Delete local USB backups older than this many days |
| `CLOUD_RETENTION_DAYS` | `60` | Delete Google Drive backups older than this many days |

Edit these values at the top of `auto_backup.sh` to match your storage capacity and needs.

### Testing the Backup

1. **Dry-run** — manually execute the script and watch the output:
   ```bash
   sudo /usr/local/bin/auto_backup.sh
   ```
2. Check that:
   - A `.img.gz` file appears in your USB mount path.
   - The file also appears in your Google Drive (`rclone ls gdrive:pi_backups/`).
   - You receive Telegram notifications (start, success, or failure).
3. Check the log:
   ```bash
   cat /var/log/pi_backup.log
   ```

### Emergency & Maintenance Commands

| Action | Command |
|---|---|
| Run backup manually | `sudo /usr/local/bin/auto_backup.sh` |
| Check timer status | `systemctl list-timers --all` (look for pi-backup) |
| View backup log | `sudo tail -f /var/log/pi_backup.log` |
| List local backups | `ls -lh /mnt/usb_backup/pi_backups/` |
| List cloud backups | `rclone ls gdrive:pi_backups/` |
| Cancel a running backup | `sudo kill $(pgrep -f auto_backup)` |
| Restore from backup | See [docs/backup.md](docs/backup.md#restore-procedure) for the full restore command |

---

## 🔒 Security — Protecting Your Secrets

**Never commit secrets** (Bot Tokens, Chat IDs, API keys, App Passwords) to this repository.

### Recommended Approach

1. **Use a separate config file** that is excluded from Git:
   ```bash
   # Example: ~/.backup_secrets
   BACKUP_BOT_TOKEN="your_token_here"
   BACKUP_CHAT_ID="your_chat_id_here"
   ```
   ```bash
   chmod 600 ~/.backup_secrets
   ```

2. **Source it in your scripts** instead of hard-coding values:
   ```bash
   source ~/.backup_secrets
   ```

3. **For the Python bot**, use environment variables or a `.env` file:
   ```python
   import os
   BOT_TOKEN = os.environ.get("BOT_TOKEN")
   ADMIN_ID  = int(os.environ.get("ADMIN_ID", "0"))
   ```

4. **Make sure `.gitignore` blocks secret files.** This repository's `.gitignore` already excludes:
   - `.env` and `.env.*`
   - `.backup_secrets` and `*.secrets`
   - `*.log`

> ⚠️ **If you accidentally committed a token**, revoke it immediately via [@BotFather](https://t.me/botfather) (`/revoke`) and generate a new one. Rotating secrets is free; a compromised bot is not.

---

## 📜 License

This project is provided as-is for personal and educational use.
