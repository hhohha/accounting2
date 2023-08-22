import logging
from datetime import date

import PySimpleGUI as sg
from typing import Dict, List, Optional, Tuple, Any

import dbif
from csv_parser import CsvParser
from enums import ClsType, TransactionStatus, CsvType
from layout import window
from transaction import Transaction
from utils import display_amount


# TODOs
#   signatures in gui
#   signatures analysis
#   backup and restore
#   gui improvements
#   improve filters (credit/debit, clear filters, last month)

class Application:
    def __init__(self):
        allClassifications = dbif.get_classifications()
        self.clsIdToName: Dict[Optional[int], str] = {c[0]: c[2] for c in allClassifications}
        self.clsIdToName[None] = 'unknown'

        self.clsNameToId: Dict[Tuple[ClsType, str], int] = {}
        for id, clsType, name in allClassifications:
            self.clsNameToId[(ClsType(clsType), name)] = id

        self.csvParser = CsvParser()

        self.transactions: List[Transaction] = []
        self.window = window
        self.values: Any = None
        self.event: Any = None

    def get_filters(self) -> str:
        print(f'values: {self.values}')

        filters: List[str] = []

        if self.values['filter_date_from']:
            filters.append(f't.dueDate >= "{self.values["filter_date_from"]}"')
        if self.values['filter_date_to']:
            filters.append(f't.dueDate <= "{self.values["filter_date_to"]}"')
        if self.values['filter_amount_min']:
            filters.append(f't.amount >= {self.values["filter_amount_min"]}')
        if self.values['filter_amount_max']:
            filters.append(f't.amount <= {self.values["filter_amount_max"]}')
        if self.values['filter_desc']:
            filters.append(f't.signature like "%{self.values["filter_desc"]}%"')
        if self.values['filter_type']:
            idLst = list(map(lambda t: self.clsNameToId[ClsType.TR_TYPE, t], self.values["filter_type"]))
            filters.append(f't.trType in ({",".join(map(str, idLst))})')
        if self.values['filter_category']:
            idLst = list(map(lambda t: self.clsNameToId[ClsType.CATEGORY, t], self.values["filter_category"]))
            filters.append(f't.category in ({",".join(map(str, idLst))})')
        if self.values['filter_tags']:
            idLst = list(map(lambda t: self.clsNameToId[ClsType.TAG, t], self.values["filter_tags"]))
            filters.append(f'tl.cls_id in ({",".join(map(str, idLst))})')

        return f' where {" and ".join(filters)}' if filters else ''

    def get_cls_name(self, clsId: int) -> str:
        try:
            return self.clsIdToName[clsId]
        except KeyError:
            logging.error(f'DB inconsistent: unknown classification: {clsId}')
            return 'error'

    def transaction_to_table_row(self, transaction: Transaction) -> List[str | int | date | None]:
        trTypeName = self.get_cls_name(transaction.trType)
        categoryName = self.get_cls_name(transaction.category)
        description = ','.join(filter(lambda f: f is not None, [transaction.AV1, transaction.AV2, transaction.AV3, transaction.AV4])) # type: ignore

        return [transaction.id, transaction.dueDate, display_amount(transaction.amount), description, trTypeName, categoryName, transaction.status.value]

    def recalculate_summaries(self) -> None:
        sumDebit, sumCredit = 0, 0
        for t in self.transactions:
            if t.amount < 0:
                sumDebit += t.amount
            else:
                sumCredit += t.amount
        self.window['txt_total_debit'].update(display_amount(sumDebit))
        self.window['txt_total_credit'].update(display_amount(sumCredit))
        self.window['txt_total_amount'].update(display_amount(sumCredit + sumDebit))
        self.window['txt_total_cnt'].update(len(self.transactions))

    def reload_transaction_table(self, reloadFromDB: bool=True) -> None:
        # if a transaction is selected, remember that row to select it (or the previous one, if deleting) afterward
        lineSelected: Optional[int] = None
        if self.values['tbl_transactions']:
            lineSelected = self.values['tbl_transactions'][0]

        if reloadFromDB:
            self.transactions = [Transaction(*t) for t in dbif.get_transactions(self.get_filters())]
        self.window['tbl_transactions'].update(values=[self.transaction_to_table_row(t) for t in self.transactions])

        self.recalculate_summaries()

        # now select the same (or neighboring) row as before
        if lineSelected is not None:
            if lineSelected >= len(self.transactions):
                lineSelected = len(self.transactions) - 1
            if lineSelected >= 0:
                self.window['tbl_transactions'].update(select_rows=[lineSelected])

    def clear_signatures_table(self) -> None:
        self.window['tbl_signatures'].update(values=[])

    def reload_signature_table(self, clsId: int) -> None:
        self.window['tbl_signatures'].update(values=[name for _, _, name in dbif.get_signatures(clsId)])

    def refresh_tags_table(self, t: Transaction) -> None:
        self.window['tbl_detail_tags'].update(values=[self.clsIdToName[tid] for tid in t.tags])
        self.clear_signatures_table()

    def show_details(self, t: Transaction) -> None:
        self.clear_details()
        self.window['txt_detail_bank'].update(t.bank)
        self.window['txt_detail_acc_no'].update(t.toAccount)
        self.window['txt_detail_acc_name'].update(t.toAccountName)
        self.window['txt_detail_vs'].update(t.variableSymbol)
        self.window['txt_detail_cs'].update(t.constantSymbol)
        self.window['txt_detail_ss'].update(t.specificSymbol)
        self.window['txt_detail_desc'].update(t.systemDescription)
        self.window['txt_detail_sender_msg'].update(t.senderDescription)
        self.window['txt_detail_addressee_msg'].update(t.addresseeDescription)
        self.window['txt_detail_av1'].update(t.AV1)
        self.window['txt_detail_av2'].update(t.AV2)
        self.window['txt_detail_av3'].update(t.AV3)
        self.window['txt_detail_av4'].update(t.AV4)

        self.window['txt_detail_category'].update(self.get_cls_name(t.category))
        self.window['txt_detail_type'].update(self.get_cls_name(t.trType))

        self.refresh_tags_table(t)

        self.window['radio_sig_type'].reset_group()

    def clear_details(self) -> None:
        for key in ['txt_detail_bank', 'txt_detail_acc_no', 'txt_detail_acc_name', 'txt_detail_vs', 'txt_detail_cs', 'txt_detail_ss',
                    'txt_detail_desc', 'txt_detail_sender_msg', 'txt_detail_addressee_msg', 'txt_detail_av1', 'txt_detail_av2', 'txt_detail_av3',
                    'txt_detail_av4', 'txt_detail_category', 'txt_detail_type']:
            window[key].update('')
            self.window['tbl_detail_tags'].update(values=[])

    def change_transaction_classification(self, cls: ClsType) -> None:
        assert cls in [ClsType.TR_TYPE, ClsType.CATEGORY], 'Invalid classification type'

        if (transactionSelected := self.get_selected_transaction()) is None:
            sg.popup('No transaction selected', title='Error')
            return

        clsNames = window['filter_type' if cls == ClsType.TR_TYPE else 'filter_category'].get_list_values()

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

    def add_tag(self) -> None:
        if (transactionSelected := self.get_selected_transaction()) is None:
            sg.popup('No transaction selected', title='Error')
            return

        tags = self.window['filter_tags'].get_list_values()

        event, values = sg.Window('Choose new tag', [
            [sg.Text('Existing tags'), sg.Listbox(values=tags, size=(30, 30), key='existing_tag')],
            [sg.Text('Create a tag'), sg.Input(key='new_tag')],
            [sg.OK(), sg.Cancel()]
        ]).read(close=True)

        if event in ['Cancel', None]:
            return

        if values['new_tag']:
            tagValue = values['new_tag']
            tagId = dbif.add_new_classification(ClsType.TAG, tagValue)
            self.clsIdToName[tagId] = tagValue
            self.clsNameToId[(ClsType.TAG, tagValue)] = tagId
            self.window['filter_tags'].update(values=list(map(lambda t: t[2], dbif.get_classifications(ClsType.TAG))))
        elif len(values['existing_tag']) > 0:
            tagValue = values['existing_tag'][0]
            tagId = self.clsNameToId[(ClsType.TAG, tagValue)]
        else:
            return

        transactionSelected.tags.add(tagId)
        if transactionSelected.status == TransactionStatus.SAVED:
            transactionSelected.status = TransactionStatus.MODIFIED
        self.reload_transaction_table(reloadFromDB=False)

    def get_selected_transaction(self) -> Optional[Transaction]:
        if not self.values['tbl_transactions']:
            return None
        lineNo = self.values['tbl_transactions'][0]
        return self.transactions[lineNo]

    def get_selected_line_no(self) -> Optional[int]:
        if not self.values['tbl_transactions']:
            return None
        return self.values['tbl_transactions'][0]

    def run(self) -> None:
        while True:
            self.event, self.values = self.window.read()

            if self.event in (None, 'exit'):
                break
            elif self.event == 'btn_load_data':
                self.reload_transaction_table()
            elif self.event == 'tbl_transactions':
                if (transactionSelected := self.get_selected_transaction()) is None:
                    self.clear_details()
                    continue

                self.show_details(transactionSelected)

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
                self.add_tag()

            elif self.event == 'btn_remove_tag':
                if (transactionSelected := self.get_selected_transaction()) is None:
                    sg.popup('No transaction selected', title='Error')
                    continue

                if len(self.values['tbl_detail_tags']) == 0:
                    sg.popup('No tag selected', title='Error')
                    continue

                lineNo = self.values['tbl_detail_tags'][0]
                tagName = window['tbl_detail_tags'].get()[lineNo]
                tagId = self.clsNameToId[(ClsType.TAG, tagName)]

                assert isinstance(transactionSelected.tags, set), "transaction tags are in a wrong format"
                transactionSelected.tags.remove(tagId)

                if transactionSelected.status == TransactionStatus.SAVED:
                    transactionSelected.status = TransactionStatus.MODIFIED
                self.reload_transaction_table(reloadFromDB=False)

            elif self.event == 'btn_save_one':
                if (transactionSelected := self.get_selected_transaction()) is None:
                    sg.popup('No transaction selected', title='Error')
                    continue
                transactionSelected.save()
                transactionSelected.status = TransactionStatus.SAVED
                self.reload_transaction_table(reloadFromDB=False)

            elif self.event == 'btn_hide_line':
                if (lineNo := self.get_selected_line_no()) is None:
                    sg.popup('No transaction selected', title='Error')
                    continue

                self.transactions.pop(lineNo)
                self.reload_transaction_table(reloadFromDB=False)
            elif self.event == 'btn_load_from_file':
                event, values = sg.Window('Get file', [
                    [sg.Text('Data file')],
                    [sg.Input(key='txt_csv_file'), sg.FileBrowse(initial_folder='/home/honza')],
                    [sg.Text('Source')],
                    [sg.Listbox(values=['kb', 'mb'], size=(30, 3), key='lst_source_type')], [sg.OK(), sg.Cancel()]
                ]).read(close=True)

                if event in ['Cancel', None]:
                    continue
                if not values['txt_csv_file']:
                    sg.popup('No file selected', title='Error')
                    continue
                if not values['lst_source_type']:
                    sg.popup('No source selected', title='Error')
                    continue

                filename = values['txt_csv_file']
                sourceType = CsvType(values['lst_source_type'][0])
                self.transactions = self.csvParser.read_transactions(filename, sourceType)
                self.reload_transaction_table(reloadFromDB=False)

            elif self.event == 'radio_sig_type':
                transactionSelected = self.get_selected_transaction()
                if transactionSelected is None:
                    continue
                typeId = transactionSelected.trType
                self.reload_signature_table(typeId)

            elif self.event == 'radio_sig_cat':
                transactionSelected = self.get_selected_transaction()
                if transactionSelected is None:
                    continue
                categoryId = transactionSelected.category
                self.reload_signature_table(categoryId)

            elif self.event == 'tbl_detail_tags':
                transactionSelected = self.get_selected_transaction()
                if transactionSelected is None:
                    continue
                if len(self.values['tbl_detail_tags']) == 0:
                    continue
                lineNo = self.values['tbl_detail_tags'][0]
                tagName = window['tbl_detail_tags'].get()[lineNo]
                tagId = self.clsNameToId[(ClsType.TAG, tagName)]

                self.reload_signature_table(tagId)

if __name__ == '__main__':
    Application().run()
