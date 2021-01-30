"""
Backup PostgreSQL database to Google Drive.
"""
import datetime
import os
import pytz
from googledisk import GoogleDrive
import psycopg2
import getpass

DB_HOSTNAME = os.getenv("DB_HOSTNAME", 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD", '')
BACKUP_KEY = os.getenv("BACKUP_KEY")
TIME_ZONE = os.getenv("TIME_ZONE", "Europe/Moscow")
ID_PARENT_FOLDER = os.getenv("ID_PARENT_FOLDER")

DB_PATH_ENCRYPTED = "/tmp/backup_db.sql.gz.enc"


def _connect_db_and_check_connection(_password=DB_PASSWORD):
    _password = f" password={_password}" if _password else str('')
    try:
        _connection = psycopg2.connect(
            f"dbname={DB_NAME} user={DB_USER} host='{DB_HOSTNAME}'{_password}")
    except psycopg2.OperationalError as oe:
        if str(oe) == 'fe_sendauth: no password supplied\n':
            global DB_PASSWORD
            DB_PASSWORD = getpass.getpass(prompt=f'Password for user {DB_USER}: ', stream=None)
            return _connect_db_and_check_connection(DB_PASSWORD)
        elif str(oe) == f'FATAL:  password authentication failed for user "{DB_USER}"\n' \
                        f'FATAL:  password authentication failed for user "{DB_USER}"\n':
            exit(str(oe).splitlines()[0], )
        else:
            exit(oe)
    _cursor = _connection.cursor()
    return _connection, _cursor


def say_hello():
    print("Hi! This tool will dump PostgreSQL database, compress \n"
          "and encode it, and then send to Google Drive.\n")


def get_now_datetime_str():
    now = datetime.datetime.now(pytz.timezone(TIME_ZONE))
    return now.strftime('%Y-%m-%d__%H-%M-%S')


def check_key(secret=False):
    from gnupg import GPG
    key = GPG().list_keys(secret=secret).key_map.get(BACKUP_KEY)
    if not key:
        exit(
            f"\U00002757 Public encrypt key ({BACKUP_KEY}) "
            f"not found. If you have no key – you need to generate it. "
        ) if not secret else exit(
            f"\U00002757 Private encrypt key ({BACKUP_KEY}) "
            f"not found."
        )
    else:
        print(f'\U0001F511 Selected key - {key["uids"][0]}')


def dump_database():
    print("\U0001F4E6 Preparing database backup started")
    _escaped_password = ":"+"\\".join(DB_PASSWORD) if DB_PASSWORD else ""
    dump_db_operation_status = os.WEXITSTATUS(os.system(
        f"pg_dump --db=postgres://{DB_USER}{_escaped_password}@{DB_HOSTNAME}:{DB_PORT}/{DB_NAME} | "
        f"gzip -c --best | gpg -e -r {BACKUP_KEY} > {DB_PATH_ENCRYPTED}"
    ))
    if dump_db_operation_status != 0:
        exit(f"\U00002757 Dump database command exits with status "
             f"{dump_db_operation_status}.")
    print("\U0001F510 DB dumped, archieved and encoded")


def upload_dump_to_google_disk():
    print("\U0001F4C2 Starting upload to Object Storage")
    GoogleDrive().upload_file(
        filename=f'db-{get_now_datetime_str()}.sql.gz.enc',
        path=DB_PATH_ENCRYPTED,
        folder_id=ID_PARENT_FOLDER
    )
    print("\U0001f680 Uploaded")


def remove_temp_files():
    os.remove(DB_PATH_ENCRYPTED)
    print("\U0001F44D That's all!")


if __name__ == '__main__':
    say_hello()
    _connect_db_and_check_connection()
    check_key()
    dump_database()
    upload_dump_to_google_disk()
    remove_temp_files()
