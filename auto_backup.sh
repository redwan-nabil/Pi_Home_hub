#!/bin/bash

# ==========================================
# CONFIGURATION - EDIT THESE VARIABLES
# ==========================================
USER_HOME="/home/YOUR_USERNAME"               # Replace YOUR_USERNAME with your actual Linux username
BACKUP_DIR="/mnt/usb_backup"                  # The path to your local backup drive
LOGFILE="$USER_HOME/backup.log"               # Where you want the log file saved
FILENAME="Pi_Backup_$(date +%Y%m%d).img.gz"   # Format of the output file

# Telegram Notification Credentials
TOKEN="YOUR_TELEGRAM_BOT_TOKEN_HERE"          # Enter your bot token (e.g., 123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11)
CHAT_ID="YOUR_TELEGRAM_CHAT_ID_HERE"          # Enter your chat ID

# Rclone Cloud Configuration
RCLONE_CONF="$USER_HOME/.config/rclone/rclone.conf"
RCLONE_REMOTE="gdrive:Pi_Backups/"            # Your rclone remote name and folder path
# ==========================================

# Telegram Notification Function
send_msg() {
    curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" \
    -d chat_id="$CHAT_ID" \
    -d text="$1" > /dev/null
}

# Log the start
echo "$(date '+%Y-%m-%d %H:%M:%S') : --- BACKUP STARTED ---" >> "$LOGFILE"

# 1. OS & Deep Cache Cleanup (Frees up SD space before backing up)
echo "$(date '+%Y-%m-%d %H:%M:%S') : Cleaning OS and temp cache..." >> "$LOGFILE"

# Clean old software update cache
sudo apt autoremove -y >> "$LOGFILE" 2>&1
sudo apt clean >> "$LOGFILE" 2>&1

# Delete app-specific temporary files (Example: stuck files from app crashes)
# sudo rm -f /tmp/*.pdf "$USER_HOME"/*.pdf >> "$LOGFILE" 2>&1

# Clear Linux system logs older than 3 days (Saves massive space)
sudo journalctl --vacuum-time=3d >> "$LOGFILE" 2>&1

# Clear redundant Timeshift snapshots (Frees up massive space before the dd clone)
echo "$(date '+%Y-%m-%d %H:%M:%S') : Clearing Timeshift snapshots..." >> "$LOGFILE"
sudo timeshift --delete-all >> "$LOGFILE" 2>&1

# Clear the temporary RAM cache
sudo sync; echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null

# 2. Local Cleanup (Keep last 2 days on local drive)
find "$BACKUP_DIR/" -name "Pi_Backup_*.img.gz" -type f -mtime +2 -delete >> "$LOGFILE" 2>&1

# 3. Cloud Cleanup (Delete files older than 19h to stay under free tier limits)
rclone delete --config="$RCLONE_CONF" "$RCLONE_REMOTE" --min-age 19h >> "$LOGFILE" 2>&1

# 4. Create Backup with Multi-core Compression
# nice -n 19 makes sure your desktop stays smooth during the process
echo "$(date '+%Y-%m-%d %H:%M:%S') : Creating compressed image (Parallel)..." >> "$LOGFILE"
sudo sh -c "nice -n 19 ionice -c 3 dd if=/dev/mmcblk0 bs=4M | nice -n 19 pigz > $BACKUP_DIR/$FILENAME" >> "$LOGFILE" 2>&1

if [ $? -ne 0 ]; then
    send_msg "❌ Pi Backup Failed: Error during compression on $(hostname)"
    exit 1
fi

# 5. Upload to Cloud Storage
echo "$(date '+%Y-%m-%d %H:%M:%S') : Uploading to Cloud Storage..." >> "$LOGFILE"
nice -n 19 ionice -c 3 rclone copy --config="$RCLONE_CONF" "$BACKUP_DIR/$FILENAME" "$RCLONE_REMOTE" >> "$LOGFILE" 2>&1

if [ $? -eq 0 ]; then
    send_msg "✅ Pi Backup Successful: $FILENAME is safe in the cloud!"
else
    send_msg "⚠️ Pi Backup Alert: Cloud upload failed! Check Quota."
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') : --- BACKUP COMPLETED ---" >> "$LOGFILE"
