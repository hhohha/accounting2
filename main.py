import logging
from typing import Dict, List, Optional

import dbif
from enums import ClsType, TransactionStatus
from layout import window
from transaction import Transaction


def transaction_to_table_row(transaction: Transaction, clsNames: Dict[Optional[int], str]) -> List[str]:
    try:
        trTypeName = clsNames[transaction.trType]
    except KeyError:
        trTypeName = 'error'
        logging.error(f'DB inconsistent: unknown classification: {transaction.trType}')
    try:
        categoryName = clsNames[transaction.category]
    except KeyError:
        categoryName = 'error'
        logging.error(f'DB inconsistent: unknown classification: {transaction.category}')

    description = ','.join(filter(lambda f: f is not None, [transaction.AV1, transaction.AV2, transaction.AV3, transaction.AV4])),

    return [transaction.id, transaction.dueDate, transaction.amount, description, trTypeName, categoryName, TransactionStatus.SAVED.value]

def main():

    clsNames: Dict[Optional[int], str] = {c[0]: c[1] for c in dbif.get_all_classifications(ClsType.CATEGORY) + dbif.get_all_classifications(ClsType.TR_TYPE)}
    clsNames[None] = 'unknown'

    transactions: Dict[int, Transaction]

    while True:
        event, values = window.read()

        if event in (None, 'exit'):
            break
        elif event == 'btn_load_data':
            transactions = {t[0]: Transaction(*t) for t in dbif.get_transactions()}
            window['tbl_transactions'].update(values=[transaction_to_table_row(t, clsNames) for t in transactions.values()])


if __name__ == '__main__':
    main()
