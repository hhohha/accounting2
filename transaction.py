from __future__ import annotations
from typing import List, Optional, Set

from dataclasses import dataclass, field
import datetime

import dbif
from enums import TransactionStatus
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
    originalCurrency: Optional[str] = None          # hidden
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

    tags: Set[int] | str | None = field(default=None, repr=False)
    status: TransactionStatus = field(default=TransactionStatus.SAVED, repr=False)
    signature: str = field(default='', repr=False)

    def __post_init__(self):
        if not self.signature:
            self.signature = ','.join(map(lambda x: x if x is not None else '', [self.toAccount, self.toAccountName, self.variableSymbol, self.constantSymbol, self.specificSymbol,
                                       self.transactionIdentifier, self.systemDescription, self.senderDescription, self.addresseeDescription,
                                       self.AV1, self.AV2, self.AV3, self.AV4])).lower()
        if self.tags is None:
            self.tags = set()
        else:
            self.tags = {int(t) for t in self.tags.split(',')}

    def save(self) -> int:
        # TODO: transaction should always have: dueDate, amount, category, trType, bank
        if self.id is None:
            self.id = dbif.save_new_transaction(self)
        else:
            dbif.save_modified_transaction(self)

        assert self.id is not None, "transaction id is None after saving"
        assert isinstance(self.tags, set), "transaction tags are not a set"

        tagsIdsFromDB = list(map(lambda x: x[0], dbif.get_tags(self.id)))
        tagsToRemove = set(tagsIdsFromDB) - set(self.tags)
        if tagsToRemove:
            dbif.remove_tags(self.id, tagsToRemove)

        tagsToAdd = set(self.tags) - set(tagsIdsFromDB)
        if tagsToAdd:
            dbif.add_tags(self.id, tagsToAdd)

        return self.id

    #def load_tags(self) -> None:
    #    #self.tags = list(map(lambda x: x[0], dbif.get_tags(self.id)))
    #    assert self.id is not None, "cannot get tags from DB: transaction id not saved in DB"
    #    self.tags = list(map(lambda t: t[0], dbif.get_tags(self.id)))

    def find_classifications(self) -> None:
        self.find_tr_type()
        self.find_category()
        #self.find_tags()

    def find_tr_type(self) -> None:
        if self.amount > 0:
            self.trType = TR_TYPE_CREDIT
            return
        for trTypeId, signature in signatures.tr_types.items():
            if signature in self.signature:
                self.trType = trTypeId
                return

    def find_category(self) -> None:
        if self.amount > 0:
            self.trType = CATEGORY_CREDIT
            return
        for categoryId, signature in signatures.categories.items():
            if signature.lower() in self.signature:
                self.category = categoryId
                return

    def delete(self):
        dbif.remove_transaction(self.id)

#    def find_tags(self) -> None:
#        for tagId, signature in signatures.tags.items():
#            if signature.lower() in self.signature:
#                self.tags.append(Tag(tagId, signature))