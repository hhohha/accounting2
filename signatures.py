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

        self.tags = {}
        for signature, sig_id in dbif.get_signatures_of_cls_type(ClsType.TAG):
            if signature not in self.tags:
                self.tags[signature] = []
            self.tags[signature].append(sig_id)
        # self.tags = dict(dbif.get_signatures_of_cls_type(ClsType.TAG))

signatures = Signatures()