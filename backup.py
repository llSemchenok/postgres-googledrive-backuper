"""
Backup PostgreSQL database to Google Drive.
"""
import datetime
import os
import pytz
from googledisk import GoogleDrive

DB_HOSTNAME = os.getenv("DB_HOSTNAME", "localhost")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
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


def check_pub_key():
    from gnupg import GPG
    if not GPG().export_keys(BACKUP_KEY):
        exit(
            f"\U00002757 Public encrypt key ({BACKUP_KEY}) "
            f"not found. If you have no key – you need to generate it. "
            f"You can find help here: "
            f"https://www.imagescape.com/blog/2015/12/18/encrypted-postgres-backups/"
        )


def dump_database():
    print("\U0001F4E6 Preparing database backup started")
    dump_db_operation_status = os.WEXITSTATUS(os.system(
        f"""pg_dump -h {DB_HOSTNAME} -U {DB_USER} {DB_NAME} | \
         gzip -c --best | gpg -e -r {BACKUP_KEY} > {DB_PATH_ENCRYPTED} """
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
    check_pub_key()
    dump_database()
    upload_dump_to_google_disk()
    remove_temp_files()
