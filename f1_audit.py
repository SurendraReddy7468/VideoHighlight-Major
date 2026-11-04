import json
import sys
from src.narrative.cues import annotate

sys.stdout.reconfigure(encoding="utf-8")
s = annotate(json.load(open("data/analysis/Begging_Disappear/sentences.json", encoding="utf-8")))

for i, x in enumerate(s):
    if x["dangle_start"] >= 0.5:
        print(f"#{x['id']}  score={x['dangle_start']}")
        print("   BEFORE:", s[i - 1]["text"] if i else "-")
        print("   THIS  :", x["text"])