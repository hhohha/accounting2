import logging
from datetime import datetime, date, timedelta

import PySimpleGUI as sg
from typing import Dict, List, Optional, Tuple, Any

import dbif
from backup import backup_db, restore_db
from csv_parser import CsvParser
from enums import ClsType, TransactionStatus, CsvType, Settings
from layout import window
from transaction import Transaction
from utils import display_amount


# TODOs
#   solve signatures reload when switching DBs or changing signatures    <<<<!!!
#   when adding tag, allow fulltext search
#   disable backup and restore for test DB
#   put sql_query into a try-except block
#   add a note field to transactions
#   on signature add/remove reload signatures
#   save all button
#   detect duplicates

class Application:
    def __init__(self):
        allClassifications = dbif.get_classifications()
        self.clsIdToName: Dict[Optional[int], str] = {c[0]: c[2] for c in allClassifications}
        self.clsIdToName[None] = 'unknown'

        self.signNameToId: Dict[str, int] = {}

        self.clsNameToId: Dict[Tuple[ClsType, str], int] = {}
        for id, clsType, name in allClassifications:
            self.clsNameToId[(ClsType(clsType), name)] = id

        self.csvParser = CsvParser()

        self.transactions: List[Transaction] = []
        self.window = window
        self.values: Any = None
        self.event: Any = None

        self.refresh_cls_filters()
        self.refresh_last_backup()

    def refresh_cls_filters(self):
        tr_types = list(map(lambda t: t[2], dbif.get_classifications(ClsType.TR_TYPE)))
        categories = list(map(lambda t: t[2], dbif.get_classifications(ClsType.CATEGORY)))
        tags = sorted(list(map(lambda t: t[2], dbif.get_classifications(ClsType.TAG))))

        self.window['filter_type'].update(values=tr_types)
        self.window['filter_category'].update(values=categories)
        self.window['filter_tags'].update(values=tags)

    def get_selected_cls_details(self) -> Optional[int]:
        if self.values['radio_sig_type'] and self.window['txt_detail_type'].get():
            return self.clsNameToId[(ClsType.TR_TYPE, self.window['txt_detail_type'].get())]
        elif self.values['radio_sig_cat'] and self.window['txt_detail_category'].get():
            return self.clsNameToId[(ClsType.CATEGORY, self.window['txt_detail_category'].get())]
        elif self.values['tbl_detail_tags']:
            lineNo = self.values['tbl_detail_tags'][0]
            tagName = self.window['tbl_detail_tags'].get()[lineNo][0]
            return self.clsNameToId[(ClsType.TAG, tagName)]
        else:
            sg.popup('No classification selected', title='Error')
            return None

    def refresh_last_backup(self) -> None:
        lastBkp = dbif.get_setting(Settings.LAST_BACKUP.value)
        textColor = 'white'
        if lastBkp is None:
            lastBkp = 'never'
            textColor = 'red'
        elif datetime.now() - datetime.strptime(lastBkp, '%Y-%m-%d') > timedelta(days=90):
            textColor = 'red'
        self.window['txt_last_backup'].update(lastBkp, text_color=textColor)

    def clear_filters(self) -> None:
        for key in ['filter_date_from', 'filter_date_to', 'filter_amount_min', 'filter_amount_max', 'filter_desc']:
            self.window[key].update('')
        for key in ['filter_type', 'filter_category', 'filter_tags']:
            self.window[key].set_value([])
        self.window['radio_filter_both'].update(True)
        self.window['radio_filter_bank_all'].update(True)

    def get_filters(self) -> Optional[str]:
        filters: List[str] = []

        if dateFrom := self.window['filter_date_from'].get():
            try:
                datetime.strptime(dateFrom, '%Y-%m-%d')
            except ValueError:
                sg.popup(f'Invalid date format in start date: {dateFrom}', title='Error')
                return None
            filters.append(f't.dueDate >= "{dateFrom}"')

        if dateTo := self.window['filter_date_to'].get():
            try:
                datetime.strptime(dateTo, '%Y-%m-%d')
            except ValueError:
                sg.popup(f'Invalid date format in end date: {dateTo}', title='Error')
                return None
            filters.append(f't.dueDate <= "{dateTo}"')

        if amountMin := self.values['filter_amount_min']:
            try:
                if int(amountMin) < 0:
                    raise ValueError
            except ValueError:
                sg.popup(f'Invalid minimum amount: {amountMin}', title='Error')
                return None
            filters.append(f'abs(t.amount) >= 100 * {amountMin}')

        if amountMax := self.values['filter_amount_max']:
            try:
                if int(amountMax) < 0:
                    raise ValueError
            except ValueError as e:
                sg.popup(f'Invalid maximum amount: {amountMax}', title='Error')
                return None
            filters.append(f'abs(t.amount) <= 100 * {amountMax}')

        if self.values['filter_desc']:
            filters.append(f't.signature like "%{self.values["filter_desc"]}%"')
        if self.values['radio_filter_cred']:
            filters.append(f't.amount >= 0')
        if self.values['radio_filter_deb']:
            filters.append(f't.amount < 0')

        if self.values['radio_filter_bank_kb']:
            filters.append(f't.bank = "kb"')
        if self.values['radio_filter_bank_mb']:
            filters.append(f't.bank = "mb"')

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

    def get_cls_name(self, clsId: Optional[int]) -> str:
        try:
            return self.clsIdToName[clsId]
        except KeyError:
            logging.error(f'DB inconsistent: unknown classification: {clsId}')
            return 'error'

    def transaction_to_table_row(self, transaction: Transaction) -> List[str | int | date | None]:
        trTypeName = self.get_cls_name(transaction.trType)
        categoryName = self.get_cls_name(transaction.category)
        description = ','.join(filter(lambda f: f is not None, [transaction.AV1, transaction.AV2, transaction.AV3, transaction.AV4])) # type: ignore
        if not description:
            description = ','.join(filter(lambda f: f is not None, [transaction.systemDescription, transaction.senderDescription, transaction.addresseeDescription])) # type: ignore

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
            filters = self.get_filters()
            if filters is None:
                return
            self.transactions = [Transaction(*t) for t in dbif.get_transactions(filters)]
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
        self.signNameToId = {x[2]: x[0] for x in dbif.get_signatures(clsId)}
        self.window['tbl_signatures'].update(values=[[item] for item in list(self.signNameToId.keys())])

    def refresh_tags_table(self, t: Transaction) -> None:
        self.window['tbl_detail_tags'].update(values=[[self.clsIdToName[tid]] for tid in t.tags])
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
            self.window['filter_tags'].update(values=sorted(list(map(lambda t: t[2], dbif.get_classifications(ClsType.TAG)))))
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

            #print(f'event: {self.event}\nvalues: {self.values}')

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
                tagName = window['tbl_detail_tags'].get()[lineNo][0]
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
                # select next line
                if (lineNo := self.get_selected_line_no()) is not None:
                    if lineNo + 1 < len(self.transactions):
                        self.window['tbl_transactions'].update(select_rows=[lineNo + 1])

            elif self.event == 'btn_hide_line':
                if (lineNo := self.get_selected_line_no()) is None:
                    sg.popup('No transaction selected', title='Error')
                    continue

                self.transactions.pop(lineNo)
                self.reload_transaction_table(reloadFromDB=False)
            elif self.event == 'btn_load_from_file':
                event, values = sg.Window('Get file', [
                    [sg.Text('Data file')],
                    [sg.Input(key='txt_csv_file'), sg.FileBrowse(initial_folder='/home/honza/projects/accounting2/data')],
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
                for t in self.transactions:
                    t.find_classifications()
                self.reload_transaction_table(reloadFromDB=False)

            elif self.event == 'radio_sig_type':
                transactionSelected = self.get_selected_transaction()
                if transactionSelected is None:
                    continue
                typeId = transactionSelected.trType
                if typeId is not None:
                    self.reload_signature_table(typeId)
                    # unselect tags
                    self.window['tbl_detail_tags'].update(select_rows=[])

            elif self.event == 'radio_sig_cat':
                transactionSelected = self.get_selected_transaction()
                if transactionSelected is None:
                    continue
                categoryId = transactionSelected.category
                if categoryId is not None:
                    self.reload_signature_table(categoryId)
                    # unselect tags
                    self.window['tbl_detail_tags'].update(select_rows=[])

            elif self.event == 'tbl_detail_tags':
                transactionSelected = self.get_selected_transaction()
                if transactionSelected is None:
                    continue
                if len(self.values['tbl_detail_tags']) == 0:
                    continue
                lineNo = self.values['tbl_detail_tags'][0]
                tagName = window['tbl_detail_tags'].get()[lineNo][0]
                tagId = self.clsNameToId[(ClsType.TAG, tagName)]

                self.window['radio_sig_cat'].reset_group()
                self.reload_signature_table(tagId)

            elif self.event == 'btn_add_sign':
                if not (clsId := self.get_selected_cls_details()):
                    continue

                if not (transactionSelected := self.get_selected_transaction()):
                    logging.warning('Suspicious... adding signature, but No transaction selected')
                    signatureHint = ''
                else:
                    signatureHint = transactionSelected.signature

                event, values = sg.Window('Add signature', [
                    [sg.Text('Signature')],
                    [sg.Input(signatureHint, key='txt_signature')],
                    [sg.OK(), sg.Cancel()]
                ]).read(close=True)

                if event in ['Cancel', None]:
                    continue

                signature = values['txt_signature']
                if len(signature) < 3:
                    sg.popup('Signature too short', title='Error')
                    continue

                dbif.add_new_signature(clsId, signature)
                self.reload_signature_table(clsId)
            elif self.event == 'btn_remove_sign':
                if not (clsId := self.get_selected_cls_details()):
                    continue

                if not self.values['tbl_signatures']:
                    sg.popup('No signature selected', title='Error')
                    continue
                lineNo = self.values['tbl_signatures'][0]
                sigName = self.window['tbl_signatures'].get()[lineNo][0]

                try:
                    sigId = self.signNameToId[sigName]
                except KeyError:
                    sg.popup('Invalid signature selected', title='Error')
                    continue
                dbif.remove_signature(sigId)
                self.reload_signature_table(clsId)
            elif self.event == 'btn_backup':
                retval = backup_db()
                if retval == 0:
                    dbif.set_setting(Settings.LAST_BACKUP.value, str(date.today()))
                    self.refresh_last_backup()
                    sg.popup('Backup successful', title='Success')
                else:
                    sg.popup(f'Backup failed with error code {retval}', title='Error')
            elif self.event == 'btn_restore':
                if sg.popup_ok_cancel('This will remove al data from the DB and replace them with the data from the backup. You sure?', title='Careful!') != 'OK':
                    continue

                event, values = sg.Window('Get file', [
                    [sg.Text('Backup file')],
                    [sg.Input(key='txt_csv_file'), sg.FileBrowse(initial_folder='/home/honza')],
                    [sg.OK(), sg.Cancel()]
                ]).read(close=True)

                if event in ['Cancel', None]:
                    continue
                if not values['txt_csv_file']:
                    sg.popup('No file selected', title='Error')
                    continue

                filename = values['txt_csv_file']
                retval = restore_db(filename)
                if retval == 0:
                    self.reload_transaction_table()
                    self.refresh_last_backup()
                    sg.popup('Restore successful', title='Success')
                else:
                    sg.popup(f'Restore failed with error code {retval}', title='Error')

            elif self.event == 'btn_filter_this_month':
                firstDayInMonth = date.today().replace(day=1)
                lastDayInMonth = (firstDayInMonth + timedelta(days=31)).replace(day=1) - timedelta(days=1)
                self.window['filter_date_from'].update(firstDayInMonth)
                self.window['filter_date_to'].update(lastDayInMonth)
                self.reload_transaction_table()

            elif self.event == 'btn_filter_prev_month':
                # if the filter_date_from and filter_date_to are not empty and from the same month, move them to the previous month
                if (dateFrom := self.window['filter_date_from'].get()) and (dateTo := self.window['filter_date_to'].get()):
                    dateFrom = datetime.strptime(dateFrom, '%Y-%m-%d').date()
                    dateTo = datetime.strptime(dateTo, '%Y-%m-%d').date()
                    if dateFrom.month == dateTo.month:
                        firstDayInMonth = dateFrom.replace(day=1)
                        lastDayInPrevMonth = firstDayInMonth - timedelta(days=1)
                        firstDayInPrevMonth = lastDayInPrevMonth.replace(day=1)
                        self.window['filter_date_from'].update(firstDayInPrevMonth)
                        self.window['filter_date_to'].update(lastDayInPrevMonth)
                        self.reload_transaction_table()

            elif self.event == 'btn_filter_next_month':
                # if the filter_date_from and filter_date_to are not empty and from the same month, move them to the next month
                if (dateFrom := self.window['filter_date_from'].get()) and (dateTo := self.window['filter_date_to'].get()):
                    dateFrom = datetime.strptime(dateFrom, '%Y-%m-%d').date()
                    dateTo = datetime.strptime(dateTo, '%Y-%m-%d').date()
                    if dateFrom.month == dateTo.month:
                        firstDayInMonth = dateFrom.replace(day=1)
                        firstDayInNextMonth = (firstDayInMonth + timedelta(days=31)).replace(day=1)
                        lastDayInNextMonth = (firstDayInNextMonth + timedelta(days=31)).replace(day=1) - timedelta(days=1)
                        self.window['filter_date_from'].update(firstDayInNextMonth)
                        self.window['filter_date_to'].update(lastDayInNextMonth)
                        self.reload_transaction_table()
            elif self.event == 'btn_clear_filters':
                self.clear_filters()

            elif self.event == 'radio_db_test':
                dbif.DB_NAME = dbif.DB_NAME_TEST
                self.transactions = []
                self.reload_transaction_table(reloadFromDB=False)
                self.__init__()

            elif self.event == 'radio_db_real':
                dbif.DB_NAME = dbif.DB_NAME_REAL
                self.transactions = []
                self.reload_transaction_table(reloadFromDB=False)
                self.__init__()

            elif self.event == 'btn_racalc_classes':
                if (transactionSelected := self.get_selected_transaction()) is None:
                    sg.popup('No transaction selected', title='Error')
                    continue
                print(f'transaction before: {transactionSelected}')
                transactionSelected.find_classifications()
                print(f'transaction after: {transactionSelected}')
                if transactionSelected.status == TransactionStatus.SAVED:
                    transactionSelected.status = TransactionStatus.MODIFIED

                self.reload_transaction_table(reloadFromDB=False)


if __name__ == '__main__':
    Application().run()
