from typing import Dict

import dbif
from enums import ClsType

class Signatures:
    def __init__(self):
        self.tr_types: Dict[int, str] = {}
        self.categories: Dict[int, str] = {}
        self.tags: Dict[int, str] = {}
        self.load()

    def load(self):
        self.tr_types = dict(dbif.get_signatures_of_cls_type(ClsType.TR_TYPE))
        self.categories = dict(dbif.get_signatures_of_cls_type(ClsType.CATEGORY))
        self.tags = dict(dbif.get_signatures_of_cls_type(ClsType.TAG))

signatures = Signatures()