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

    def line_to_transaction_kb(self, line: str) -> Optional[Transaction]:
        fields = list(map(lambda l: l.strip('"'), line.split(self.delimiter)))
        if len(fields) < 19:
            logging.warning(f'Line {line} has only {len(fields)} fields, expected 16')
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
                category = None,
                trType = None,
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
                rawData = f.read()
                self.parse_data(rawData)
                return self.transactions
        except FileNotFoundError:
            print(f'File {filename} not found')
        return []

    def parse_data(self, rawData: str) -> None:
        lines = rawData.split('\n')

        if self.sourceType == CsvType.KB:
            parse_func = self.line_to_transaction_kb
        elif self.sourceType == CsvType.MB:
            parse_func = self.line_to_transaction_mb
        else:
            assert False, f'Unknown source type: {self.sourceType}'

        self.transactions = [t for t in map(parse_func, lines[1:]) if t is not None]

