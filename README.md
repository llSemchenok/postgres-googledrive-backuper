Backup and restore PostgreSQL database with Google Drive
===
There are two scripts: `backup.py` and` restore.py`. The first one creates 
Dump PostgreSQL, zip it and encrypt it, then save it to Google Drive. The second one finds the last dump in
Google Drive, downloads, unzips and decrypts it, and then uploads it to
PostgreSQL database.

To run scripts you need:
* Python 3.6 or greater,
* The pip package management tool,
* A Google account with enable [Google Drive Activity API](https://developers.google.com/drive/activity/v2/quickstart/python#step_1_turn_on_the),
* To have access to a compatible version of the [GnuPG executable](https://docs.red-dove.com/python-gnupg/#deployment-requirements),
* Check `check_hostname()` function in `restore.py` — it checks hostname of current server (kind of protection against drop database tables on production server).

Example of backup database (substitute your values in the variables below):

```sh
DB_HOSTNAME=your_hostname \ # Default localhost
DB_PORT=your_port \ # Default 5432, can be omitted
DB_NAME=your_database  \ 
DB_USER=your_db_user  \
DB_PASSWORD=your_db_password \ # Can be omitted, if no password is specified, the script will ask for it
BACKUP_KEY=your_key_id \ # Use the `gpg --list-secret-keys --keyid-format LONG` command to list GPG keys
ID_PARENT_FOLDER==your_id_google_drive_folder \ # Create folder in google drive and copy id folder from url
TIME_ZONE=Europe/Moscow \
CREDENTIALS_PATH=/path/to/credentials.json \ # Default looks in script folder
python3 backup.py
```

Example of restore database:

```sh
DB_HOSTNAME=your_hostname \ # Default localhost
DB_PORT=your_port \ # Default 5432, can be omitted
DB_NAME=your_database  \ 
DB_USER=your_db_user  \
DB_PASSWORD=your_db_password \ # Can be omitted, if no password is specified, the script will ask for it
BACKUP_KEY=your_key_id \ # Use the `gpg --list-secret-keys --keyid-format LONG` command to list GPG keys
CHECK_HOSTNAME=true \ # Default false, delete this is line if you don't want check hostname
ID_PARENT_FOLDER==your_id_google_drive_folder \ # Create folder in google drive and copy id folder from url
TIME_ZONE=Europe/Moscow \
CREDENTIALS_PATH=/path/to/credentials.json \ # Default looks in script folder
python3 restore.py
```