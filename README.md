# 🖨️ Ultimate Raspberry Pi Cloud Print & Scan Server

Turn a standard USB printer/scanner into a global, cloud-connected powerhouse. This system allows you to print and scan from anywhere in the world using your phone, your Windows PC, or an automated Telegram Bot complete with payment verification and intelligent duplexing.

---

## ✨ Features
* **🌍 Global Access:** Print from any network in the world via Tailscale VPN.
* **💻 Windows Native Printing:** Uses "Raw Mode" so your Windows PC controls all printing preferences (paper type, quality, margins) perfectly.
* **📱 Mobile Printing:** Seamlessly connect Android devices via the Mopria Print app.
* **🤖 Telegram Business Bot:** Let customers send PDFs to a Telegram bot, select color/duplex options, and verify payments before printing.
* **📄 Smart Duplexing:** The bot automatically injects blank pages into odd-numbered PDFs to prevent CUPS duplexing bugs—you just flip the stack!
* **📸 Cloud Scanner:** Scan documents directly to your browser using `scanservjs`.

---

## 🛠️ Phase 1: The Cloud Network (Tailscale)
To access your printer from outside your house securely, we use Tailscale.

1. **Install Tailscale on the Pi:**
   ```bash
   curl -fsSL [https://tailscale.com/install.sh](https://tailscale.com/install.sh) | sh
   ```
2. **Connect the Pi to your account:**
   ```Bash
    sudo tailscale up
   ```
(Click the link provided in the terminal to log in and authorize the Pi).

3. **Find your Magic IP:**
   ```Bash
    tailscale ip -4
   ```
Save this IP Address! We will use it for everything. (Example: `100.x.x.x `)

4. **Install Tailscale on your other devices:** Download the Tailscale app on your Windows PC and Android phone, log in, and leave it running in the background.


## 🖨️ Phase 2: The Print Server (CUPS)
CUPS is the engine that drives Linux printing.

1. **Install CUPS**
   ```Bash
    sudo apt update
    sudo apt install cups -y
    sudo usermod -a -G lpadmin $USER
    sudo cupsctl --remote-any
    sudo systemctl restart cups
   ```

