import os
import shutil
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime
import re
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
LANGUAGE = config.get('General', 'language', fallback='en')

KEEP_DAILY_DAYS = config.getint('Retention', 'keep_daily_days', fallback=7)
KEEP_WEEKLY_DAYS = config.getint('Retention', 'keep_weekly_days', fallback=60)
MIN_BACKUPS = config.getint('Retention', 'min_backups', fallback=5)

SEND_EMAIL = config.getboolean('Email', 'send_email', fallback=True)
SMTP_SERVER = config.get('Email', 'smtp_server')
SMTP_PORT = config.getint('Email', 'smtp_port')
SMTP_USER = config.get('Email', 'smtp_user')
SMTP_PASSWORD = config.get('Email', 'smtp_password')
EMAIL_TO = config.get('Email', 'email_to')
EMAIL_FROM = config.get('Email', 'email_from')

MIN_FREE_SPACE_GB = config.getfloat('Thresholds', 'min_free_space_gb', fallback=10)
NO_BACKUP_ALERT_DAYS = config.getint('Thresholds', 'no_backup_alert_days', fallback=31)

# Translations
TRANSLATIONS = {
    'en': {
        'start_cleanup': "Starting cleanup of {}",
        'max_age': "Max age: {} days",
        'retention_policy': "Retention: keep daily {} days, keep weekly up to {} days, min backups: {}",
        'dry_run_mode': "Dry run: {}",
        'backup_dir_not_found': "Backup directory not found: {}",
        'critical_error_subject': "Lightroom Backup Cleanup - CRITICAL ERROR",
        'low_disk_space': "LOW DISK SPACE WARNING: Only {:.2f} GB free (Threshold: {} GB)",
        'error_checking_disk': "Error checking disk space: {}",
        'corrupt_zip': "CORRUPT ZIP: {} - First bad file: {}",
        'corrupt_zip_generic': "CORRUPT ZIP: {} is not a valid zip file",
        'error_accessing_dir': "Error accessing backup directory: {}",
        'error_subject': "Lightroom Backup Cleanup - ERROR",
        'no_backups_found': "NO BACKUPS FOUND in {}",
        'no_recent_backup': "NO RECENT BACKUP FOUND! Last backup was {} days ago ({})",
        'would_delete': "WOULD DELETE",
        'deleting': "DELETING",
        'older_than': "Older than {} days",
        'recent_daily': "Recent daily backup",
        'weekly_retention': "Weekly retention",
        'redundant_weekly': "Redundant weekly backup",
        'min_backup_limit': "Minimum backup limit (keeping newest {})",
        'successfully_deleted': "Successfully deleted {}",
        'error_deleting': "Error deleting {}: {}",
        'keeping': "KEEPING",
        'skipping': "SKIPPING",
        'parse_error': "Could not parse date",
        'summary': "Summary:",
        'total_checked': "Total backups checked: {}",
        'to_delete': "To be deleted:       {}",
        'kept': "Kept:                {}",
        'review_output': "Review the output. If correct, set dry_run = False in config.ini",
        'report_subject': "Lightroom Backup Cleanup - {}",
        'critical_warning': "CRITICAL WARNING",
        'no_report_sent': "No report sent (No changes/errors and no stale backup warning).",
        'email_sent': "Email notification sent successfully.",
        'email_disabled': "Email sending is disabled in config.",
        'email_failed': "Failed to send email: {}"
    },
    'nl': {
        'start_cleanup': "Start opruimen van {}",
        'max_age': "Maximale leeftijd: {} dagen",
        'retention_policy': "Bewaarbeleid: dagelijks {} dagen, wekelijks tot {} dagen, min backups: {}",
        'dry_run_mode': "Testmodus (Dry run): {}",
        'backup_dir_not_found': "Backup map niet gevonden: {}",
        'critical_error_subject': "Lightroom Backup Opruiming - KRITIEKE FOUT",
        'low_disk_space': "WAARSCHUWING LAGE SCHIJFRUIMTE: Slechts {:.2f} GB vrij (Limiet: {} GB)",
        'error_checking_disk': "Fout bij controleren schijfruimte: {}",
        'corrupt_zip': "CORRUPTE ZIP: {} - Eerste slechte bestand: {}",
        'corrupt_zip_generic': "CORRUPTE ZIP: {} is geen geldig zip bestand",
        'error_accessing_dir': "Fout bij openen backup map: {}",
        'error_subject': "Lightroom Backup Opruiming - FOUT",
        'no_backups_found': "GEEN BACKUPS GEVONDEN in {}",
        'no_recent_backup': "GEEN RECENTE BACKUP GEVONDEN! Laatste backup was {} dagen geleden ({})",
        'would_delete': "ZOU VERWIJDEREN",
        'deleting': "VERWIJDEREN",
        'older_than': "Ouder dan {} dagen",
        'recent_daily': "Recente dagelijkse backup",
        'weekly_retention': "Wekelijkse backup",
        'redundant_weekly': "Overtollige wekelijkse backup",
        'min_backup_limit': "Minimum aantal backups (bewaar nieuwste {})",
        'successfully_deleted': "Succesvol verwijderd {}",
        'error_deleting': "Fout bij verwijderen {}: {}",
        'keeping': "BEWAREN",
        'skipping': "OVERSLAAN",
        'parse_error': "Kon datum niet lezen",
        'summary': "Samenvatting:",
        'total_checked': "Totaal gecontroleerd:    {}",
        'to_delete': "Te verwijderen:          {}",
        'kept': "Bewaard:                 {}",
        'review_output': "Controleer de uitvoer. Indien correct, zet dry_run = False in config.ini",
        'report_subject': "Lightroom Backup Opruim Rapport - {}",
        'critical_warning': "KRITIEKE WAARSCHUWING",
        'no_report_sent': "Geen rapport verzonden (Geen wijzigingen/fouten en geen waarschuwingen).",
        'email_sent': "E-mailmelding succesvol verzonden.",
        'email_disabled': "E-mail verzenden is uitgeschakeld in configuratie.",
        'email_failed': "Kon e-mail niet verzenden: {}"
    }
}

