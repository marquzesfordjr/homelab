#!/bin/bash
DATE=$(date +%Y-%m-%d)
BACKUP_DIR="/mnt/homelab-backup/$DATE"
NAS="admin@192.168.137.50:/mnt/ssd/share/backups"

# Create backup dir
mkdir -p /tmp/homelab-backup/$DATE

# Backup each LXC's data directory
for IP in 200 201 202 203 204 205 206 207 208 209 210; do
  echo "Backing up 192.168.137.$IP..."
  ssh root@192.168.137.$IP "tar czf /tmp/backup-$IP.tar.gz /opt 2>/dev/null"
  scp root@192.168.137.$IP:/tmp/backup-$IP.tar.gz /tmp/homelab-backup/$DATE/
  ssh root@192.168.137.$IP "rm /tmp/backup-$IP.tar.gz"
done

# Send to NAS
rsync -avz /tmp/homelab-backup/$DATE/ $NAS/$DATE/

# Keep only last 7 days locally
find /tmp/homelab-backup -maxdepth 1 -type d -mtime +7 -exec rm -rf {} \;

echo "Backup complete: $DATE"
