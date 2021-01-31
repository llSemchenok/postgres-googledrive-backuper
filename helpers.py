from gnupg import GPG
import psycopg2
import getpass


def connect_db_and_check_connection(db_name: str, db_user: str, db_hostname: str, db_port: str = 5432,
                                    db_password: str = None):
    try:
        connection = psycopg2.connect(
            f"dbname={db_name} user={db_user} host='{db_hostname}' port={db_port}"
            f"{f' password={db_password}' if db_password else str('')}")
    except psycopg2.OperationalError as oe:
        if str(oe) == 'fe_sendauth: no password supplied\n':
            db_password = getpass.getpass(prompt=f'Password for user {db_user}: ', stream=None)
            return connect_db_and_check_connection(db_password)
        elif str(oe) == f'FATAL:  password authentication failed for user "{db_user}"\n' \
                        f'FATAL:  password authentication failed for user "{db_user}"\n':
            exit(str(oe).splitlines()[0], )
        else:
            exit(oe)
    return connection, connection.cursor(), db_password


def check_key(key_id: str, secret: bool = False):
    key = GPG().list_keys(secret=secret).key_map.get(key_id)
    if not key:
        exit(
            f"\U00002757 Public encrypt key ({key}) "
            f"not found. If you have no key – you need to generate it. "
        ) if not secret else exit(
            f"\U00002757 Private encrypt key ({key}) "
            f"not found."
        )
    else:
        print(f'\U0001F511 Selected key - {key["uids"][0]}')
