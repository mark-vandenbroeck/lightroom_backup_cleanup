# Lightroom Backup Opruim Script

Dit Python script automatiseert het onderhoud van je Lightroom backup mappen. Het verwijdert slim oude backups terwijl dagelijkse en wekelijkse versies bewaard blijven, controleert op data-integriteit, bewaakt de schijfruimte en stuurt e-mailmeldingen bij kritieke gebeurtenissen.

## Functies

-   **Slim Bewaarbeleid (Retention Policy)**:
    -   **0 - 7 dagen**: Bewaart alle dagelijkse backups.
    -   **7 - 60 dagen**: Bewaart één backup per week (Slim uitdunnen).
    -   **> 60 dagen**: Verwijdert alle backups (tenzij minimum aantal backups wordt bereikt).
    -   **Minimum Aantal Backups**: Bewaart altijd minstens `min_backups` (standaard 5), ongeacht leeftijd.
-   **Integriteitscontrole**: Controleert of het `.zip` bestand in de backup map niet corrupt is.
-   **Schijfruimte Monitoring**: Waarschuwt als de vrije schijfruimte onder een instelbare limiet komt (standaard 10GB).
-   **Alarm "Geen Backup"**: Stuurt een alarm als er in de laatste 31 dagen geen nieuwe backup is gemaakt.
-   **HTML Rapporten**: Stuurt mooi opgemaakte tabellen via e-mail.
-   **Conditionele Rapportage**: Stuurt **alleen** e-mailmeldingen wanneer:
    -   Een backup wordt verwijderd.
    -   Er een fout optreedt (bijv. corrupte zip, schijf vol).
    -   Er een waarschuwing is (bijv. geen recente backup).
-   **Gedetailleerde Logging**: Houdt een roterend logbestand bij (`cleanup_backup.log`) (max 1MB, 4 bestanden).
-   **SMB Backup Kopie & Retentie**: Kopieert nieuwe backups automatisch naar een externe SMB (Samba) share en past daar hetzelfde bewaarbeleid op toe. Ondersteunt automatische koppeling (mounting) op macOS via `osascript`.

## Installatie

1.  **Vereisten**:
    -   Python 3 geïnstalleerd op macOS.
    -   Standaard bibliotheken: `os`, `shutil`, `logging`, `datetime`, `re`, `smtplib`, `ssl`, `email`, `configparser`, `zipfile`.

2.  **Bestanden**:
    -   `cleanup_backups.py`: Het hoofdscript.
    -   `config.ini`: Configuratiebestand (moet in dezelfde map staan).

## Configuratie (`config.ini`)

1.  **Kopieer de voorbeeldconfiguratie**:
    ```bash
    cp sample_config_ned.ini config.ini
    ```
2.  **Bewerk `config.ini`**:
    Open `config.ini` in een teksteditor en pas de waarden aan.
    Het bestand bevat gedetailleerd commentaar (in het Nederlands) bij elke parameter.

    **Belangrijkste instellingen**:
    -   `backup_dir`: Pad naar je backups.
    -   `max_age_days`: Maximale bewaartijd.
    -   `min_backups`: Minimum aantal te bewaren backups (veiligheidsnet).
    -   `dry_run`: Zet op `True` om te testen, `False` om daadwerkelijk te verwijderen.
    -   `language`: `en` (Engels) of `nl` (Nederlands).
    -   `[Email]`: Configureer SMTP instellingen als je meldingen wilt ontvangen. Zet `send_email = False` om uit te schakelen.
    -   `[SMB]`: Configureer `enable_smb`, `smb_url`, `smb_mount_path` en `smb_backup_dir` om backups naar een Samba-netwerkmap te kopiëren en daar opruimregels op toe te passen.


## Gebruik

### Handmatige Uitvoer

Draai het script handmatig om de configuratie te testen of een opruiming te forceren:

```bash
python3 cleanup_backups.py
```

Controleer de terminal uitvoer of `cleanup_backup.log` voor details.

### Geautomatiseerde Uitvoer (Cron)

Het script is ontworpen om automatisch via `cron` te draaien.
Voorbeeld crontab regel (draait dagelijks om 22:30):

```bash
30 22 * * * /usr/bin/python3 /Users/mark/Documents/Python/Lightroom/cleanup_backup/cleanup_backups.py
```

Om je crontab te bewerken, typ `crontab -e` in de terminal.

## Logs

Logs worden opgeslagen in dezelfde map als het script: `cleanup_backup.log`.
Het logbestand roteert automatisch wanneer het 1MB bereikt, waarbij tot 4 historische logbestanden bewaard blijven.

## Veiligheid

-   **Dry Run**: Zet altijd `dry_run = True` wanneer je wijzigingen aanbrengt in de configuratie of nieuwe logica test.
-   **E-mail Alerts**: Gebruik indien mogelijk een **App Password** voor je e-mailaccount in plaats van je hoofdwachtwoord, voor betere beveiliging.
