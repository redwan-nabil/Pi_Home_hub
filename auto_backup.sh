#!/bin/bash
LOGFILE="/home/username/backup.log"
FILENAME="Pi_Backup_$(date +%Y%m%d).img.gz"

# Telegram Credentials
TOKEN="Add your telegram bot token"
CHAT_ID="add your chat id"

# Notification Function
send_msg() {
    curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" \
    -d chat_id="$CHAT_ID" \
    -d text="$1" > /dev/null
}

# Log the start
echo "$(date '+%Y-%m-%d %H:%M:%S') : --- BACKUP STARTED ---" >> "$LOGFILE"

# 1. OS & Deep Cache Cleanup (Frees up SD space before backing up)
echo "$(date '+%Y-%m-%d %H:%M:%S') : Cleaning OS and Bot cache..." >> "$LOGFILE"

# Clean old software update cache
sudo apt autoremove -y >> "$LOGFILE" 2>&1
sudo apt clean >> "$LOGFILE" 2>&1

# Delete any stuck/abandoned PDF files from the bot crashes
sudo rm -f /tmp/print_*.pdf /tmp/scanned_*.pdf /home/redwannabil/*.pdf >> "$LOGFILE" 2>&1

# Clear Linux system logs older than 3 days (This saves massive space!)
sudo journalctl --vacuum-time=3d >> "$LOGFILE" 2>&1

# Clear the temporary RAM cache
sudo sync; echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null

# 2. Local Cleanup (Keep last 2 days on pendrive)
find /mnt/usb_backup/ -name "Pi_Backup_*.img.gz" -type f -mtime +2 -delete >> "$LOGFILE" 2>&1

# 3. Cloud Cleanup (Delete files older than 19h to stay under 15GB limit)
rclone delete --config="/home/redwannabil/.config/rclone/rclone.conf" gdrive:Pi_Backups/ --min-age 19h >> "$LOGFILE" 2>&1

# 4. Create Backup with Multi-core Compression
# nice -n 19 makes sure your desktop stays smooth during the process
echo "$(date '+%Y-%m-%d %H:%M:%S') : Creating compressed image (Parallel)..." >> "$LOGFILE"
sudo sh -c "nice -n 19 ionice -c 3 dd if=/dev/mmcblk0 bs=4M | nice -n 19 pigz > /mnt/usb_backup/$FILENAME" >> "$LOGFILE" 2>&1

if [ $? -ne 0 ]; then
    send_msg "❌ Pi Backup Failed: Error during compression on $(hostname)"
    exit 1
fi

# 5. Upload to Google Drive
echo "$(date '+%Y-%m-%d %H:%M:%S') : Uploading to Google Drive..." >> "$LOGFILE"
nice -n 19 ionice -c 3 rclone copy --config="/home/redwannabil/.config/rclone/rclone.conf" /mnt/usb_backup/"$FILENAME" gdrive:Pi_Backups/ >> "$LOGFILE" 2>&1

if [ $? -eq 0 ]; then
    send_msg "✅ Pi Backup Successful: $FILENAME is safe in the cloud!"
else
    send_msg "⚠️ Pi Backup Alert: Google Drive upload failed! Check Quota."
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') : --- BACKUP COMPLETED ---" >> "$LOGFILE"
