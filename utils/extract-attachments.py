import sys
import json
import yaml
from pathlib import PurePath
import pprint

try:
    jsonfile = sys.argv[1]
except IndexError:
    sys.err(f"Usage: {sys.argv[0]} JSONFILE")

with open(jsonfile) as f:
    data = json.load(f)

tickets = data["tickets"]

attachments = []
for d in tickets.values():
    attachments.extend(d.get("attachments").keys())

#suffixes = set(tuple(PurePath(_).suffixes) for _ in attachments)
suffixes = set(PurePath(_).suffix for _ in attachments)

pprint.pprint(suffixes, compact=True)
