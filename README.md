# Lightroom Backup Cleanup Script

This Python script automates the maintenance of Lightroom backup directories. It intelligently removes old backups while preserving daily and weekly shapshots, checks for data integrity, monitors disk space, and sends email notifications upon critical events.

## Features

-   **Smart Retention Policy**:
    -   **0 - 7 days**: Keeps all daily backups.
    -   **7 - 60 days**: Keeps one backup per week (Smart Thinning).
    -   **> 60 days**: Deletes all backups (unless minimum backup limit is reached).
    -   **Minimum Backups**: Ensures at least `min_backups` (default 5) are kept, regardless of age.
-   **Integrity Checks**: Verifies that the `.zip` file within the backup directory is not corrupt.
-   **Disk Space Monitoring**: Warns if free disk space falls below a configurable threshold (default 10GB).
-   **Stale Backup Alert**: Sends an alarm if no new backup has been created in the last 31 days.
-   **HTML Reports**: Sends beautifully formatted HTML table reports via email.
-   **Conditional Reporting**: Sends email notifications *only* when:
    -   A backup is deleted.
    -   An error occurs (e.g., corrupt zip, disk full).
    -   A warning is triggered (e.g., stale backup).
-   **Detailed Logging**: Maintains a rotating log file (`cleanup_backup.log`) with rotation (max 1MB, 4 files).
-   **SMB Backup Copy & Retention**: Automatically copies new backups to a remote SMB (Samba) share and applies the same retention cleanup policy to the share. It supports automatic mounting on macOS using `osascript`.

## Installation

1.  **Prerequisites**:
    -   Python 3 installed on macOS.
    -   Standard libraries used: `os`, `shutil`, `logging`, `datetime`, `re`, `smtplib`, `ssl`, `email`, `configparser`, `zipfile`.

2.  **Files**:
    -   `cleanup_backups.py`: The main script.
    -   `config.ini`: Configuration file (must be in the same directory).

## Configuration (`config.ini`)

1.  **Copy the sample configuration**:
    ```bash
    cp sample_config.ini config.ini
    ```
2.  **Edit `config.ini`**:
    Open `config.ini` in a text editor and update the values.
    The file contains detailed comments explaining each parameter.

    **Key settings**:
    -   `backup_dir`: Path to your backups.
    -   `max_age_days`: Retention limit.
    -   `min_backups`: Minimum number of backups to keep (safety net).
    -   `dry_run`: Set to `True` for testing, `False` for actual deletion.
    -   `[Email]`: Configure SMTP settings if you want notifications.
    -   `[SMB]`: Configure `enable_smb`, `smb_url`, `smb_mount_path`, and `smb_backup_dir` to copy backups to a Samba network share and apply retention rules there.



## Usage

### Manual Execution

Run the script manually to test configuration or force a clean-up:

```bash
python3 cleanup_backups.py
```

Check the console output or `cleanup_backup.log` for details.

### Automated Execution (Cron)

The script is designed to run automatically via `cron`.
Example crontab entry (runs daily at 22:30):

```bash
30 22 * * * /usr/bin/python3 /Users/mark/Documents/Python/Lightroom/cleanup_backup/cleanup_backups.py
```

To edit your crontab, run `crontab -e` in the terminal.

## Logs

Logs are stored in the same directory as the script: `cleanup_backup.log`.
The log file rotates automatically when it reaches 1MB, keeping up to 4 historical log files.

## Safety

-   **Dry Run**: Always set `dry_run = True` when making changes to configuration or testing new logic.
-   **Email Alerts**: Ensure your SMTP credentials are an **App Password**, not your main account password, for better security.
