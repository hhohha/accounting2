from __future__ import annotations
from typing import Optional, Set

from dataclasses import dataclass, field, InitVar
import datetime

import dbif
from enums import TransactionStatus
from signatures import signatures
from utils import remove_extra_spaces

TR_TYPE_CREDIT = 5
CATEGORY_CREDIT = 16

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
    initTags: InitVar[Optional[str]] = None         # tags are passed as str, but need to be converted to set in __post_init__

    tags: Set[int] = field(init=False, repr=False)
    status: TransactionStatus = field(default=TransactionStatus.SAVED, repr=False)
    signature: str = field(default='', init=False, repr=False)

    def __post_init__(self, initTags: str | None):

        print(f'initTags: {initTags}')
        for fieldName in ['systemDescription', 'senderDescription', 'addresseeDescription', 'AV1', 'AV2', 'AV3', 'AV4']:
            fld = getattr(self, fieldName)
            if fld is not None:
                newField = remove_extra_spaces(fld).strip()
                setattr(self, fieldName, newField if newField else None)

        if not self.signature:
            self.signature = self.make_signature()
        if initTags is None:
            self.tags = set()
        else:
            self.tags = {int(t) for t in initTags.split(',')}

    def make_signature(self) -> str:
        nonEmptyFields: filter[str] = filter(None, [self.toAccount, self.toAccountName, self.variableSymbol, self.constantSymbol, self.specificSymbol,
                                       self.transactionIdentifier, self.systemDescription, self.senderDescription, self.addresseeDescription,
                                       self.AV1, self.AV2, self.AV3, self.AV4])
        return ','.join(nonEmptyFields).lower()

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

    def delete(self):
        dbif.remove_transaction(self.id)

    def find_classifications(self) -> None:
        self.find_tr_type()
        self.find_category()
        self.find_tags()

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
            self.category = CATEGORY_CREDIT
            return
        for categoryId, signature in signatures.categories.items():
            if signature.lower() in self.signature:
                self.category = categoryId
                return

    def find_tags(self) -> None:
        assert isinstance(self.tags, set), "transaction tags are not a set"
        for tagId, signature in signatures.tags.items():
            if signature.lower() in self.signature:
                self.tags.add(tagId)