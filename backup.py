"""
Backup PostgreSQL database to Google Drive.
"""
import datetime
import os
import pytz
from googledisk import GoogleDrive
from helpers import *

DB_HOSTNAME = os.getenv("DB_HOSTNAME", 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD", '')
BACKUP_KEY = os.getenv("BACKUP_KEY")
TIME_ZONE = os.getenv("TIME_ZONE", "Europe/Moscow")
ID_PARENT_FOLDER = os.getenv("ID_PARENT_FOLDER")

DB_PATH_ENCRYPTED = "/tmp/backup_db.sql.gz.enc"


def say_hello():
    print("Hi! This tool will dump PostgreSQL database, compress \n"
          "and encode it, and then send to Google Drive.\n")


def get_now_datetime_str():
    now = datetime.datetime.now(pytz.timezone(TIME_ZONE))
    return now.strftime('%Y-%m-%d__%H-%M-%S')


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
    _, _, DB_PASSWORD = connect_db_and_check_connection(db_name=DB_NAME, db_user=DB_USER, db_hostname=DB_HOSTNAME,
                                                        db_port=DB_PORT, db_password=DB_PASSWORD)
    check_key(BACKUP_KEY)
    dump_database()
    upload_dump_to_google_disk()
    remove_temp_files()
