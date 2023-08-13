from __future__ import annotations
from typing import List, Optional

from dataclasses import dataclass, field
import datetime

import dbif
from signatures import signatures
from utils import valueIfPresent

TR_TYPE_CREDIT = 5
CATEGORY_CREDIT = 6

@dataclass
class Tag:
    id: int
    name: str

@dataclass
class Transaction:
    id: Optional[int]           # in table
    dueDate: datetime.date      # in table
    amount: int                 # in table
    bank: str                   # in details

    # these may not be present for construction, but must be present for saving
    category: Optional[int] = None  # in table
    trType: Optional[int] = None    # in table

    # optionals
    writeOffDate: Optional[datetime.date] = None    # hidden
    toAccount: Optional[str] = None                 # in details
    toAccountName: Optional[str] = None             # in details
    originalAmount: Optional[int] = None            # hidden
    currency: Optional[str] = None                  # hidden
    rate:  Optional[float] = None                   # hidden
    variableSymbol: Optional[str] = None            # in details
    constantSymbol: Optional[str] = None            # in details
    specificSymbol: Optional[str] = None            # in details
    transactionIdentifier: Optional[str] = None     # hidden
    systemDescription: Optional[str] = None         # in details
    senderDescription: Optional[str] = None         # in details
    addresseeDescription: Optional[str] = None      # in details
    AV1: Optional[str] = None                       # in details
    AV2: Optional[str] = None                       # in details
    AV3: Optional[str] = None                       # in details
    AV4: Optional[str] = None                       # in details

    signature_data: str = field(init=False, repr=False)
    tags: List[int] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self):
        self.signature_data = ','.join(map(lambda x: x if x is not None else '', [self.toAccount, self.toAccountName, self.variableSymbol, self.constantSymbol, self.specificSymbol,
                                       self.transactionIdentifier, self.systemDescription, self.senderDescription, self.addresseeDescription,
                                       self.AV1, self.AV2, self.AV3, self.AV4])).lower()

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

    def load_tags(self) -> None:
        self.tags = list(map(lambda x: x[0], dbif.get_tags(self.id)))

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

#    def find_tags(self) -> None:
#        for tagId, signature in signatures.tags.items():
#            if signature.lower() in self.signature_data:
#                self.tags.append(Tag(tagId, signature))