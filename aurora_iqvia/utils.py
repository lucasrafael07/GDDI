# -*- coding: utf-8 -*-
from __future__ import annotations
import hashlib
import json
from datetime import date, datetime, timedelta
from typing import Iterable, Generator

def only_digits(s: str | None) -> str:
    if not s:
        return ""
    return "".join(ch for ch in str(s) if ch.isdigit())

def md5_bytes(b: bytes) -> str:
    return hashlib.md5(b).hexdigest()

def beautify_json(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2)

def daterange(d0: date, d1: date) -> Generator[date, None, None]:
    cur = d0
    while cur <= d1:
        yield cur
        cur += timedelta(days=1)

def parse_br_date(s: str) -> date:
    return datetime.strptime(s, "%d/%m/%Y").date()
