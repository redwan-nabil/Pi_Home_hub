#!/bin/bash

# ==============================================================================
# RPI 5 UNIFIED BACKUP PIPELINE v4.5 (DOCKER-AWARE GOVERNOR)
# ==============================================================================

LOGFILE="/home/redwannabil/master_backup.log"
DATE=$(date +"%Y-%m-%d_%H-%M")

# --- DIRECTORIES ---
BASE_USB_DIR="/mnt/usb_backup/server_backup"
OS_DIR="$BASE_USB_DIR/RPI_OS_backup"
HA_DIR="$BASE_USB_DIR/HA_Backup"
NC_DIR="$BASE_USB_DIR/Nextcloud_Admin_backup"

HA_SOURCE="/home/redwannabil/homeassistant"
NC_SOURCE="/home/redwannabil/nextcloud"

# --- TELEGRAM SETTINGS ---
TOKEN="YOUR_TELEGRAM_BOT_TOKEN"
CHAT_ID="YOUR_TELEGRAM_CHAT_ID"

# ==============================================================================

send_msg() {
    curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendMessage" -d chat_id="$CHAT_ID" -d text="$1" -d parse_mode="Markdown" > /dev/null
}

# ==============================================================================
# 🧠 THE CPU GOVERNOR (Docker-Aware)
# ==============================================================================
governor_loop() {
    local PAUSED=0
    while true; do
        LOAD=$(cat /proc/loadavg | awk '{print $1}')
        
        # Only look for active, aggressive docker commands
        DOCKER_BUSY=$(pgrep -f "docker compose|docker build|docker run" > /dev/null && echo 1 || echo 0)

        SPIKE=$(awk -v load="$LOAD" -v dbusy="$DOCKER_BUSY" 'BEGIN {if (load > 3.0 || dbusy == 1) print 1; else print 0}')
        SAFE=$(awk -v load="$LOAD" -v dbusy="$DOCKER_BUSY" 'BEGIN {if (load < 1.5 && dbusy == 0) print 1; else print 0}')

        if [ "$SPIKE" -eq 1 ] && [ "$PAUSED" -eq 0 ]; then
            sudo pkill -STOP -x "dd" 2>/dev/null
            sudo pkill -STOP -x "gzip" 2>/dev/null
            sudo pkill -STOP -x "tar" 2>/dev/null
            sudo pkill -STOP -x "rclone" 2>/dev/null
            PAUSED=1
            send_msg "⚠️ *Resource Conflict Detected!* Auto-pausing backup to prioritize system tasks (Load: $LOAD)..."
        elif [ "$SAFE" -eq 1 ] && [ "$PAUSED" -eq 1 ]; then
            sudo pkill -CONT -x "dd" 2>/dev/null
            sudo pkill -CONT -x "gzip" 2>/dev/null
            sudo pkill -CONT -x "tar" 2>/dev/null
            sudo pkill -CONT -x "rclone" 2>/dev/null
            PAUSED=0
            send_msg "✅ *Resources Freed.* Resuming backup pipeline (Load: $LOAD)."
        fi
        sleep 10
    done
}

# Start the Governor and make sure it dies when the script finishes
governor_loop &
GOVERNOR_PID=$!
trap "kill $GOVERNOR_PID 2>/dev/null" EXIT

# ==============================================================================
# PIPELINE EXECUTION
# ==============================================================================

echo "======================================================" >> "$LOGFILE"
echo "$(date '+%Y-%m-%d %H:%M:%S') : --- UNIFIED BACKUP STARTED ---" >> "$LOGFILE"
send_msg "🚀 *Backup Pipeline Started:* Preparing system..."

# --- STEP 0: PREPARE FOLDERS ---
sudo mkdir -p "$OS_DIR" "$HA_DIR" "$NC_DIR"

