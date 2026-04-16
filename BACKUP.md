# Backup Guide (Raspberry Pi Nextcloud)

## What to back up
- Nextcloud app/config: `~/nextcloud/system`
- MariaDB database: dump from the `db` container
- User data: `/mnt/usb_backup/nc_data`

## 1) Put Nextcloud in maintenance mode
```bash
cd ~/nextcloud
docker compose exec -u www-data app php occ maintenance:mode --on
```

## 2) Database backup (dump)
```bash
cd ~/nextcloud
mkdir -p backups

# If your service name is "db"
docker compose exec db mariadb-dump -u root -p"${MYSQL_ROOT_PASSWORD}" "${MYSQL_DATABASE}" > backups/nextcloud_db_$(date +%F).sql
```

## 3) Backup Nextcloud config/app files
```bash
cd ~/nextcloud
tar -czf backups/nextcloud_system_$(date +%F).tar.gz system
```

## 4) Backup user data (Vault)
> This can be large; use rsync to another disk/NAS.
```bash
sudo rsync -aH --delete /mnt/usb_backup/nc_data/ /path/to/your/backup_destination/nc_data/
```

## 5) Turn maintenance mode off
```bash
cd ~/nextcloud
docker compose exec -u www-data app php occ maintenance:mode --off
```

## Restore notes (high-level)
- Restore `system/` back to `~/nextcloud/system`
- Restore user data back to `/mnt/usb_backup/nc_data`
- Re-import SQL dump into the DB container
