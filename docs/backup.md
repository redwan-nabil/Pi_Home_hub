# 💾 Automated Raspberry Pi Backup — Detailed Reference

This document supplements the backup section in the main [README.md](../README.md).

---

## Architecture Overview

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

## Script Configuration Reference

All configuration lives at the top of `scripts/auto_backup.sh`:

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

## Secrets File Format

Create `~/.backup_secrets` with:

```bash
BACKUP_BOT_TOKEN="123456:ABC-your-token-here"
BACKUP_CHAT_ID="your_numeric_chat_id"
```

Then lock it down:

```bash
chmod 600 ~/.backup_secrets
```

> **⚠️ Never commit this file to Git.** The `.gitignore` already excludes it.

## Restore Procedure

To restore a backup image onto a **new** SD card:

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

## Troubleshooting

| Problem | Solution |
|---|---|
| `pigz: command not found` | `sudo apt install pigz` |
| `rclone: command not found` | `sudo apt install rclone` |
| USB drive not mounted | Check `lsblk` and re-mount; verify `/etc/fstab` |
| rclone auth expired | Re-run `rclone config reconnect gdrive:` |
| Telegram messages not arriving | Verify token/chat ID; test with `curl` manually |
| Backup takes too long | Use `-1` (fast) compression; consider excluding boot partition |
| Disk full on USB | Reduce `LOCAL_RETENTION_DAYS` or use a larger drive |
