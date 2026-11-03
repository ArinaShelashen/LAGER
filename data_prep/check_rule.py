"""
check_rule.py – checks that MØD can read a rule.

Reads the GML text of a rule from standard input and prints one line of JSON:
    {"ok": true}
    {"ok": false, "error": "..."}

It runs as a separate process so that a broken rule can never disturb the web
server, and because MØD must be imported in a clean Python process.
Used by rules.py; can also be used by hand:
    python data_prep/check_rule.py < my_rule.gml
"""

import json
import sys


def main():
    gml = sys.stdin.read()
    try:
        from mod import Rule
        Rule.fromGMLString(gml, add=False)
        result = {"ok": True}
    except Exception as e:
        result = {"ok": False, "error": str(e).strip() or type(e).__name__}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