def t(key, *args):
    """Retrieves the translated string and formats it with arguments."""
    lang_dict = TRANSLATIONS.get(LANGUAGE, TRANSLATIONS.get('en'))
    text = lang_dict.get(key, key)
    if args:
        return text.format(*args)
    return text

def setup_logging():
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    if logger.hasHandlers():
        logger.handlers.clear()
    
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=1*1024*1024, backupCount=4)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    log_capture_string = io.StringIO()
    string_handler = logging.StreamHandler(log_capture_string)
    string_handler.setFormatter(formatter)
    logger.addHandler(string_handler)
    
    return logger, log_capture_string

def send_email(subject, body_text, body_html=None):
    if not SEND_EMAIL:
        print(t('email_disabled'))
        return

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO

    part1 = MIMEText(body_text, 'plain')
    msg.attach(part1)
    
    if body_html:
        part2 = MIMEText(body_html, 'html')
        msg.attach(part2)

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, context=context) as server:
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(EMAIL_FROM, EMAIL_TO, msg.as_string())
        print(t('email_sent')) 
    except Exception as e:
        print(t('email_failed', e))

def parse_backup_date(dirname):
    patterns = [
        r'(\d{4}-\d{2}-\d{2}[-_ ]\d{2}[-_\.]\d{2})',
        r'(\d{4}-\d{2}-\d{2})'
    ]
    for pattern in patterns:
        match = re.search(pattern, dirname)
        if match:
            date_str = match.group(1)
            date_str_clean = date_str.replace('_', '-').replace(' ', '-').replace('.', '-')
            try:
                if len(date_str_clean) >= 16:
                     return datetime.strptime(date_str_clean[:16], '%Y-%m-%d-%H-%M')
                return datetime.strptime(date_str_clean[:10], '%Y-%m-%d')
            except ValueError:
                continue
    return None

def check_disk_space(logger):
    try:
        total, used, free = shutil.disk_usage(BACKUP_DIR)
        free_gb = free / (1024**3)
        if free_gb < MIN_FREE_SPACE_GB:
            logger.warning(t('low_disk_space', free_gb, MIN_FREE_SPACE_GB))
            return False
        return True
    except OSError as e:
        logger.error(t('error_checking_disk', e))
        return False

def check_zip_integrity(path, logger):
    """Checks if the zip file inside the directory is valid."""
    zips = [f for f in os.listdir(path) if f.endswith('.zip')]
    if not zips:
        return True 

    for zip_name in zips:
        zip_path = os.path.join(path, zip_name)
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                ret = zip_ref.testzip()
                if ret is not None:
                    logger.error(t('corrupt_zip', zip_path, ret))
                    return False
        except zipfile.BadZipFile:
            logger.error(t('corrupt_zip_generic', zip_path))
            return False
    return True

def log_to_html(log_content):
    lines = log_content.splitlines()
    html_rows = ""
    for line in lines:
        color = "#000000" # Black default
        bg_color = "transparent"
        
        if "ERROR" in line or "CRITICAL" in line or "DELETING" in line or "WOULD DELETE" in line:
            color = "#D32F2F" # Red
            bg_color = "#FFEBEE"
        elif "WARNING" in line:
            color = "#E65100" # Orange
            bg_color = "#FFF3E0"
        elif "KEEPING" in line:
            color = "#2E7D32" # Green
        elif "Summary" in line:
            bg_color = "#F5F5F5"
            line = f"<b>{line}</b>"
            
        html_rows += f"<tr style='background-color:{bg_color};'><td style='color:{color}; padding: 4px 8px; font-family: monospace;'>{line}</td></tr>"
        
    html = f"""
    <html>
    <body style="font-family: sans-serif;">
        <h2>Lightroom Backup Cleanup Report</h2>
        <table style="border-collapse: collapse; width: 100%;">
            {html_rows}
        </table>
    </body>
    </html>
    """
    return html

