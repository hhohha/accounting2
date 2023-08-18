from enum import Enum

class ClsType(Enum):
    TR_TYPE = 0
    CATEGORY = 1
    TAG = 2

class TransactionStatus(Enum):
    NEW = 'new'
    MODIFIED = 'modified'
    SAVED = 'saved'

class CsvType(Enum):
    KB = 'kb'
    MB = 'mb'