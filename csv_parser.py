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
        fields = list(map(lambda l: l.strip('"'), line.split(self.delimiter)))
        if len(fields) < 19:
            logging.warning(f'Line {line} has only {len(fields)} fields, expected 19')
            return None
        try:
            return Transaction(
                id = None,
                dueDate = datetime.strptime(fields[0], '%d.%m.%Y').date(),
                writeOffDate = datetime.strptime(fields[1], '%d.%m.%Y').date() if fields[1] else None,
                toAccount = fields[2],
                toAccountName = fields[3],
                amount = int(fields[4].replace('.', '').replace(',', '')),
                originalAmount = int(fields[5].replace('.', '').replace(',', '')) if fields[5] else None,
                originalCurrency = fields[6],
                rate = float(fields[7].replace(',', '.')) if fields[6] else None,
                variableSymbol = fields[8],
                constantSymbol = fields[9],
                specificSymbol = fields[10],
                transactionIdentifier = fields[11],
                systemDescription = fields[12],
                senderDescription = fields[13],
                addresseeDescription = fields[14],
                AV1 = fields[15],
                AV2 = fields[16],
                AV3 = fields[17],
                AV4 = fields[18],
                bank = 'KB',
                status = TransactionStatus.NEW
            )
        except ValueError as e:
            logging.warning(f'Error parsing line {fields}: {e}')
            return None


    def line_to_transaction_mb(self, line: str) -> Transaction:
        pass

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
            if len(lines) >= 18 and lines[2] == '\n' and lines[16] == '\n':
                lines = lines[18:]
                parse_func = self.line_to_transaction_kb
            else:
                logging.warning(f'File seems to have an unexpected format')
                return
        elif self.sourceType == CsvType.MB:
            if len(lines) >= 37 and lines[35] == '\n' and lines[33] == '\n':
                lines = lines[37:]
                parse_func = self.line_to_transaction_mb
            else:
                logging.warning(f'File seems to have an unexpected format')
                return
        else:
            assert False, f'Unknown source type: {self.sourceType}'

        self.transactions = [t for t in map(parse_func, lines) if t is not None]
