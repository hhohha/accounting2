import time, os
from dbif import DB_HOST, DB_USER, DB_PASSWORD, DB_NAME

# TODO - maybe encrypt the backup and send to cloud, keep last 3 backups
def backup_db() -> int:
    currentTime = time.strftime('%Y-%m-%d')
    BACKUP_DIR = '/home/honza/projects/accounting2/backups'
    BACKUP_FILE = f'{BACKUP_DIR}/accounting2-{currentTime}.sql'

    cmd = f'mysqldump -h {DB_HOST} -u {DB_USER} -p{DB_PASSWORD} {DB_NAME} > {BACKUP_FILE}'
    return os.system(cmd)

def restore_db(filename: str) -> int:
    cmd = f'mysql -h {DB_HOST} -u {DB_USER} -p{DB_PASSWORD} {DB_NAME} < {filename}'
    return os.system(cmd)