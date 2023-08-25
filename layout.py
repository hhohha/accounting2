import PySimpleGUI as sg

import dbif
from enums import ClsType


def get_main_window_layout():
    tr_types = list(map(lambda t: t[2], dbif.get_classifications(ClsType.TR_TYPE)))
    categories = list(map(lambda t: t[2], dbif.get_classifications(ClsType.CATEGORY)))
    tags = list(map(lambda t: t[2], dbif.get_classifications(ClsType.TAG)))

    ##### main table frame ####################################################
    transactionsTable = sg.Table(values = [[]], key='tbl_transactions', headings=['id', 'date', 'amount', 'message', 'type', 'category', 'status'],
                                 auto_size_columns=False, num_rows=65, col_widths=[5, 12, 10, 100, 20, 20, 10], enable_events = True)
    frameTransactionTable = sg.Frame(layout=[[transactionsTable]], title='Transactions')

    ##### details frame #######################################################
    frameTransactionDetails = sg.Frame(layout=[
        [sg.Text('Bank: '), sg.Text('', key='txt_detail_bank')],
        [sg.Text('Account number: '), sg.Text('', key='txt_detail_acc_no')],
        [sg.Text('Account name: '), sg.Text('', key='txt_detail_acc_name')],
        [sg.Text('VS: '), sg.Text('', key='txt_detail_vs')],
        [sg.Text('CS: '), sg.Text('', key='txt_detail_cs')],
        [sg.Text('SS: '), sg.Text('', key='txt_detail_ss')],
        [sg.Text('Description: '), sg.Text('', key='txt_detail_desc')],
        [sg.Text('Sender msg: '), sg.Text('', key='txt_detail_sender_msg')],
        [sg.Text('Addressee msg: '), sg.Text('', key='txt_detail_addressee_msg')],
        [sg.Text('', key='txt_detail_av1')],
        [sg.Text('', key='txt_detail_av2')],
        [sg.Text('', key='txt_detail_av3')],
        [sg.Text('', key='txt_detail_av4')]
    ], title='Transaction details')

    frameTags = sg.Frame(layout=[
        [sg.Table(values=[[]], key='tbl_detail_tags', headings=['tags'], auto_size_columns=False, num_rows=5, col_widths=[25], enable_events=True)],
        [sg.Button('Remove tag', key='btn_remove_tag'), sg.Button('Add tag', key='btn_add_tag')],
    ], title='Tags')

    frameCategory = sg.Frame(layout=[
        [sg.Radio('Category signatures', 'grp_cls', enable_events=True, key='radio_sig_cat')],
        [sg.Text('', key='txt_detail_category')]
    ], title='Category')

    frameTrType = sg.Frame(layout=[
        [sg.Radio('Type signatures', 'grp_cls', enable_events=True, key='radio_sig_type')],
        [sg.Text('', key='txt_detail_type')]
    ], title='Type')

    frameSignatures = sg.Frame(layout=[
        [sg.Table(values=[[]], key='tbl_signatures', headings=['signature'], auto_size_columns=False, num_rows=10, col_widths=[25])],
        [sg.Button('Add signature', key='btn_add_sign'), sg.Button('Remove signature', key='btn_remove_sign')]
    ], title='Signatures')

    frameDetails = sg.Frame(layout=[[frameTransactionDetails], [frameTags], [frameCategory], [frameTrType], [frameSignatures]], title='Details')

    ##### buttons frame #######################################################
    frameButtons = sg.Frame(layout=[
        [sg.Button('Save all', key='btn_save_all'), sg.Button('Save one', key='btn_save_one')],
        [sg.Button('Change type', key='btn_change_type'), sg.Button('Change category', key='btn_change_category')],
        [sg.Button('Load data', key='btn_load_data'), sg.Button('Load from file', key='btn_load_from_file')],
        [sg.Button('Hide line', key='btn_hide_line'), sg.Button('Remove line from DB', key='btn_remove_line')],
        [sg.Button('Backup DB', key='btn_backup'), sg.Button('Restore DB', key='btn_restore')]
    ], title='Buttons')

    ##### filter frame ########################################################
    frameFilter = sg.Frame(layout=[
        [
            sg.Text('Date from:'), sg.Input(key='filter_date_from'),
            sg.Text('Date to:'), sg.Input(key='filter_date_to'),
            sg.Text('Amount min:'), sg.Input(key='filter_amount_min'),
            sg.Text('Amount max:'), sg.Input(key='filter_amount_max'),
            sg.Text('Description:'), sg.Input(key='filter_desc')
        ],
        [
            sg.Text('Type:'), sg.Listbox(values=tr_types, key='filter_type', size=(25,10), select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED),
            sg.Text('Category:'), sg.Listbox(values=categories, key='filter_category', size=(25,10), select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED),
            sg.Text('Tag:'), sg.Listbox(values=tags, key='filter_tags', size=(25,10), select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED)
        ],
        [sg.Button('Clear filters', key='btn_clear_filters')]
    ], title='Filters')

    ##### summary frame #######################################################
    frameSummary = sg.Frame(layout=[
        [sg.Text('Total credit:'), sg.Text('', key='txt_total_credit')],
        [sg.Text('Total debit:'), sg.Text('', key='txt_total_debit')],
        [sg.Text('Total amount:'), sg.Text('', key='txt_total_amount')],
        [sg.Text('Transaction count:'), sg.Text('', key='txt_total_cnt')],
        [sg.Text('Last backup:'), sg.Text('', key='txt_last_backup')]
    ], title='Summary')

    layout = [
        [frameTransactionTable, frameDetails],
        [frameButtons, frameFilter, frameSummary]
    ]

    return layout

layout = get_main_window_layout()
window = sg.Window('Welcome to accounting', layout, default_element_size=(12, 1), element_padding=(1, 1), return_keyboard_events=True,
                       resizable=False, finalize=True)