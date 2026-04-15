#!/usr/bin/env bash
# ============================================================================
# auto_backup.sh — Automated Raspberry Pi SD Card Backup
# ============================================================================
# Creates a compressed full-disk image, stores it on a USB drive, uploads it
# to Google Drive via rclone, sends Telegram notifications, and rotates old
# backups automatically.
#
# Usage:
#   sudo /usr/local/bin/auto_backup.sh
#
# Prerequisites:
#   - pigz   (parallel gzip)
#   - rclone (configured with a Google Drive remote)
#   - A mounted USB drive
#   - Telegram bot token + chat ID in ~/.backup_secrets
#
# See README.md for full setup instructions.
# ============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration — edit these to match your setup
# ---------------------------------------------------------------------------

# Source device (the SD card)
SOURCE_DEVICE="/dev/mmcblk0"

# Local USB backup directory (must be mounted)
USB_MOUNT="/mnt/usb_backup"
LOCAL_BACKUP_DIR="${USB_MOUNT}/pi_backups"

# rclone remote name and cloud folder
RCLONE_REMOTE="gdrive"
CLOUD_BACKUP_DIR="pi_backups"

# Retention
LOCAL_RETENTION_DAYS=30
CLOUD_RETENTION_DAYS=60

# Log file
LOG_FILE="/var/log/pi_backup.log"

# Secrets file (must contain BACKUP_BOT_TOKEN and BACKUP_CHAT_ID)
SECRETS_FILE="${HOME}/.backup_secrets"

# ---------------------------------------------------------------------------
# Internal variables (do not edit)
# ---------------------------------------------------------------------------
TIMESTAMP="$(date +%Y-%m-%d_%H%M%S)"
HOSTNAME_TAG="$(hostname)"
BACKUP_FILENAME="${HOSTNAME_TAG}_backup_${TIMESTAMP}.img.gz"
BACKUP_PATH="${LOCAL_BACKUP_DIR}/${BACKUP_FILENAME}"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

log() {
    local msg
    msg="[$(date '+%Y-%m-%d %H:%M:%S')] $*"
    echo "$msg" | tee -a "$LOG_FILE"
}

send_telegram() {
    local message="$1"
    if [[ -n "${BACKUP_BOT_TOKEN:-}" && -n "${BACKUP_CHAT_ID:-}" ]]; then
        curl -s -X POST \
            "https://api.telegram.org/bot${BACKUP_BOT_TOKEN}/sendMessage" \
            -d chat_id="${BACKUP_CHAT_ID}" \
            -d text="${message}" \
            -d parse_mode="Markdown" > /dev/null 2>&1 || true
    else
        log "WARNING: Telegram credentials not set — skipping notification."
    fi
}

cleanup_local() {
    log "Rotating local backups older than ${LOCAL_RETENTION_DAYS} days..."
    find "$LOCAL_BACKUP_DIR" -maxdepth 1 -name "*.img.gz" -type f -mtime +"$LOCAL_RETENTION_DAYS" -print -delete | while read -r f; do
        log "  Deleted: $f"
    done
}

cleanup_cloud() {
    log "Rotating cloud backups older than ${CLOUD_RETENTION_DAYS} days..."
    rclone delete "${RCLONE_REMOTE}:${CLOUD_BACKUP_DIR}" \
        --min-age "${CLOUD_RETENTION_DAYS}d" \
        --verbose 2>&1 | tee -a "$LOG_FILE" || true
}

# ---------------------------------------------------------------------------
# Pre-flight checks
# ---------------------------------------------------------------------------

preflight() {
    # Must run as root (dd needs raw device access)
    if [[ $EUID -ne 0 ]]; then
        echo "ERROR: This script must be run as root (sudo)." >&2
        exit 1
    fi

    # Load secrets
    if [[ -f "$SECRETS_FILE" ]]; then
        # shellcheck source=/dev/null
        source "$SECRETS_FILE"
    else
        log "WARNING: Secrets file ${SECRETS_FILE} not found. Telegram notifications disabled."
    fi

    # Check required tools
    for cmd in pigz rclone dd; do
        if ! command -v "$cmd" &> /dev/null; then
            log "ERROR: Required command '$cmd' is not installed."
            send_telegram "❌ *Backup FAILED* — \`$cmd\` is not installed on ${HOSTNAME_TAG}."
            exit 1
        fi
    done

    # Ensure USB mount is available
    if ! mountpoint -q "$USB_MOUNT"; then
        log "ERROR: USB drive is not mounted at ${USB_MOUNT}."
        send_telegram "❌ *Backup FAILED* — USB drive not mounted at \`${USB_MOUNT}\` on ${HOSTNAME_TAG}."
        exit 1
    fi

    # Ensure backup directory exists
    mkdir -p "$LOCAL_BACKUP_DIR"
}

# ---------------------------------------------------------------------------
# Main backup routine
# ---------------------------------------------------------------------------

main() {
    preflight

    log "========================================"
    log "BACKUP START: ${BACKUP_FILENAME}"
    log "========================================"
    send_telegram "🔄 *Backup Started*%0AHost: \`${HOSTNAME_TAG}\`%0AFile: \`${BACKUP_FILENAME}\`"

    local start_time size
    start_time=$(date +%s)
    size="unknown"

    # --- Step 1: Create compressed image ---
    log "Step 1/4: Creating compressed image from ${SOURCE_DEVICE}..."
    if dd if="$SOURCE_DEVICE" bs=4M status=none | pigz -1 > "$BACKUP_PATH"; then
        size=$(du -h "$BACKUP_PATH" | cut -f1)
        log "  Image created: ${BACKUP_PATH} (${size})"
    else
        log "ERROR: dd/pigz failed."
        send_telegram "❌ *Backup FAILED* at image creation step on ${HOSTNAME_TAG}."
        exit 1
    fi

    # --- Step 2: Upload to Google Drive ---
    log "Step 2/4: Uploading to ${RCLONE_REMOTE}:${CLOUD_BACKUP_DIR}/..."
    if rclone copy "$BACKUP_PATH" "${RCLONE_REMOTE}:${CLOUD_BACKUP_DIR}/" --progress 2>&1 | tee -a "$LOG_FILE"; then
        log "  Upload complete."
    else
        log "WARNING: rclone upload failed. Local backup is safe."
        send_telegram "⚠️ *Backup Warning* — Upload to Google Drive failed. Local copy saved on USB."
    fi

    # --- Step 3: Rotate old backups ---
    log "Step 3/4: Cleaning up old backups..."
    cleanup_local
    cleanup_cloud

    # --- Step 4: Summary ---
    local end_time duration_min
    end_time=$(date +%s)
    duration_min=$(( (end_time - start_time) / 60 ))

    log "Step 4/4: Backup complete in ${duration_min} minutes."
    log "========================================"
    log "BACKUP DONE: ${BACKUP_FILENAME}"
    log "========================================"

    send_telegram "✅ *Backup Complete*%0AHost: \`${HOSTNAME_TAG}\`%0AFile: \`${BACKUP_FILENAME}\`%0ASize: \`${size}\`%0ADuration: \`${duration_min} min\`"
}

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
main "$@"
