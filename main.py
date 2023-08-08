from layout import window


def main():


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
