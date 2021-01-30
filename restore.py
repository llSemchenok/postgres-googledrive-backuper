"""
Renew database on current server, if hostname startswith loader*
or ends with .local (can be modified in check_hostname function below).
Script download last dump from Google Drive, decrypt
and load it after clear current database state.
"""
import os
import socket
import psycopg2
import getpass

from googledisk import GoogleDrive

DB_HOSTNAME = os.getenv("DB_HOSTNAME", "localhost")
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
BACKUP_KEY = os.getenv("BACKUP_KEY")
TIME_ZONE = os.getenv("TIME_ZONE", "Europe/Moscow")
ID_PARENT_FOLDER = os.getenv("ID_PARENT_FOLDER")
CHECK_HOSTNAME = os.getenv("CHECK_HOSTNAME", False)

DB_PATH_ENCRYPTED = "/tmp/backup_db.sql.gz.enc"
DB_PATH_DECRYPTED = "/tmp/db.sql.gz"


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
    print(
        "This tool will download last database backup from Google Drive, \n"
        "decompress and unzip it, and then load to local database \n")


def check_hostname():
    hostname = socket.gethostname()
    if not hostname.startswith('loader-') and not hostname.endswith('.local'):
        exit(f"\U00002757 It seems this is not loader server "
             f"({hostname}), exit.")
    print("We are on some loader or local server, ok\n")


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
    _escaped_password = ":"+"\\".join(DB_PASSWORD) if DB_PASSWORD else ""
    operation_status = os.WEXITSTATUS(os.system(
        f"psql --db=postgres://{DB_USER}{_escaped_password}@{DB_HOSTNAME}:{DB_PORT}/{DB_NAME} < /tmp/db.sql"
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
    connection, cursor = _connect_db_and_check_connection()
    if CHECK_HOSTNAME:
        check_hostname()
    check_key(True)
    download_last_backup_file()
    decrypt_database()
    unzip_database()
    clear_database()
    load_database()
    remove_temp_files()
