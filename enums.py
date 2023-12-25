from enum import Enum

class ClsType(Enum):
    TR_TYPE = 0
    CATEGORY = 1
    TAG = 2

class TransactionStatus(Enum):
    NEW = 'new'
    MODIFIED = 'modified'
    SAVED = 'saved'
    DUPLICATE = 'duplicate'

class CsvType(Enum):
    KB = 'kb'
    MB = 'mb'

class Settings(Enum):
    LAST_BACKUP = 'last_backup'