from __future__ import annotations
from enum import Enum
from typing import Set, TYPE_CHECKING, Optional, List, Tuple
import mysql.connector
from enums import ClsType
from utils import value_or_null
from datetime import date

if TYPE_CHECKING:
    from transaction import Transaction

DB_HOST = 'localhost'
DB_USER = 'honza'
DB_PASSWORD = 'jejda'
DB_NAME = 'accounting2'

class Table(Enum):
    TRANSACTIONS = 'transactions'
    SIGNATURES = 'signatures'
    CLASSIFICATIONS = 'classifications'
    TAG_LINKS = 'tag_links'

transactionFieldsSelect = ["id", "dueDate", "amount", "bank", "category", "trType", "writeOffDate", "toAccount", "toAccountName", "originalAmount",
                           "originalCurrency", "rate", "variableSymbol", "constantSymbol", "specificSymbol", "transactionIdentifier",
                           "systemDescription", "senderDescription", "addresseeDescription", "AV1", "AV2", "AV3", "AV4"]

transactionFieldsSave = transactionFieldsSelect + ['signature']

def get_setting(key: str) -> Optional[str]:
    retval = sql_query(f'select sValue from settings where sKey = "{key}"')
    if len(retval) == 0:
        return None
    else:
        return retval[0][0]

def set_setting(key: str, value: str) -> None:
    sql_query(f'delete from settings where sKey = "{key}"')
    sql_query(f'insert into settings (sKey, sValue) values ("{key}", "{value}")')

def sql_query(sql: str) -> list:
    mydb = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASSWORD, database=DB_NAME)

    myCursor = mydb.cursor()
    myCursor.execute(sql)
    sql = sql.lower().strip()

    if sql.startswith('select'):
        return myCursor.fetchall()
    elif sql.startswith('update') or sql.startswith('insert') or sql.startswith('delete'):
        mydb.commit()
        return []
    else:
        assert False, f"bad sql query: {sql}"

def get_new_id(table: Table) -> int:
    idx = sql_query(f'select max(id) from {table.value}')[0][0]
    assert isinstance(idx, int) or idx is None, f"invalid new id received from table {table.value}"
    return idx + 1 if isinstance(idx, int) else 0

def add_new_signature(clsId: int, signature: str) -> int:
    newId = get_new_id(Table.SIGNATURES)
    sql_query(f'insert into signatures (id, cls_id, value) values ({newId}, {clsId}, "{signature}")')
    return newId

def remove_signature(idx: int) -> None:
    sql_query(f'delete from signatures where id = {idx}')

def get_signatures_of_cls_type(cls: ClsType) -> list:
    return sql_query(f'select c.id, s.value from classifications c, signatures s where s.cls_id = c.id and c.type = {cls.value}')

def get_signatures(clsId: int) -> list:
    return sql_query(f'select id, cls_id, value from signatures where cls_id = {clsId}')

def get_classifications(cls: Optional[ClsType] = None) -> list:
    filters = f'where type = {cls.value}' if cls is not None else ''
    return sql_query(f'select id, type, name from classifications {filters}')

def add_new_classification(cls: ClsType, name: str) -> int:
    newId = get_new_id(Table.CLASSIFICATIONS)
    sql_query(f'insert into classifications (id, type, name) values ({newId}, {cls.value}, "{name}")')
    return newId

def parse_fields(t: Transaction, fields: List[str]) -> Tuple[str, str]:
    columnNames: List[str] = []
    columnValues: List[str] = []

    for field in fields:
        value = getattr(t, field)
        if not value:
            continue
        elif isinstance(value, str):
            value = value.strip()
            if not value:
                continue
            value = f'"{value}"'
        elif isinstance(value, date):
            value = f'"{value}"'
        else:
            value = str(value)
        columnNames.append(field)
        columnValues.append(value)

    return ','.join(columnNames), ','.join(columnValues)

def save_new_transaction(t: Transaction) -> int:
    assert t.id is None, "transaction already has an id"

    t.id = get_new_id(Table.TRANSACTIONS)

    columnNames, columnValues = parse_fields(t, transactionFieldsSave)
    print(f'QUERY: insert into transactions ({columnNames}) values ({columnValues})')

    sql_query(f'insert into transactions ({columnNames}) values ({columnValues})')
    return t.id

def save_modified_transaction(t: Transaction) -> None:
    updatedColumns = ', '.join([f'{field} = {value_or_null(t, field, commas=False)}' for field in transactionFieldsSave])
    sql_query(f'update transactions set {updatedColumns} where id = {t.id}')

def get_transactions(filters: str = '') -> list:
    return sql_query(f'''
        select {",".join(["t." + field for field in transactionFieldsSelect])}, group_concat(tl.cls_id)
        from transactions as t left join tag_links as tl on tl.trans_id = t.id
        {filters}
        group by t.id
        order by t.dueDate
    ''')

def get_tags(trId: int) -> list:
    return sql_query(f'select distinct cls_id from tag_links where trans_id = {trId}')

def remove_transaction(trId: int) -> None:
    sql_query(f'delete from tag_links where trans_id = {trId}')
    sql_query(f'delete from transactions where id = {trId}')

def remove_tags(trId: int, tagIds: Set[int]) -> None:
    sql_query(f'delete from tag_links where trans_id = {trId} and cls_id in ({",".join(map(str, tagIds))})')

def add_tags(trId: int, tagIds: Set[int]) -> None:
    for tagId in tagIds:
        add_tag(trId, tagId)

def add_tag(trId: int, tagId: int) -> None:
    sql_query(f'insert into tag_links (trans_id, cls_id) values ({trId}, {tagId})')