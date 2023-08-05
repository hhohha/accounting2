from typing import Dict

import dbif
from enums import ClsType


class Signatures:
    def __init__(self):
        self.tr_types: Dict[int, str] = {}
        self.categories: Dict[int, str] = {}
        self.tags: Dict[int, str] = {}

    def load(self):
        result = dbif.get_signatures_of_cls_type(ClsType.TR_TYPE)
        #for idx, signature


