# 🖨️ Ultimate Raspberry Pi Cloud Print & Scan Server (Tailscale + CUPS + Scanservjs + Telegram Bot)

Turn a normal USB printer/scanner connected to a Raspberry Pi into a secure, global **cloud printing + cloud scanning** system you can use from anywhere via **Tailscale**.

You will get:
- **Windows printing (RAW mode)** so Windows controls all printing preferences (paper type, quality, margins, duplex, etc.)
- **Android printing (Mopria)**
- **Cloud scanner UI** via `scanservjs` (scan to browser)
- **Telegram Business Bot** (customers send PDFs → select color/duplex → payment verification → print / scan)

---

## ✅ Requirements

### Hardware
- Raspberry Pi (recommended: Raspberry Pi 3/4/5)
- MicroSD + Raspberry Pi OS (Lite or Desktop)
- USB Printer (and optional USB scanner, or printer+scanner combo)
- Stable power + stable internet

### Accounts / Apps
- A **Tailscale** account
- Tailscale installed on:
  - Raspberry Pi
  - Windows PC
  - Android phone
- Telegram account + a Telegram Bot token (from **@BotFather**)

---

## 🧱 Phase 0 — Start from Scratch (Raspberry Pi OS Setup)

1. Flash **Raspberry Pi OS** to your SD card (Raspberry Pi Imager recommended).
2. Boot the Pi and run:
   ```bash
   sudo apt update && sudo apt upgrade -y
   ```
3. (Optional but recommended) Set timezone/locale:
   ```bash
   sudo raspi-config
   ```

---

## 🌍 Phase 1 — Secure Global Network (Tailscale)

Tailscale gives your Pi a private IP (Magic IP) like `100.x.x.x`. You’ll use it to access CUPS and the scanner UI from anywhere.

### 1) Install Tailscale on the Pi
```bash
curl -fsSL https://tailscale.com/install.sh | sh
```

### 2) Connect the Pi to your Tailscale account
```bash
sudo tailscale up
```
- Open the login link shown in the terminal
- Approve the device

### 3) Get the Pi’s Tailscale IP (Magic IP)
```bash
tailscale ip -4
```
Example: `100.64.12.34`

✅ Save it. You will use it everywhere below as:
- `YOUR_TAILSCALE_IP` = `100.64.12.34`

### 4) Install Tailscale on other devices
- Install Tailscale on your **Windows PC** and **Android phone**
- Log in with the same Tailscale account
- Keep Tailscale running in background

---

## 🖨️ Phase 2 — Install & Configure Print Server (CUPS)

CUPS is the printing engine on Linux.

### 1) Install CUPS
```bash
sudo apt update
sudo apt install cups -y
sudo usermod -a -G lpadmin $USER
sudo cupsctl --remote-any
sudo systemctl restart cups
```

### 2) Open the CUPS Web UI (from any Tailscale-connected device)
In your PC/phone browser:
- `http://YOUR_TAILSCALE_IP:631`

Example:
- `http://100.64.12.34:631`

If asked to log in:
- username: your Pi username
- password: your Pi password

---

## 🖨️ Phase 3 — Add TWO Printers in CUPS (IMPORTANT)

You must add the **same physical printer twice**.

### Printer #1: Mobile + Telegram Bot printer (normal driver)
1. Go to **Administration → Add Printer**
2. Select your USB printer
3. Name it: **`EpsonMobile`** (or any name you prefer)
4. Check: **Share This Printer**
5. Choose correct **Make/Model** driver
6. Set default paper size to **A4**

✅ This printer is used for:
- Android (Mopria)
- Telegram bot printing

---

### Printer #2: Windows printer (RAW mode)
RAW mode allows Windows to control all printing preferences.

1. Go to **Administration → Add Printer**
2. Select the same USB printer again
3. Name it: **`EpsonWindows`**
4. Check: **Share This Printer**
5. **CRITICAL:** For “Make”, scroll to the very top and select **Raw**
6. Finish adding the printer

✅ This printer is used for:
- Windows printing with full Windows preferences

---

## 💻 Phase 4 — Add Printer to Windows (via Tailscale)

### 1) Ensure Tailscale is connected on Windows
Open Tailscale and confirm it’s connected (same tailnet as your Pi).

### 2) Add the RAW printer in Windows
1. Windows **Settings → Bluetooth & devices → Printers & scanners**
2. Click **Add device**
3. Wait a few seconds → click **“The printer that I want isn’t listed”**
4. Choose **Select a shared printer by name**
5. Enter this EXACT URL:
   ```
   http://YOUR_TAILSCALE_IP:631/printers/EpsonWindows
   ```
   Example:
   ```
   http://100.64.12.34:631/printers/EpsonWindows
   ```
6. Click Next
7. Windows will ask for a driver:
   - Select your printer brand/model from Windows list, OR
   - Click **Have Disk** to install official drivers

✅ Print a test page.
Now Windows controls: quality, margins, paper type, duplex, etc.

---

## 📱 Phase 5 — Add Printer to Android (Mopria)

### 1) Install Mopria
Install **Mopria Print Service** from the Play Store.

### 2) Add the printer manually
1. Open Mopria
2. Menu (3 dots) → **Add Printer**
3. Tap **+** (add manually)
4. Fill:
   - Name: `Pi Printer`
   - Printer URL:
     ```
     http://YOUR_TAILSCALE_IP:631/printers/EpsonMobile
     ```

Example:
```
http://100.64.12.34:631/printers/EpsonMobile
```

✅ Now you can print from any Android app.

---

## 📸 Phase 6 — Cloud Scanning (scanservjs)

This creates a browser-based scanner UI accessible through Tailscale.

### 1) Install dependencies
```bash
sudo apt update
sudo apt install sane sane-utils imagemagick tesseract-ocr -y
```

