from typing import Dict

import dbif
from layout import window
from transaction import Transaction


def main():


    # window.cls_transl = dbif.get_cls_transl()
    # window.cls_transl[None] = 'unknown'
    transactions: Dict[int, Transaction] = {}
    # tr_data = []

    while True:
        event, values = window.read()

        if event in (None, 'exit'):
            break
        elif event == 'btn_load_data':
            for line in dbif.get_transactions():
                transactions[line[0]] = Transaction(*line)
            for t in transactions.values():
                print(t)
            #print(transactions)

if __name__ == '__main__':
    main()
