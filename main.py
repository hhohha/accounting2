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

def show_details(transaction: Transaction):
    window['txt_detail_bank'].update(transaction.bank)
    window['txt_detail_acc_no'].update(transaction.toAccount)
    window['txt_detail_acc_name'].update(transaction.toAccountName)
    window['txt_detail_vs'].update(transaction.variableSymbol)
    window['txt_detail_cs'].update(transaction.constantSymbol)
    window['txt_detail_ss'].update(transaction.specificSymbol)
    window['txt_detail_desc'].update(transaction.systemDescription)
    window['txt_detail_sender_msg'].update(transaction.senderDescription)
    window['txt_detail_addressee_msg'].update(transaction.addresseeDescription)
    window['txt_detail_av1'].update(transaction.AV1)
    window['txt_detail_av2'].update(transaction.AV2)
    window['txt_detail_av3'].update(transaction.AV3)
    window['txt_detail_av4'].update(transaction.AV4)

def main():

    clsNames: Dict[Optional[int], str] = {c[0]: c[1] for c in dbif.get_all_classifications(ClsType.CATEGORY)
                                          + dbif.get_all_classifications(ClsType.TR_TYPE) + dbif.get_all_classifications(ClsType.TAG)}
    clsNames[None] = 'unknown'

    transactions: Dict[int, Transaction] = {}

    while True:
        event, values = window.read()

        if event in (None, 'exit'):
            break
        elif event == 'btn_load_data':
            transactions = {t[0]: Transaction(*t) for t in dbif.get_transactions()}
            window['tbl_transactions'].update(values=[transaction_to_table_row(t, clsNames) for t in transactions.values()])
        elif event == 'btn_load_from_file':
            # TODO
            pass
        elif event == 'tbl_transactions':
            #print(f'values: {values}')
            lineSelected = values['tbl_transactions'][0]
            #print(f'selected line: {lineSelected}')
            txId = window["tbl_transactions"].get()[lineSelected][0]
            transactionSelected = transactions[txId]
            #print(f'selected tx: {transactionSelected}')
            transactionSelected.load_tags()
            show_details(transactionSelected)
            print(f'tags: {transactionSelected.tags}')
            window['tbl_detail_tags'].update(values=[clsNames[tid] for tid in transactionSelected.tags])

if __name__ == '__main__':
    main()
