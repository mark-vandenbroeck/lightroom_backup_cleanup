import os
import shutil
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime, timedelta
import re
import smtplib
import ssl
from email.mime.text import MIMEText
import io
import configparser
import zipfile

# Determine script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, 'config.ini')
LOG_FILE = os.path.join(SCRIPT_DIR, 'cleanup_backup.log')

# Load Configuration
config = configparser.ConfigParser()
if not os.path.exists(CONFIG_FILE):
    print(f"Error: Config file not found at {CONFIG_FILE}")
    exit(1)
config.read(CONFIG_FILE)

# Configuration Variables
BACKUP_DIR = config.get('General', 'backup_dir')
MAX_AGE_DAYS = config.getint('General', 'max_age_days')
DRY_RUN = config.getboolean('General', 'dry_run')

KEEP_DAILY_DAYS = config.getint('Retention', 'keep_daily_days', fallback=7)
KEEP_WEEKLY_DAYS = config.getint('Retention', 'keep_weekly_days', fallback=60)

SEND_EMAIL = config.getboolean('Email', 'send_email', fallback=True)
SMTP_SERVER = config.get('Email', 'smtp_server')
SMTP_PORT = config.getint('Email', 'smtp_port')
SMTP_USER = config.get('Email', 'smtp_user')
SMTP_PASSWORD = config.get('Email', 'smtp_password')
EMAIL_TO = config.get('Email', 'email_to')
EMAIL_FROM = config.get('Email', 'email_from')

# ... (setup_logging remains the same)

def send_email(subject, body):
    if not SEND_EMAIL:
        print("Email sending is disabled in config.")
        return

    msg = MIMEText(body)
    # ... (rest of send_email logic)

# ... (rest of the script)

