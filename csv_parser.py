import logging
from datetime import datetime
from typing import Optional, List

from enums import CsvType, TransactionStatus
from transaction import Transaction


class CsvParser:
    def __init__(self):
        self.delimiter: str = ';'
        self.sourceType: Optional[CsvType] = None
        self.transactions: List[Transaction] = []

    def line_to_transaction_mb(self, line: str) -> Optional[Transaction]:
        fields = list(map(lambda l: l.strip('"'), line.split(self.delimiter)))
        if len(fields) < 11:
            logging.warning(f'Line {line} has only {len(fields)} fields, expected 11')
            return None
        try:
            return Transaction(
                id = None,
                dueDate = datetime.strptime(fields[0], '%d-%m-%Y').date(),
                writeOffDate = datetime.strptime(fields[1], '%d-%m-%Y').date() if fields[1] else None,
                senderDescription = fields[2],
                addresseeDescription = fields[3],
                toAccountName=fields[4],
                toAccount=fields[5],
                constantSymbol=fields[6],
                variableSymbol=fields[7],
                specificSymbol=fields[8],
                amount=int(fields[9].replace('.', '').replace(',', '').replace(' ', '')),
                bank='MB',
                status=TransactionStatus.NEW
            )
        except ValueError as e:
            logging.warning(f'Line {line} cannot be parsed: {e}')
            return None

    def line_to_transaction_kb(self, line: str) -> Optional[Transaction]:
        def parse_amount(amount_str: str) -> int:
            s = amount_str.strip().replace(',', '.')
            return int(round(float(s) * 100))

        fields = list(map(lambda l: l.strip('"'), line.split(self.delimiter)))
        if len(fields) < 19:
            logging.warning(f'Line {line} has only {len(fields)} fields, expected 19')
            return None
        try:
            return Transaction(
                id = None,
                dueDate = datetime.strptime(fields[1], '%d.%m.%Y').date(),
                writeOffDate = datetime.strptime(fields[0], '%d.%m.%Y').date() if fields[0] else None,
                toAccount = fields[2],
                toAccountName = fields[3],
                amount = parse_amount(fields[4]),
                originalAmount =  parse_amount(fields[6]) if fields[6] else None,
                originalCurrency = fields[7],
                rate = float(fields[8].replace(',', '.')) if fields[8] else None,
                variableSymbol = fields[9],
                constantSymbol = fields[10],
                specificSymbol = fields[11],
                transactionIdentifier = fields[12],
                systemDescription = fields[13],
                senderDescription = fields[14],
                addresseeDescription = None,
                AV1 = fields[15],
                AV2 = None,
                AV3 = None,
                AV4 = None,
                bank = 'KB',
                status = TransactionStatus.NEW
            )
        except ValueError as e:
            logging.warning(f'Error parsing line {fields}: {e}')
            return None

    def read_transactions(self, filename: str, sourceType: CsvType) -> List[Transaction]:
        self.sourceType = sourceType
        self.transactions.clear()
        try:
            with open(filename, 'r', encoding='cp1250') as f:
                lines = f.readlines()
                self.parse_data(lines)
                return self.transactions
        except FileNotFoundError:
            print(f'File {filename} not found')
        return []

    def parse_data(self, lines: List[str]) -> None:
        if self.sourceType == CsvType.KB:
            parse_func = self.line_to_transaction_kb
        elif self.sourceType == CsvType.MB:
            parse_func = self.line_to_transaction_mb
        else:
            assert False, f'Unknown source type: {self.sourceType}'

        self.transactions = [t for t in map(parse_func, lines) if t is not None]