2. **Access the CUPS Web Interface**
Open a browser on your PC or phone (while connected to Tailscale) and go to:
👉 https://YOUR_TAILSCALE_IP:631
(Note: Your browser will say "Warning: Not Secure". Click Advanced -> Proceed anyway. Log in with your Pi's username and password).

3.** Add Printer #1 (For Mobile & Telegram Bot)**
  -   Go to **Administration** -> **Add Printer**.
      
  -   Select your USB Printer from the list.
      
  -   Name it: **`EpsonMobile`** _(Make sure to check "Share This Printer")_.
      
  -   Select your printer's Make and Model to install the standard driver.
      
  -   Set the default paper size to A4.
  -   
4. **Add Printer #2 (For Windows RAW Mode)**
We need a second "virtual" printer for Windows so Windows can handle the complex printing preferences (like glossy photo paper).

  Go to Administration -> Add Printer.
  
  Select the exact same USB Printer again.
  
  Name it: EpsonWindows (Make sure to check "Share This Printer").
  
  CRITICAL STEP: For the "Make", scroll to the very top and select Raw.
  
  Click Add Printer.


## 💻 Phase 3: Connecting Your Devices
**Adding to Windows (Via Tailscale)**
  Open Windows Settings -> Printers & Scanners -> Add a printer or scanner.
  
  Wait 3 seconds, then click The printer that I want isn't listed.
  
  Select Select a shared printer by name.
  
  Type this exact URL: http://YOUR_TAILSCALE_IP:631/printers/EpsonWindows

  Click Next. Windows will ask for a driver. Select your printer brand and model from the Windows list (or click "Have Disk" to install official drivers).
  
  Print a test page! You can now edit all printer preferences via Windows.

**Adding to Android Mobile (Via Mopria)**
  Install the Mopria Print Service app from the Google Play Store.
  
  Open Mopria -> Click the 3 dots (Menu) -> Add Printer.
  
  Click the + button to add manually.
  
  Name: Pi Printer
  
  Printer URL:  `http://YOUR_TAILSCALE_IP:631/printers/EpsonMobile `
  
  You can now print directly from any app on your phone!


## 📸 Phase 4: Cloud Scanner (Scanservjs)
Turn your USB scanner into a web app accessible from anywhere.

1. **Install dependencies and the app:**

   ```Bash
    sudo apt install sane sane-utils imagemagick tesseract-ocr -y
    curl -sL [https://raw.githubusercontent.com/sbs20/scanservjs/main/install.sh](https://raw.githubusercontent.com/sbs20/scanservjs/main/install.sh) | sudo bash
   ```
Access your scanner:
Open a browser (connected to Tailscale) and go to:
👉  `http://YOUR_TAILSCALE_IP:8080 `
You can now scan documents directly to your phone/PC browser!


## 🤖 Phase 5: The Telegram Automation Bot
This bot handles customer PDF files, automated duplexing, and payment verification.

1. **Install Python Dependencies**
  ```Bash
sudo apt install python3-pip -y
pip3 install pyTelegramBotAPI psutil PyPDF2 --break-system-packages
  ```
2. **Create the Bot Script**
  ```Bash
nano /home/redwannabil/businessbot.py
  ```
Paste your complete Python bot code into this file. Save and exit (Ctrl+X, Y, Enter).

3. **Create the System Service (Runs Bot Forever)**
  ```Bash
sudo nano /etc/systemd/system/printerbot.service
  ```
Paste this exact code:

  ```Ini, TOML
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
Save and exit (Ctrl+X, Y, Enter).

4. Activate the Bot
  ```Bash
sudo systemctl daemon-reload
sudo systemctl enable printerbot.service
sudo systemctl start printerbot.service
  ```
Your bot is now live and will survive system reboots automatically!


## 💡 How to Use the Bot & Cautions
**User Flow:**

  Customer sends a PDF to the bot.
  
  Bot asks for Color vs. B/W, and One-Sided vs. Both-Sided.
  
  Bot asks for payment details.
  
  Admin receives the file, payment proof, and exact printing preferences.
  
  Admin clicks "Verify".
  
  If Both-Sided, the bot automatically prints odd pages, injects a blank page (if needed), pauses, and tells the admin to flip the stack and click "Done".


## ⚠️ Important Cautions for Reliability:

  Never separate pages manually: When the bot asks you to reverse the stack for duplexing, grab the entire stack, flip it, and put it in the tray. The bot's PyPDF2 blank-page-injection handles the math for you.
  
  Paper Jams: If the printer jams, clear the jam physically. You may need to use the cancel -a command (see below) to clear the broken job out of CUPS before trying again.
  
  Keep Printer On: For the best UX, keep the printer powered on during business hours. If it is off, the bot will kindly place customer jobs in a "waiting room" until you turn the printer on.


## 🚨 Essential & Emergency Commands Cheat Sheet
Keep these commands handy. They are all you need to maintain the server.

**🤖 Bot Management:**

  Check if Bot is running/crashing:  `sudo systemctl status printerbot.service`
  
  View Live Bot Logs/Errors: `sudo journalctl -u printerbot.service -f`
  
  Edit Bot Code: `nano /home/redwannabil/businessbot.py`
  
  Restart Bot (Apply Code Changes): `sudo systemctl restart printerbot.service`
  
  Stop Bot: `sudo systemctl stop printerbot.service`

**🖨️ Printer Emergencies:**

  Cancel ALL stuck print jobs: `cancel -a`
  
  See what the printer is doing: `lpstat -p EpsonMobile`
  
  Restart CUPS Print Engine: `sudo systemctl restart cups`

📸 Scanner Emergencies:

See if Pi detects the scanner: `scanimage -Lv

Restart Scanner Web App: `sudo systemctl restart scanservjs`
