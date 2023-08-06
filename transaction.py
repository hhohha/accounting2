from __future__ import annotations
from typing import List, Optional

from dataclasses import dataclass, field
import datetime

import dbif
from signatures import signatures


TR_TYPE_CREDIT = 5
CATEGORY_CREDIT = 6

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

    signature_data: str = ''
    tags: List[Tag] = field(default_factory=list)

    def __post_init__(self):
        self.signature_data = ','.join([self.toAccount, self.toAccountName, self.variableSymbol, self.constantSymbol, self.specificSymbol,
                                       self.transactionIdentifier, self.systemDescription, self.senderDescription, self.addresseeDescription,
                                       self.AV1, self.AV2, self.AV3, self.AV4]).lower()

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

    def find_classifications(self) -> None:
        self.find_tr_type()
        self.find_category()
        self.find_tags()

    def find_tr_type(self) -> None:
        if self.amount > 0:
            self.trType = TR_TYPE_CREDIT
            return
        for trTypeId, signature in signatures.tr_types.items():
            if signature in self.signature_data:
                self.trType = trTypeId
                return

    def find_category(self) -> None:
        if self.amount > 0:
            self.trType = CATEGORY_CREDIT
            return
        for categoryId, signature in signatures.categories.items():
            if signature.lower() in self.signature_data:
                self.category = categoryId
                return

    def find_tags(self) -> None:
        for tagId, signature in signatures.tags.items():
            if signature.lower() in self.signature_data:
                self.tags.append(Tag(tagId, signature))