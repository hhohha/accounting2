import logging
from datetime import date

import PySimpleGUI as sg
from typing import Dict, List, Optional

import dbif
from enums import ClsType, TransactionStatus
from layout import window
from transaction import Transaction

class Application:
    def __init__(self):
        allClassifications = dbif.get_classifications()
        self.clsIdToName: Dict[Optional[int], str] = {c[0]: c[1] for c in allClassifications}
        self.clsIdToName[None] = 'unknown'
        self.clsNameToId: Dict[str, int] = {c[1]: c[0] for c in allClassifications}
        self.transactions: List[Transaction] = []

    def transaction_to_table_row(self, transaction: Transaction) -> List[str | int | date | None]:
        try:
            trTypeName = self.clsIdToName[transaction.trType]
        except KeyError:
            trTypeName = 'error'
            logging.error(f'DB inconsistent: unknown classification: {transaction.trType}')
        try:
            categoryName = self.clsIdToName[transaction.category]
        except KeyError:
            categoryName = 'error'
            logging.error(f'DB inconsistent: unknown classification: {transaction.category}')

        description = ','.join(filter(lambda f: f is not None, [transaction.AV1, transaction.AV2, transaction.AV3, transaction.AV4])) # type: ignore

        return [transaction.id, transaction.dueDate, transaction.amount, description, trTypeName, categoryName, transaction.status.value]

    def reload_transaction_table(self, reloadFromDB: bool=True) -> None:
        if reloadFromDB:
            self.transactions = [Transaction(*t) for t in dbif.get_transactions()]
        window['tbl_transactions'].update(values=[self.transaction_to_table_row(t) for t in self.transactions])

    def show_details(self, transaction: Transaction) -> None:
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

    def clear_details(self) -> None:
        for key in ['txt_detail_bank', 'txt_detail_acc_no', 'txt_detail_acc_name', 'txt_detail_vs', 'txt_detail_cs', 'txt_detail_ss',
                    'txt_detail_desc', 'txt_detail_sender_msg', 'txt_detail_addressee_msg', 'txt_detail_av1', 'txt_detail_av2', 'txt_detail_av3',
                    'txt_detail_av4']:
            window[key].update('')

    def run(self) -> None:
        while True:
            event, values = window.read()

            if event in (None, 'exit'):
                break
            elif event == 'btn_load_data':
                self.reload_transaction_table()
            elif event == 'btn_load_from_file':
                # TODO
                pass
            elif event == 'tbl_transactions':
                if not values['tbl_transactions']:
                    self.clear_details()
                    continue
                lineSelected = values['tbl_transactions'][0]
                transactionSelected = self.transactions[lineSelected]
                transactionSelected.load_tags()
                self.show_details(transactionSelected)
                window['tbl_detail_tags'].update(values=[self.clsIdToName[tid] for tid in transactionSelected.tags])
            elif event == 'btn_remove_line':
                if not values['tbl_transactions']:
                    sg.popup('No transaction selected', title='Error')
                    continue
                if sg.popup_ok_cancel('This will remove the transaction permanently. You sure?', title='Careful!') != 'OK':
                    continue
                lineSelected = values['tbl_transactions'][0]
                transactionSelected = self.transactions[lineSelected]
                transactionSelected.delete()
                self.reload_transaction_table()
            elif event == 'btn_change_type':
                if not values['tbl_transactions']:
                    sg.popup('No transaction selected', title='Error')
                    continue
                lineSelected = values['tbl_transactions'][0]
                transactionSelected = self.transactions[lineSelected]

                trTypes = window['type_filter'].get_list_values()
                event, values = sg.Window('Choose new type', [
                    [sg.Listbox(values=trTypes, size=(20, 10), key='types')],
                    [sg.OK(), sg.Cancel()]
                ]).read(close=True)

                if event in ['Cancel', None] or len(values['types']) == 0:
                    continue

                newType = self.clsNameToId[values['types'][0]]

                transactionSelected.trType = newType
                if transactionSelected.status == TransactionStatus.SAVED:
                    transactionSelected.status = TransactionStatus.MODIFIED

                self.reload_transaction_table(reloadFromDB=False)

            elif event == 'btn_change_category':
                pass
            elif event == 'btn_add_tag':
                pass
            elif event == 'btn_remove_tag':
                pass
            elif event == 'btn_save_one':
                pass

if __name__ == '__main__':
    Application().run()
