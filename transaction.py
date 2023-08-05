from __future__ import annotations
from typing import List, Optional

from dataclasses import dataclass, field
import datetime

import dbif

@dataclass
class Tag:
    id: int
    name: str

@dataclass
class Transaction:
    id: Optional[int]
    dueDate: datetime.date
    amount: int
    bank: str

    # these may not be present for construction, but must be present for saving
    category: Optional[int] = None
    trType: Optional[int] = None

    # optionals
    writeOffDate: Optional[datetime.date] = None
    toAccount: Optional[str] = None
    toAccountName: Optional[str] = None
    currency: Optional[str] = None
    rate:  Optional[float] = None
    variableSymbol: Optional[str] = None
    constantSymbol: Optional[str] = None
    specificSymbol: Optional[str] = None
    transactionIdentifier: Optional[str] = None
    systemDescription: Optional[str] = None
    senderDescription: Optional[str] = None
    addresseeDescription: Optional[str] = None
    AV1: Optional[str] = None
    AV2: Optional[str] = None
    AV3: Optional[str] = None
    AV4: Optional[str] = None

    tags: List[Tag] = field(default_factory=list)

    def save(self) -> int:
        # TODO: transaction should always have: dueDate, amount, category, trType, bank
        if self.id is None:
            self.id = dbif.save_new_transaction(self)
        else:
            dbif.save_modified_transaction(self)
        assert self.id is not None, "transaction id is None after saving"

        tagIds = map(lambda x: x.id, self.tags)
        tagsIdsFromDB = map(lambda x: x[0], dbif.get_tags(self.id))

        dbif.remove_tags(self.id, set(tagsIdsFromDB) - set(tagIds))
        dbif.add_tags(self.id, set(tagIds) - set(tagsIdsFromDB))

        return self.id

    @staticmethod
    def load_from_DB(id: int) -> Transaction:
        # TODO: this really needs testing
        t = Transaction(*dbif.get_transactions(f'where t.id = {id}')[0])
        return t
