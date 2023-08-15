import logging
from datetime import date

import PySimpleGUI as sg
from typing import Dict, List, Optional, Tuple, Any

import dbif
from enums import ClsType, TransactionStatus
from layout import window
from transaction import Transaction

class Application:
    def __init__(self):
        allClassifications = dbif.get_classifications()
        self.clsIdToName: Dict[Optional[int], str] = {c[0]: c[2] for c in allClassifications}
        self.clsIdToName[None] = 'unknown'

        self.clsNameToId: Dict[Tuple[ClsType, str], int] = {}
        for id, clsType, name in allClassifications:
            self.clsNameToId[(ClsType(clsType), name)] = id

        self.transactions: List[Transaction] = []
        self.window = window
        self.values: Any = None
        self.event: Any = None

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

    def recalculate_summaries(self) -> None:
        pass

    def reload_transaction_table(self, reloadFromDB: bool=True) -> None:
        # if a transaction is selected, remember that row to select it (or the previous one, if deleting) afterward
        lineSelected: Optional[int] = None
        if self.values['tbl_transactions']:
            lineSelected = self.values['tbl_transactions'][0]

        if reloadFromDB:
            self.transactions = [Transaction(*t) for t in dbif.get_transactions()]
        window['tbl_transactions'].update(values=[self.transaction_to_table_row(t) for t in self.transactions])

        self.recalculate_summaries()

        # now select the same (or neighboring) row as before
        if lineSelected is not None:
            if lineSelected >= len(self.transactions):
                lineSelected = len(self.transactions) - 1
            if lineSelected >= 0:
                window['tbl_transactions'].update(select_rows=[lineSelected])

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

    def change_transaction_classification(self, cls: ClsType) -> None:
        assert cls in [ClsType.TR_TYPE, ClsType.CATEGORY], 'Invalid classification type'

        if (transactionSelected := self.get_selected_transaction()) is None:
            sg.popup('No transaction selected', title='Error')
            return

        clsNames = window['type_filter' if cls == ClsType.TR_TYPE else 'cat_filter'].get_list_values()

        event, values = sg.Window(f'Choose new {"type" if cls == ClsType.TR_TYPE else "category"}', [
            [sg.Listbox(values=clsNames, size=(20, 10), key='cls')],
            [sg.OK(), sg.Cancel()]
        ]).read(close=True)

        if event in ['Cancel', None] or len(values['cls']) == 0:
            return

        typeId = values['cls'][0]
        newType = self.clsNameToId[(cls, typeId)]

        if cls == ClsType.TR_TYPE:
            transactionSelected.trType = newType
        else:
            transactionSelected.category = newType
        if transactionSelected.status == TransactionStatus.SAVED:
            transactionSelected.status = TransactionStatus.MODIFIED

        self.reload_transaction_table(reloadFromDB=False)

    def get_selected_transaction(self) -> Optional[Transaction]:
        if not self.values['tbl_transactions']:
            return None
        lineSelected = self.values['tbl_transactions'][0]
        return self.transactions[lineSelected]

    def run(self) -> None:
        while True:
            self.event, self.values = self.window.read()

            if self.event in (None, 'exit'):
                break
            elif self.event == 'btn_load_data':
                self.reload_transaction_table()
            elif self.event == 'btn_load_from_file':
                # TODO
                pass
            elif self.event == 'tbl_transactions':
                if (transactionSelected := self.get_selected_transaction()) is None:
                    self.clear_details()
                    continue

                transactionSelected.load_tags()
                self.show_details(transactionSelected)
                window['tbl_detail_tags'].update(values=[self.clsIdToName[tid] for tid in transactionSelected.tags])

            elif self.event == 'btn_remove_line':
                if (transactionSelected := self.get_selected_transaction()) is None:
                    sg.popup('No transaction selected', title='Error')
                    continue

                if sg.popup_ok_cancel('This will remove the transaction permanently. You sure?', title='Careful!') != 'OK':
                    continue

                transactionSelected.delete()
                self.reload_transaction_table()

            elif self.event == 'btn_change_type':
                self.change_transaction_classification(ClsType.TR_TYPE)

            elif self.event == 'btn_change_category':
                self.change_transaction_classification(ClsType.CATEGORY)

            elif self.event == 'btn_add_tag':
                pass
            elif self.event == 'btn_remove_tag':
                pass
            elif self.event == 'btn_save_one':
                if (transactionSelected := self.get_selected_transaction()) is None:
                    sg.popup('No transaction selected', title='Error')
                    continue
                transactionSelected.save()
                transactionSelected.status = TransactionStatus.SAVED
                self.reload_transaction_table(reloadFromDB=False)

            elif self.event == 'btn_hide_line':
                pass

if __name__ == '__main__':
    Application().run()