def cleanup_backups():
    logger, log_capture_string = setup_logging()
    
    logger.info(t('start_cleanup', BACKUP_DIR))
    logger.info(t('max_age', MAX_AGE_DAYS))
    logger.info(t('retention_policy', KEEP_DAILY_DAYS, KEEP_WEEKLY_DAYS, MIN_BACKUPS))
    logger.info(t('dry_run_mode', DRY_RUN))
    
    if LANGUAGE != 'en':
        logger.info(f"Language: {LANGUAGE} (Dutch/Nederlands)")

    should_send_report = False
    critical_error = False

    if not os.path.exists(BACKUP_DIR):
        logger.error(t('backup_dir_not_found', BACKUP_DIR))
        final_log = log_capture_string.getvalue()
        send_email(t('critical_error_subject'), final_log, log_to_html(final_log))
        return

    # Check Disk Space
    if not check_disk_space(logger):
        critical_error = True
        should_send_report = True

    now = datetime.now()
    backups = []

    try:
        items = os.listdir(BACKUP_DIR)
    except OSError as e:
        logger.error(t('error_accessing_dir', e))
        final_log = log_capture_string.getvalue()
        send_email(t('error_subject'), final_log, log_to_html(final_log))
        return

    # 1. Parse all backups
    for item in items:
        item_path = os.path.join(BACKUP_DIR, item)
        if not os.path.isdir(item_path):
            continue
        backup_date = parse_backup_date(item)
        if backup_date:
            backups.append({'path': item_path, 'name': item, 'date': backup_date})

    # Sort backups by date (newest first)
    backups.sort(key=lambda x: x['date'], reverse=True)

    # Check for "No Backup" Alert
    if not backups:
        logger.error(t('no_backups_found', BACKUP_DIR))
        critical_error = True
        should_send_report = True
    elif (now - backups[0]['date']).days > NO_BACKUP_ALERT_DAYS:
        logger.error(t('no_recent_backup', (now - backups[0]['date']).days, backups[0]['name']))
        critical_error = True
        should_send_report = True

    # 2. Determine action for each backup
    weekly_buckets = set() 

    deleted_count = 0
    kept_count = 0
    
    # Check integrity of the NEWEST backup always
    if backups:
        if not check_zip_integrity(backups[0]['path'], logger):
            critical_error = True
            should_send_report = True

    for i, backup in enumerate(backups):
        age_days = (now - backup['date']).days
        item = backup['name']
        item_path = backup['path']
        
        action = "KEEP" 
        reason = "Default"

        # MINIMUM BACKUPS CHECK
        if i < MIN_BACKUPS:
             action = "KEEP"
             reason = t('min_backup_limit', MIN_BACKUPS)
        elif age_days > MAX_AGE_DAYS:
            action = "DELETE"
            reason = t('older_than', MAX_AGE_DAYS)
        elif age_days <= KEEP_DAILY_DAYS:
            action = "KEEP"
            reason = t('recent_daily')
        else:
            year_week = backup['date'].isocalendar()[:2] 
            if year_week not in weekly_buckets:
                action = "KEEP"
                reason = t('weekly_retention')
                weekly_buckets.add(year_week)
            else:
                action = "DELETE"
                reason = t('redundant_weekly')

        if action == "DELETE":
            log_action = t('would_delete') if DRY_RUN else t('deleting')
            logger.info(f"[{log_action}] {item} (Age: {age_days} days) - {reason}")
            should_send_report = True 
            
            if not DRY_RUN:
                try:
                    shutil.rmtree(item_path)
                    logger.info(t('successfully_deleted', item))
                    deleted_count += 1
                except Exception as e:
                    logger.error(t('error_deleting', item, e))
                    should_send_report = True
                    critical_error = True
            else:
                deleted_count += 1
        else:
            logger.info(f"[{t('keeping')}]      {item} (Age: {age_days} days) - {reason}")
            kept_count += 1

    logger.info(t('summary'))
    logger.info(t('total_checked', len(backups)))
    logger.info(t('to_delete', deleted_count))
    logger.info(t('kept', kept_count))
    
    if DRY_RUN and deleted_count > 0:
        logger.info(t('review_output'))

    # Send Email Report if necessary
    if should_send_report or critical_error:
        status_suffix = "DRY RUN" if DRY_RUN else "REPORT"
        if critical_error:
            status_suffix = t('critical_warning')
        
        log_contents = log_capture_string.getvalue()
        subject = t('report_subject', status_suffix)
        send_email(subject, log_contents, log_to_html(log_contents))
    else:
        logger.info(t('no_report_sent'))

    log_capture_string.close()

if __name__ == "__main__":
    cleanup_backups()
