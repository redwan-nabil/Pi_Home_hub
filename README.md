# Nextcloud setup: A complete secure private NAS server with pi5  
**Integration: Tailscale + Docker + Nextcloud**

A complete, practical guide for building a **high-performance** and **secure** personal cloud/NAS on a **Raspberry Pi 5**, using **Docker** (Nextcloud + MariaDB) with a **split-storage architecture** to avoid the classic permission/I/O issues—plus a hardened access model using **Tailscale** (no port-forwarding).

---

## Key Principles (The “God-Tier” Split Architecture)

This build intentionally separates the system and the data:

- **The Brain (SD card)**  
  Raspberry Pi OS + Docker + Nextcloud application files + database live here for fast app/database operations.

- **The Vault (External SSD / USB Drive)**  
  Formatted as **ext4** and mounted permanently. Stores **only user data** (photos, documents, uploads).

- **The Network (Private Access)**  
  Access Nextcloud via **Tailscale VPN** only. No public exposure, no router port forwarding.

---

## Step 1 — Storage Preparation (The Vault)

> Never run a Linux server workload on **exFAT/FAT32**. Use **ext4**.

### 1) Identify the drive
```bash
lsblk
```
Assume the data partition is `/dev/sda1` for the examples below.

### 2) Format to ext4 (WIPES THE PARTITION)
```bash
sudo mkfs.ext4 /dev/sda1
```

### 3) Get the UUID (required for stable mounts)
```bash
lsblk -f
```
Copy the `UUID` for `/dev/sda1`.

### 4) Create mount point + add `/etc/fstab` entry
```bash
sudo mkdir -p /mnt/usb_backup
sudo nano /etc/fstab
```

Add a line like this (replace UUID):
```text
UUID=your-long-uuid-code-here /mnt/usb_backup ext4 defaults,noatime 0 2
```

### 5) Apply and verify
```bash
sudo systemctl daemon-reload
sudo mount -a
mount | grep usb_backup
```

---

## Step 2 — Docker Deployment (Split Architecture)

### 1) Create the data folder + “safe” permissions
Nextcloud in Docker commonly runs as `www-data` (UID/GID `33:33`).

```bash
sudo mkdir -p /mnt/usb_backup/nc_data
sudo chown -R 33:33 /mnt/usb_backup/nc_data
sudo chmod -R 770 /mnt/usb_backup/nc_data
```

Optional (only if you have backup scripts that need to write to `/mnt/usb_backup` root):
```bash
sudo chown pi:pi /mnt/usb_backup  # replace "pi" with your username if different
sudo chmod 755 /mnt/usb_backup
```

### 2) Create the compose project
```bash
mkdir -p ~/nextcloud
cd ~/nextcloud
nano docker-compose.yml
```

### 3) Paste this `docker-compose.yml`
> Notes:
> - `./system` = Nextcloud app files (Brain / SD card)
> - `./database` = MariaDB data (Brain / SD card)
> - `/mnt/usb_backup/nc_data` = user files (Vault / external drive)

```yaml
version: '3'

services:
  db:
    image: mariadb:10.6
    restart: always
    command: --transaction-isolation=READ-COMMITTED --log-bin=binlog --binlog-format=ROW
    volumes:
      - ./database:/var/lib/mysql
    environment:
      - MYSQL_ROOT_PASSWORD=your_strong_root_password
      - MYSQL_PASSWORD=your_strong_password
      - MYSQL_DATABASE=nextcloud_db
      - MYSQL_USER=nextcloud_user

  app:
    image: nextcloud
    restart: always
    ports:
      - 8090:80
    links:
      - db
    volumes:
      - ./system:/var/www/html
      - /mnt/usb_backup/nc_data:/var/www/html/data
    environment:
      - MYSQL_PASSWORD=your_strong_password
      - MYSQL_DATABASE=nextcloud_db
      - MYSQL_USER=nextcloud_user
      - MYSQL_HOST=db
```

### 4) Start it
```bash
docker compose up -d
```

Wait ~60 seconds, then open:

- **Local LAN:** `http://<your-pi-ip>:8090`
- **Tailscale:** `http://<your-tailscale-ip>:8090` (recommended)

Create the admin account (avoid spaces in the username).

---

## Step 3 — Performance Optimization (Fix high I/O wait / CPU spikes)

Nextcloud defaults to “AJAX” background jobs (runs during web requests). Switch to system cron:

### 1) Tell Nextcloud to use cron
```bash
docker exec --user www-data nextcloud-app-1 php occ backgroundjob:cron
```

### 2) Add the cron entry on the Pi
```bash
crontab -e
```

Add:
```text
*/5 * * * * docker exec -u www-data nextcloud-app-1 php -f /var/www/html/cron.php
```

---

## Step 4 — Security & Encryption

### A) Network security (Tailscale-first)
- Do **not** expose ports 80/443 on your router.
- Install **Tailscale** on the Pi and your devices.
- Access Nextcloud only via the Tailscale IP (e.g. `100.x.x.x:8090`).

### B) Server-Side Encryption (SSE)
Protects data-at-rest if the physical drive is stolen.

1. Nextcloud → **Apps** → **Security** → enable **Default encryption module**
2. Nextcloud → **Administration settings** → **Security**
3. Enable **Server-side encryption**

### C) End-to-End Encryption (E2EE)
Protects selected folders: encrypted on the client before upload.

1. Nextcloud → **Apps** → enable **End-to-End Encryption**
2. In your Nextcloud desktop/mobile client: **Settings → Set up encryption**
3. **Write down the recovery phrase** (paper/offline). If lost, data cannot be recovered.
4. Create a folder → menu → **Encrypt**

---

## Step 5 — Add Future Storage (SATA SSD) Without Changing Docker

1. Format new SSD `ext4` and mount via UUID in `/etc/fstab` (example mount: `/mnt/sata_ssd`)
2. Set ownership:
   ```bash
   sudo chown -R 33:33 /mnt/sata_ssd
   ```
3. Nextcloud → **Apps** → enable **External storage support**
4. Nextcloud → **Administration settings → External storages**
5. Add “Local” storage pointing to `/mnt/sata_ssd`

---

## Troubleshooting & Common Errors

### 1) “Target is busy” when unmounting
Something is still using the mount (scripts, Samba, shell session, etc.).
```bash
sudo fuser -kv /mnt/usb_backup
sudo umount -l /mnt/usb_backup
```

### 2) “Internal Server Error” (Cache crash after moving files)
Often caused by broken/corrupted cached assets in `appdata_*`.

```bash
# Remove cached JS/CSS (adjust path if your compose project differs)
sudo rm -rf /home/pi/nextcloud/system/data/appdata_*/js/*
sudo rm -rf /home/pi/nextcloud/system/data/appdata_*/css/*

# Repair + rescan
docker exec --user www-data nextcloud-app-1 php occ maintenance:repair
docker exec --user www-data nextcloud-app-1 php occ files:scan --all

# Restart containers
cd ~/nextcloud && docker compose restart
```

### 3) “403 Forbidden” / “Operation blocked”
Usually missing `.htaccess` or permissions drift.

```bash
sudo chown -R 33:33 /home/pi/nextcloud/system
sudo chown -R 33:33 /mnt/usb_backup/nc_data

docker exec --user www-data nextcloud-app-1 php occ maintenance:update:htaccess
```

### 4) “No connection to anti-virus. Upload cannot be completed.”
Antivirus app enabled, but ClamAV service is missing/off. (Often not worth it on a Pi.)

```bash
docker exec --user www-data nextcloud-app-1 php occ app:disable files_antivirus
```

