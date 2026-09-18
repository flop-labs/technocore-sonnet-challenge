"""Check one word's dictionary count and DID letters; does not verify identity."""

import argparse
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from sonnet_validate import read_lexicon, validate_word  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("did", help="The contributor's exact registered DID")
    parser.add_argument("word", help="One word, with optional allowed punctuation")
    args = parser.parse_args()
    try:
        dictionary = ROOT / "cmudict.dict"
        actual = hashlib.sha256(dictionary.read_bytes()).hexdigest()
        source = json.loads((ROOT / "upstream.json").read_text(encoding="utf-8"))
        if actual != source["cmudict"]["dictionary"]["sha256"]:
            raise ValueError("dictionary: does not match frozen upstream hash")
        count = validate_word(args.word, args.did, read_lexicon(dictionary))
        if not 1 <= count <= 10:
            raise ValueError("word: exceeds the ten-syllable line budget")
    except (OSError, ValueError, KeyError) as error:
        print(error, file=sys.stderr)
        return 1
    print(json.dumps({"word_compatible": True, "syllables": count,
                      "signature_checked": False, "dictionary_sha256": actual}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
