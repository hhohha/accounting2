import PySimpleGUI as sg
from PySimpleGUI import RELIEF_RAISED, RELIEF_RIDGE, VerticalSeparator, HorizontalSeparator

import dbif
from enums import ClsType


def get_main_window_layout():
    tr_types = list(map(lambda t: t[2], dbif.get_classifications(ClsType.TR_TYPE)))
    categories = list(map(lambda t: t[2], dbif.get_classifications(ClsType.CATEGORY)))
    tags = list(map(lambda t: t[2], dbif.get_classifications(ClsType.TAG)))

    ##### main table frame ####################################################
    transactionsTable = sg.Table(values = [[]], key='tbl_transactions', headings=['id', 'date', 'amount', 'message', 'type', 'category', 'status'],
                                 auto_size_columns=False, num_rows=65, col_widths=[5, 12, 10, 100, 20, 20, 10], enable_events = True)

    frameButtons = sg.Frame(layout=[
        [sg.Button('Save one', key='btn_save_one', p=((0, 20), (0, 0))),
         sg.Button('Change type', key='btn_change_type', p=((0, 20), (0, 0))),
         sg.Button('Change category', key='btn_change_category', p=((0, 20), (0, 0))),
         sg.Button('Hide line', key='btn_hide_line', p=((0, 20), (0, 0))),
         sg.Button('Remove line from DB', key='btn_remove_line', p=((0, 20), (0, 0))),
         sg.Button('Load from file', key='btn_load_from_file', p=((0, 130), (0, 0))),

         sg.Text('Total credit:'), sg.Text('', key='txt_total_credit', p=((0, 25), (0, 0))),
         sg.Text('Total debit:'), sg.Text('', key='txt_total_debit', p=((0, 25), (0, 0))),
         sg.Text('Total amount:'), sg.Text('', key='txt_total_amount', p=((0, 25), (0, 0))),
         sg.Text('Transaction count:'), sg.Text('', key='txt_total_cnt')
        ]
    ], title='',expand_x=True)

    frameTransactionTable = sg.Frame(layout=[[transactionsTable], [frameButtons]], title='Transactions')

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

    sep = sg.HorizontalSeparator()

    frameSignatures = sg.Frame(layout=[
        [sg.Table(values=[[]], key='tbl_signatures', headings=['signature'], auto_size_columns=False, num_rows=10, col_widths=[25])],
        [sg.Button('Add signature', key='btn_add_sign'), sg.Button('Remove signature', key='btn_remove_sign')]
    ], title='Signatures')

    frameDetails = sg.Frame(layout=[[frameTransactionDetails], [frameTags], [frameCategory], [frameTrType], [sep], [frameSignatures]], title='', pad=10, border_width=5, expand_x=True, expand_y=True)

    ##### filter frame ########################################################
    frameFilter = sg.Frame(layout=[
        [
            sg.Text('Date from:', p=((0, 0), (10, 0))), sg.Input(key='filter_date_from', p=((0, 0), (10, 0))),
            sg.Text('Date to:', p=((0, 0), (10, 0))), sg.Input(key='filter_date_to', p=((0, 0), (10, 0))),
            sg.Text('Amount min:', p=((0, 0), (10, 0))), sg.Input(key='filter_amount_min', p=((0, 0), (10, 0))),
            sg.Text('Amount max:', p=((0, 0), (10, 0))), sg.Input(key='filter_amount_max', p=((0, 0), (10, 0))),
            sg.Text('Description:', p=((0, 0), (10, 0))), sg.Input(key='filter_desc', p=((0, 0), (10, 0)))
        ],
        [HorizontalSeparator(p=((0, 0), (10, 10)))],
        [
            sg.Radio('Only credit', 'filter_credit_debit', key='radio_filter_cred'),
            sg.Radio('Only debit', 'filter_credit_debit', key='radio_filter_deb'),
            sg.Radio('Both', 'filter_credit_debit', key='radio_filter_both', default=True)
        ],
        [HorizontalSeparator(p=((0, 0), (10, 10)))],
        [
            sg.Text('Type:'), sg.Listbox(values=tr_types, key='filter_type', size=(25,10), select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED),
            sg.Text('Category:'), sg.Listbox(values=categories, key='filter_category', size=(25,10), select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED),
            sg.Text('Tag:'), sg.Listbox(values=tags, key='filter_tags', size=(25,10), select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED)
        ],
        [HorizontalSeparator(p=((0, 0), (10, 10)))],
        [
            sg.Button('Load data', key='btn_load_data', p= ((10, 50), (10, 10))),
            sg.Button('<', key='btn_filter_prev_month'),
            sg.Button('This month', key='btn_filter_this_month'),
            sg.Button('>', key='btn_filter_next_month', p= ((10, 50), (10, 10))),
            sg.Button('Clear filters', key='btn_clear_filters'),
        ]
    ], title='Filters', p=((0, 0), (20, 0)))

    ##### backup frame #######################################################
    frameBkp = sg.Frame(layout=[
        [sg.Button('Backup DB', key='btn_backup'), sg.Button('Restore DB', key='btn_restore')],
        [sg.Text('Last backup:'), sg.Text('', key='txt_last_backup', p = ((0, 0), (5, 0)))]
    ], title='Backup', p=((100, 0), (290, 0)))

    return [
        [frameTransactionTable, frameDetails],
        [frameFilter, frameBkp]
    ]

layout = get_main_window_layout()
window = sg.Window('Welcome to accounting', layout, default_element_size=(12, 1), element_padding=(1, 1), return_keyboard_events=True,
                   resizable=False, finalize=True).finalize()