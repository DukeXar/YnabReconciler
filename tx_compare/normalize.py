from __future__ import annotations

import re


ALIASES = {
    "m&s": "marks and spencer",
    "marks and spencer clapham": "marks and spencer",
    "ls patty and bun holdi": "patty and bun",
    "patty bun holdings london": "patty and bun",
    "gails": "gails",
    "gail s": "gails",
    "gails limited reigate surrey": "gails",
    "gails abbeville road london": "gails",
    "roofoods ltd": "roofoods",
    "tfl travel charge": "transport for london",
    "amazon co uk": "amazon",
    "paypal betterme": "betterme",
    "paypal ubertrip": "uber",
    "zettle b century uk li": "b century",
    "hutchison 3g aruac": "hutchison 3g",
    "harleytherapy co uk": "er psychology",
}

PATTERN_ALIASES = [
    ("tfl travel charge", "transport for london"),
    ("m and s", "marks and spencer"),
    ("m s clapham", "marks and spencer"),
    ("harleytherapy co uk", "er psychology"),
    ("ls patty and bun", "patty and bun"),
]

KEYWORD_ALIASES = [
    ("gail", "gails"),
    ("waitrose", "waitrose"),
    ("sainsbury", "sainsburys"),
    ("itsu", "itsu"),
    ("amazon", "amazon"),
    ("caffe nero", "caffe nero"),
    ("deliveroo", "deliveroo"),
    ("pret a manger", "pret a manger"),
    ("roofoods", "roofoods"),
    ("uber eats", "uber eats"),
    ("trainline", "trainline"),
    ("wasabi", "wasabi"),
    ("nordic balance", "nordic balance"),
    ("2 love", "2 love"),
]


def normalize_merchant(value: str) -> str:
    s = value.lower().strip()
    s = s.replace("&", " and ")
    s = re.sub(r"https?://\S+", " ", s)
    s = re.sub(r"\b\d{3,}[-\d]*\b", " ", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    if s in ALIASES:
        return ALIASES[s]
    for pattern, alias in PATTERN_ALIASES:
        if pattern in s:
            return alias
    for pattern, alias in KEYWORD_ALIASES:
        if pattern in s:
            return alias
    return s