sudo apt autoremove -y >> "$LOGFILE" 2>&1
sudo apt clean >> "$LOGFILE" 2>&1
sudo rm -f /tmp/print_*.pdf /tmp/scanned_*.pdf /home/redwannabil/*.pdf >> "$LOGFILE" 2>&1
sudo journalctl --vacuum-time=3d >> "$LOGFILE" 2>&1
sudo sync; echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null

# --- STEP 1: THROTTLED OS BACKUP ---
echo "$(date '+%Y-%m-%d %H:%M:%S') : [1/3] Starting Throttled OS Backup..." >> "$LOGFILE"
OS_FILENAME="Pi_OS_$DATE.img.gz"

sudo sh -c "dd if=/dev/mmcblk0 bs=4M | pv -q -L 8m | gzip > $OS_DIR/$OS_FILENAME" >> "$LOGFILE" 2>&1

if [ $? -eq 0 ]; then
    send_msg "💽 *Local USB Success:* Pi OS image saved safely!"
else
    send_msg "❌ *FATAL ERROR:* Pi OS backup failed!"
    exit 1
fi

# --- STEP 2: HOME ASSISTANT BACKUP ---
echo "$(date '+%Y-%m-%d %H:%M:%S') : [2/3] Starting Home Assistant Backup..." >> "$LOGFILE"
HA_FILENAME="HA_Backup_$DATE.tar.gz"

sudo tar -czvf "$HA_DIR/$HA_FILENAME" "$HA_SOURCE" >> "$LOGFILE" 2>&1
if [ $? -eq 0 ] || [ $? -eq 1 ]; then
    send_msg "💽 *Local USB Success:* Home Assistant saved!"
else
    send_msg "⚠️ *Warning:* Home Assistant local backup failed!"
fi

# --- STEP 3: NEXTCLOUD ADMIN BACKUP ---
echo "$(date '+%Y-%m-%d %H:%M:%S') : [3/3] Starting Nextcloud Settings Backup..." >> "$LOGFILE"
NC_FILENAME="Nextcloud_Admin_$DATE.tar.gz"

sudo tar --exclude='*/data/*' -czvf "$NC_DIR/$NC_FILENAME" "$NC_SOURCE" >> "$LOGFILE" 2>&1
if [ $? -eq 0 ] || [ $? -eq 1 ]; then
    send_msg "💽 *Local USB Success:* Nextcloud Admin saved!"
fi

# --- STEP 4: CLOUD UPLOAD (G-DRIVE) ---
echo "$(date '+%Y-%m-%d %H:%M:%S') : Uploading to Google Drive..." >> "$LOGFILE"

sudo rclone delete --config="/home/redwannabil/.config/rclone/rclone.conf" gdrive:Server_Backups/HA_Backup/ --min-age 48h >> "$LOGFILE" 2>&1
sudo rclone delete --config="/home/redwannabil/.config/rclone/rclone.conf" gdrive:Server_Backups/NC_Backup/ --min-age 48h >> "$LOGFILE" 2>&1

nice -n 19 ionice -c 3 sudo rclone copy --config="/home/redwannabil/.config/rclone/rclone.conf" "$HA_DIR/$HA_FILENAME" gdrive:Server_Backups/HA_Backup/ >> "$LOGFILE" 2>&1
CLOUD_HA=$?

nice -n 19 ionice -c 3 sudo rclone copy --config="/home/redwannabil/.config/rclone/rclone.conf" "$NC_DIR/$NC_FILENAME" gdrive:Server_Backups/NC_Backup/ >> "$LOGFILE" 2>&1
CLOUD_NC=$?

if [ $CLOUD_HA -eq 0 ] && [ $CLOUD_NC -eq 0 ]; then
    send_msg "☁️ *Cloud Sync Success:* HA & Nextcloud safely uploaded!"
fi

# --- STEP 5: LOCAL USB RETENTION ---
echo "$(date '+%Y-%m-%d %H:%M:%S') : Cleaning old local USB backups..." >> "$LOGFILE"
sudo find "$OS_DIR" -name "*.img.gz" -type f -mtime +3 -delete >> "$LOGFILE" 2>&1
sudo find "$HA_DIR" -name "*.tar.gz" -type f -mtime +3 -delete >> "$LOGFILE" 2>&1
sudo find "$NC_DIR" -name "*.tar.gz" -type f -mtime +3 -delete >> "$LOGFILE" 2>&1

send_msg "🏁 *PIPELINE COMPLETE:* All automated backup tasks finished safely."
echo "$(date '+%Y-%m-%d %H:%M:%S') : --- PIPELINE FINISHED SUCCESSFULLY ---" >> "$LOGFILE"

exit 0
