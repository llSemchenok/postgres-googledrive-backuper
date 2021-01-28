"""
Renew database on current server, if hostname startswith loader*
or ends with .local (can be modified in check_hostname function below).
Script download last dump from Google Drive, decrypt
and load it after clear current database state.
"""
import os
import socket

import psycopg2

from googledisk import GoogleDrive

DB_HOSTNAME = os.getenv("DB_HOSTNAME", "localhost")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
BACKUP_KEY = os.getenv("BACKUP_KEY")
TIME_ZONE = os.getenv("TIME_ZONE", "Europe/Moscow")
ID_PARENT_FOLDER = os.getenv("ID_PARENT_FOLDER")
CHECK_HOSTNAME = os.getenv("CHECK_HOSTNAME", False)

DB_PATH_ENCRYPTED = "/tmp/backup_db.sql.gz.enc"
DB_PATH_DECRYPTED = "/tmp/db.sql.gz"

connection = psycopg2.connect(
    f"dbname={DB_NAME} user={DB_USER} host='{DB_HOSTNAME}'")
cursor = connection.cursor()


def say_hello():
    print(
        "This tool will download last database backup from Google Drive, \n"
        "decompress and unzip it, and then load to local database \n")


def check_hostname():
    hostname = socket.gethostname()
    if not hostname.startswith('loader-') and not hostname.endswith('.local'):
        exit(f"\U00002757 It seems this is not loader server "
             f"({hostname}), exit.")
    print("We are on some loader or local server, ok\n")


def check_pub_key():
    from gnupg import GPG
    if not GPG().export_keys(BACKUP_KEY, True, expect_passphrase=False):
        exit(
            f"""\U00002757 Private encrypt key ({BACKUP_KEY}) "
            "not found. You can find help here: "
            "https://www.imagescape.com/blog/2015/12/18/encrypted-postgres-backups/"""
        )


def download_last_backup_file():
    file = GoogleDrive().get_list_files_ids_in_folder(ID_PARENT_FOLDER)[0]  # get backup files

    print(f"\U000023F3 Last backup in Google Drive is {file['name']}, \nfile id {file['id']}], "
          f"{str(round(float(file['size']) / (1024 * 1024), 3))} MB, download it")
    GoogleDrive().download_file(file['id'], DB_PATH_ENCRYPTED)
    print(f"\U0001f680 Downloaded {file['webContentLink']}")


def decrypt_database():
    operation_status = os.WEXITSTATUS(os.system(
        f"gpg -d -o {DB_PATH_DECRYPTED} {DB_PATH_ENCRYPTED}"
    ))
    if operation_status != 0:
        exit(f"\U00002757 Can not decrypt db file, status "
             f"{operation_status}.")
    print(f"\U0001F511 Database decrypted")


def unzip_database():
    _silent_remove_file('/tmp/db.sql')
    operation_status = os.WEXITSTATUS(os.system(
        f"""gzip -d {DB_PATH_DECRYPTED}"""
    ))
    if operation_status != 0:
        exit(f"\U00002757 Can not decrypt db file, status "
             f"{operation_status}.")
    print(f"\U0001F4E4 Database unzipped")


def clear_database():
    tables = _get_all_db_tables()
    if not tables:
        return
    with connection:
        with connection.cursor() as local_cursor:
            local_cursor.execute("\n".join([
                f'drop table if exists "{table}" cascade;'
                for table in tables]))
    print(f"\U0001F633 Database cleared")


def load_database():
    print(f"\U0001F4A4 Database load started")
    operation_status = os.WEXITSTATUS(os.system(
        f"""psql -h {DB_HOSTNAME} -U {DB_USER} {DB_NAME} < /tmp/db.sql"""
    ))
    if operation_status != 0:
        exit(f"\U00002757 Can not load database, status {operation_status}.")
    print(f"\U0001F916 Database loaded")


def remove_temp_files():
    _silent_remove_file(DB_PATH_ENCRYPTED)
    print("\U0001F44D That's all!")


def _get_all_db_tables():
    cursor.execute("""SELECT table_name FROM information_schema.tables
                      WHERE table_schema = 'public' order by table_name;                                            """)
    results = cursor.fetchall()
    tables = []
    for row in results:
        tables.append(row[0])
    return tables


def _silent_remove_file(filename: str):
    try:
        os.remove(filename)
    except FileNotFoundError:
        pass


if __name__ == "__main__":
    say_hello()
    if CHECK_HOSTNAME:
        check_hostname()
    download_last_backup_file()
    decrypt_database()
    unzip_database()
    clear_database()
    load_database()
    remove_temp_files()
