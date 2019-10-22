import sys
import json
import yaml

try:
    jsonfile = sys.argv[1]
except IndexError:
    sys.err(f"Usage: {sys.argv[0]} JSONFILE")

with open(jsonfile) as f:
    data = json.load(f)

tickets = data["tickets"]
output = {"labels": {}}
tag_types = [
    ["component", "c:"],
    ["priority", "p:"],
    ["type", "t:"], 
    ["owner", "o:"], 
]
# Convert space to hyphen and drop punctuation
fixer = str.maketrans(" ", "-", ",;:")
for tag_type, prefix in tag_types:
    tag_list = set(d.get("attributes").get(tag_type) for d in tickets.values())
    output["labels"][tag_type] = {_: f"{prefix}{_.translate(fixer)}" for _ in tag_list}
    print(f"{tag_type}s:", tag_list)
    print()

kwd_list = []
for d in tickets.values():
#    kwd_list.extend(d.get("attributes").get("keywords").split(" "))
    kwd_list.append(d.get("attributes").get("keywords"))
kwd_list = set(kwd_list)
output["labels"]["keywords"] = {_: _.split() for _ in kwd_list}
print(f"keywords:", kwd_list)

with open("tag-translations.yaml", "w") as f:
    yaml.dump(output, f, default_flow_style=False)

