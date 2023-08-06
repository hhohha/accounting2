import PySimpleGUI as sg

import dbif
from enums import ClsType

def get_main_window_layout():
    tr_types = list(map(lambda t: str(t[0]) + ' ' + t[1], dbif.get_all_classifications(ClsType.TR_TYPE)))
    categories = list(map(lambda t: str(t[0]) + ' ' + t[1], dbif.get_all_classifications(ClsType.CATEGORY)))
    tags = list(map(lambda t: str(t[0]) + ' ' + t[1], dbif.get_all_classifications(ClsType.TAG)))

    filter_frame = sg.Frame(layout=[[sg.Text('Date from:'), sg.Input(key='date_from'), sg.Text('Date to:'), sg.Input(key='date_to'),
        sg.Text('       Amount min:'), sg.Input(key='amount_min'), sg.Text('Amount max:'), sg.Input(key='amount_max'),
        sg.Text('       Description:'), sg.Input(key='desc')],
        [sg.Text()],
        [sg.Text('Type:'), sg.Listbox(values=tr_types, key='type_filter', size=(25,10), select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED),
         sg.Text('      Category:'), sg.Listbox(values=categories, key='cat_filter', size=(25,10), select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED),
         sg.Text('      Tag:'), sg.Listbox(values=tags, key='tag_filter', size=(25,10), select_mode=sg.LISTBOX_SELECT_MODE_EXTENDED)
        ],
        [sg.Button('Clear filters')]
    ], title='Filters')

    frame_tags = sg.Frame(layout=[
        [sg.Table(values=[[]], key='tag_table', headings=['id', 'tags'], auto_size_columns=False, num_rows=15, col_widths=[5, 25], enable_events = True)],
        [sg.Button('Remove tag'), sg.Button('Add tag')],
        [sg.Text()]
    ], title='Tags')

    frame_cat = sg.Frame(layout=[
        [sg.Radio('Category strings', 'grp_cls', enable_events=True, key='radio_str_cat')],
        [sg.Input(size=(33,None), disabled=True, key='category')]
    ], title='Category')

    frame_type = sg.Frame(layout=[
        [sg.Radio('Type strings', 'grp_cls', enable_events=True, key='radio_str_type')],
        [sg.Input(size=(33,None), disabled=True, key='type')]
    ], title='Type')

    summary_frame = sg.Frame(layout=[
        [sg.Text('Total plus:'), sg.Text('                         ', key='txt_total_plus')],
        [sg.Text('Total minus:'), sg.Text('                         ', key='txt_total_minus')],
        [sg.Text('Total amount:'), sg.Text('                         ', key='txt_total')],
        [sg.Text('Total count:'), sg.Text('                         ', key='txt_cnt')]
    ], title='Summary')

    date_frame = sg.Frame(layout=[
        [sg.Text('Last kb:'), sg.Text('                         ', key='txt_last_kb')],
        [sg.Text('Last mb:'), sg.Text('                         ', key='txt_last_mb')],
    ], title='Last transactions')

    layout = [[
            sg.Table(values=[[]], key='main_table', headings=['id', 'date', 'amount', 'message', 'type', 'category', 'status'], auto_size_columns=False, num_rows=65, col_widths=[5, 12, 10, 100, 20, 20, 10], enable_events = True),
            sg.Frame(layout=[
                [frame_tags],
                [sg.Text(), sg.Text()],
                [frame_cat],
                [sg.Text(), sg.Text()],
                [frame_type],
                [sg.Text(), sg.Text()],
                [sg.Text('Strings')],
                [sg.Table(values=[[]], key='str_table', headings=['id', 'string'], auto_size_columns=False, num_rows=24, col_widths=[5, 25])],
                [sg.Button('Add string'), sg.Button('Remove string')]
            ], title='Classification')
        ],
        [sg.Button('Save all'), sg.Button('Save one'), sg.Text('          '), sg.Button('Change type'), sg.Button('Change category')],
        [sg.Button('LOAD DATA', key='load_all'), sg.Button('Load from file', key='load_from_file'), sg.Button('Hide line', key='hide_line'), sg.Button('Remove line from DB', key='remove_line')],
        [sg.Text()],
        [filter_frame, sg.Text('     '), summary_frame, date_frame]
    ]

    transactionsTable = sg.Table(values = [[]], key='table_transactions', headings=['id', 'date', 'amount', 'message', 'type', 'category', 'status'],
                                 auto_size_columns=False, num_rows=65, col_widths=[5, 12, 10, 100, 20, 20, 10], enable_events = True)
    frameTransactions = sg.Frame(layout=[[transactionsTable]], title='Transactions')


    frameDetails = sg.Frame(layout=[[frameTransactionData], [frameTags], [frameCategory], [frameTrType], [frameSignatures]], title='Details')
    frameButtons = sg.Frame(layout=[], title='Buttons')
    frameFilter = sg.Frame(layout=[], title='Filter')
    frameSummary = sg.Frame(layout=[], title='Summary')

    layout = [
        [frameTransactions, frameDetails],
        [frameButtons, frameFilter, frameSummary]
    ]

    return layout


def main():
    layout = get_main_window_layout()
    window = sg.Window('Welcome to accounting', layout, default_element_size=(12, 1), element_padding=(1, 1), return_keyboard_events=True,
                       resizable=False)

    # window.cls_transl = dbif.get_cls_transl()
    # window.cls_transl[None] = 'unknown'
    transactions = {}
    tr_data = []

    while True:
        event, values = window.read()

        if event in (None, 'exit'):
            break

if __name__ == '__main__':
    main()
