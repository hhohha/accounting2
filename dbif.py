from __future__ import annotations
from enum import Enum
from typing import Set, TYPE_CHECKING
import mysql.connector
from enums import ClsType

if TYPE_CHECKING:
    from transaction import Transaction

class Table(Enum):
    TRANSACTIONS = 'transactions'
    SIGNATURES = 'signatures'
    CLASSIFICATIONS = 'classifications'
    TAG_LINKS = 'tag_links'

transactionFields = ["id", "dueDate", "amount", "bank", "category", "trType", "writeOffDate", "toAccount", "toAccountName", "currency", "rate",
                     "variableSymbol", "constantSymbol", "specificSymbol", "transactionIdentifier", "systemDescription", "senderDescription",
                     "addresseeDescription", "AV1", "AV2", "AV3", "AV4"]

def nameIfPresent(obj, name: str) -> str:
    return name + ', ' if getattr(obj, name) is not None else ''

def valueIfPresent(obj, name: str) -> str:
    return f', {str(getattr(obj, name))} ' if getattr(obj, name) is not None else ''

def valueOrNull(obj, name: str) -> str:
    return f', {str(getattr(obj, name))} ' if getattr(obj, name) is not None else ', null '

def sql_query(sql: str) -> list:
    mydb = mysql.connector.connect(host='localhost', user='honza', password='jejda', database='accounting2')

    myCursor = mydb.cursor()
    myCursor.execute(sql)
    sql = sql.lower()

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

def change_signature(idx: int, signature: str) -> None:
    sql_query(f'update signatures set value = "{signature}" where id = {idx}')

def remove_signature(idx: int) -> None:
    sql_query(f'delete from signatures where id = {idx}')

def get_all_classifications(cls: ClsType) -> list:
    return sql_query(f'select id, name from classifications where type = {cls.value}')

def get_signatures_of_cls_type(cls: ClsType) -> list:
    return sql_query(f'select c.id, s.value from classifications c, signatures s where s.cls_id = c.id and c.cls_type = {cls.value}')

def add_new_classification(cls_type: int, name: str) -> int:
    newId = get_new_id(Table.CLASSIFICATIONS)
    sql_query(f'insert into classifications (id, cls_type, name) values ({newId}, {cls_type}, "{name}")')
    return newId

def save_new_transaction(t: Transaction) -> int:
    assert t.id is None, "transaction already has an id"
    assert t.category is not None, "transaction has no category"
    assert t.trType is not None, "transaction has no type"

    t.id = get_new_id(Table.TRANSACTIONS)
    columnNames = [nameIfPresent(t, field) for field in transactionFields]
    columnValues = [valueIfPresent(t, field) for field in transactionFields]

    sql_query(f'insert into transactions ({columnNames}) values ({columnValues})')
    return t.id

def save_modified_transaction(t: Transaction) -> None:
    updatedColumns = [f'{field} = {valueOrNull(t, field)}' for field in transactionFields]
    sql_query(f'update transactions set {updatedColumns} where id = {t.id}')

def get_transaction(trId: int) -> Transaction:
    result = sql_query(f'select * from transactions where id = {trId}')
    assert len(result) == 1, f"transaction with id {trId} not found"
    return result[0]

def get_transactions(filters: str) -> list:
    # TODO: review
    return sql_query(f'select t.*, x.id tags from transactions t left join (select * from tag_links l, classifications c where l.cls_id = c.id)'
                     f' x on x.trans_id = t.id {filters} order by t.tdate')

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