### 2) Install scanservjs
```bash
curl -sL https://raw.githubusercontent.com/sbs20/scanservjs/main/install.sh | sudo bash
```

### 3) Access scanservjs (from any device on Tailscale)
Open:
- `http://YOUR_TAILSCALE_IP:8080`

Example:
- `http://100.64.12.34:8080`

✅ Scan from phone/PC browser.

---

## 🤖 Phase 7 — Telegram Business Print/Scan Bot

This bot allows customers to:
- send PDFs
- select color & duplex
- submit payment details
- admin verifies payment
- bot prints (odd/even duplex workflow) or scans

---

## 🔑 Get Your Telegram Credentials (Bot Token + Admin ID)

Before running the Telegram bot, you need two values:

### 1) Bot Token (from @BotFather)
1. Open Telegram and search for **@BotFather**
2. Send:
   ```
   /newbot
   ```
3. Follow the prompts to set a name and username for your bot
4. BotFather will give you a long API token like:
   ```
   123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
   ```
✅ Save this token — you’ll paste it into `businessbot.py` as `BOT_TOKEN`.

---

### 2) Admin ID (from @userinfobot)
1. Open Telegram and search for **@userinfobot**
2. Tap **Start**
3. It will reply with your Telegram numeric ID (usually 9–10 digits)

✅ Save this ID — you’ll paste it into `businessbot.py` as `ADMIN_ID`.

---

## 🧩 Telegram Bot Installation (Pi)

### 1) Install Python packages
```bash
sudo apt update
sudo apt install python3-pip -y
pip3 install pyTelegramBotAPI PyPDF2 --break-system-packages
```

### 2) Create the bot file
```bash
nano /home/redwannabil/businessbot.py
```

Paste your full bot code into that file.

### 3) Configure your bot (IMPORTANT)
Inside `businessbot.py`, set:
- `BOT_TOKEN` = your token from @BotFather
- `ADMIN_ID` = your Telegram numeric ID
- `PRINTER_NAME` = your CUPS printer name (example: `EpsonMobile`)

To confirm printer names in CUPS:
```bash
lpstat -p
```

### 4) Create a systemd service to run the bot forever
```bash
sudo nano /etc/systemd/system/printerbot.service
```

Paste (edit username/path if different):
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

### 5) Enable + start the bot
```bash
sudo systemctl daemon-reload
sudo systemctl enable printerbot.service
sudo systemctl start printerbot.service
```

✅ Your bot now survives reboot.

---

## 🧭 How to Use the Telegram Bot (User Flow)

### Print workflow
1. Customer sends a PDF to the bot **as a FILE** (not photo).
2. Bot asks: **Color / B&W**
3. Bot asks: **One-sided / Both-sided**
4. Bot asks for payment details.
5. Admin receives:
   - PDF
   - printing preferences
   - payment details
6. Admin verifies payment (Yes/No).
7. Bot prints:
   - One-sided: prints normally
   - Both-sided:
     - prints odd pages first
     - tells admin to flip/reverse the entire stack
     - prints even pages

### Scan workflow
1. Customer types `/scan`
2. Bot asks confirmation
3. Bot asks for payment details
4. Admin verifies payment
5. Admin presses “Start scanning”
6. Bot scans and sends PDF to the customer

---

## ⚠️ Reliability & Sustainability Tips (Important)

- **Keep printer ON during business hours** so customers don’t wait.
- **Duplex rule:** never separate pages manually.
  - When bot says flip stack: flip/reverse the **entire stack** and reinsert.
- If you get jams or stuck jobs:
  - clear jam physically
  - cancel stuck jobs using commands below
- Use a stable power supply (bad power causes random USB printer/scanner disconnects).
- (Optional) Use a UPS for power backup.

---

## 🧰 Essential Commands Cheat Sheet

### 🤖 Bot management
Check bot status:
```bash
sudo systemctl status printerbot.service
```

View live bot logs/errors:
```bash
sudo journalctl -u printerbot.service -f
```

Edit bot code:
```bash
nano /home/redwannabil/businessbot.py
```

Restart bot (apply changes):
```bash
sudo systemctl restart printerbot.service
```

Stop bot:
```bash
sudo systemctl stop printerbot.service
```

Start bot:
```bash
sudo systemctl start printerbot.service
```

---

### 🖨️ CUPS / Printer emergency commands
See printers:
```bash
lpstat -p
```

See queue/jobs:
```bash
lpstat -o
```

Cancel ALL stuck print jobs:
```bash
cancel -a
```

Restart CUPS engine:
```bash
sudo systemctl restart cups
```

---

### 📸 Scanner emergency commands
Check if Pi detects the scanner:
```bash
scanimage -Lv
```

Restart scanner web app:
```bash
sudo systemctl restart scanservjs
```

---

## 🔒 Security Notes
- Tailscale is the security layer: only your tailnet devices can access:
  - CUPS `:631`
  - scanservjs `:8080`
- Do **NOT** expose CUPS to public internet directly.
- Keep the Pi updated:
  ```bash
  sudo apt update && sudo apt upgrade -y
  ```

---

## ✅ Endpoints Summary (Copy/Paste)

Replace `YOUR_TAILSCALE_IP` with your Pi’s Tailscale IP.

- CUPS UI:
  - `http://YOUR_TAILSCALE_IP:631`
- Windows RAW printer:
  - `http://YOUR_TAILSCALE_IP:631/printers/EpsonWindows`
- Mobile/Telegram printer:
  - `http://YOUR_TAILSCALE_IP:631/printers/EpsonMobile`
- Cloud scanner UI (scanservjs):
  - `http://YOUR_TAILSCALE_IP:8080`

---

### Maintainer
- Telegram: `t.me/Redwan_Nabil2003`
