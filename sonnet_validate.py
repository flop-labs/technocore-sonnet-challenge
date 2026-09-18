"""Draft sonnet format validator; no service integration or publishing side effects."""

import argparse
import hashlib
import json
import re
from pathlib import Path

# Restrict the game's spelling grammar instead of guessing how to split tokens.
WORD = re.compile(r"[A-Za-z]+(?:'[A-Za-z]+)*")
TOKEN = re.compile(r"([A-Za-z]+(?:'[A-Za-z]+)*)[,.;:!?]?")
# Shape guard only. The referee separately verifies the exact DID and signature.
ED25519_DID = re.compile(r"did:key:z6Mk[1-9A-HJ-NP-Za-km-z]{44}")
VOWELS = {"AA", "AE", "AH", "AO", "AW", "AY", "EH", "ER", "EY", "IH", "IY", "OW", "OY", "UH", "UW"}


def read_lexicon(path: Path) -> dict[str, int]:
    """Read CMUdict text; charge the largest listed syllable count per word."""
    counts: dict[str, int] = {}
    for entry in path.read_text(encoding="utf-8").splitlines():
        # Current CMUdict uses # comments; older files use ;;; comment lines.
        fields = entry.split("#", 1)[0].split()
        if not fields or fields[0].startswith(";;;"):
            continue
        word = re.sub(r"\(\d+\)$", "", fields[0]).lower()
        if not WORD.fullmatch(word):
            continue
        count = sum(phone[:-1] in VOWELS and phone[-1:] in {"0", "1", "2"} for phone in fields[1:])
        counts[word] = max(counts.get(word, 0), count)
    if not any(counts.values()):
        raise ValueError("dictionary: no usable pronunciations")
    return counts


def word_syllables(token: str, lexicon: dict[str, int]) -> int:
    """Validate exactly one game word; never accept a caller-supplied count."""
    if not isinstance(token, str) or not (match := TOKEN.fullmatch(token)):
        raise ValueError("word: expected one English word with optional trailing punctuation")
    word = match[1].lower()
    if word not in lexicon:
        raise ValueError(f"word: {word!r} is not in the frozen dictionary")
    if lexicon[word] == 0:
       raise ValueError(f"word: {word!r} has no vowel phone in the frozen dictionary")
    return lexicon[word]


def validate_word(token: str, verified_did: str, lexicon: dict[str, int]) -> int:
    """Check a word against the authenticated sender's DID; return syllables."""
    count = word_syllables(token, lexicon)
    if not isinstance(verified_did, str) or not ED25519_DID.fullmatch(verified_did):
        raise ValueError("agent_did: expected the registered Ed25519 did:key")
    allowed = {ch for ch in verified_did.lower() if "a" <= ch <= "z"}
    letters = {ch for ch in token.lower() if "a" <= ch <= "z"}
    missing = letters - allowed
    if missing:
        raise ValueError(f"word: letters absent from contributor DID: {''.join(sorted(missing))}")
    return count


def validate_poem(text: str, lexicon: dict[str, int], *, exact_ten: bool = False) -> list[int]:
    """Check form only; a final poem cannot prove its turn history or authorship."""
    text = text.removesuffix("\n")
    stanzas = text.split("\n\n")
    if len(stanzas) > 1 and [len(stanza.split("\n")) for stanza in stanzas] != [4, 4, 4, 2]:
        raise ValueError("stanzas: expected 4/4/4/2 lines")
    lines = [line for stanza in stanzas for line in stanza.split("\n")]
    if len(lines) != 14:
        raise ValueError(f"lines: expected 14, got {len(lines)}")
    counts = []
    for number, line in enumerate(lines, 1):
        try:
            count = sum(word_syllables(token, lexicon) for token in line.split(" "))
        except ValueError as error:
            raise ValueError(f"line {number}: {error}") from error
        if count > 10 or (exact_ten and count != 10):
            expected = "exactly 10" if exact_ten else "at most 10"
            raise ValueError(f"line {number}: syllables must be {expected}, got {count}")
        counts.append(count)
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dictionary", type=Path, help="Frozen CMUdict pronunciation file")
    parser.add_argument("poem", type=Path, help="Text file containing exactly 14 poem lines")
    parser.add_argument("--exact-ten", action="store_true")
    args = parser.parse_args()
    try:
        lexicon = read_lexicon(args.dictionary)
        counts = validate_poem(
            args.poem.read_text(encoding="utf-8"), lexicon, exact_ten=args.exact_ten
        )
        digest = hashlib.sha256(args.dictionary.read_bytes()).hexdigest()
    except (OSError, ValueError) as error:
        parser.exit(1, f"{error}\n")
    print(json.dumps({"form_valid": True, "syllables_per_line": counts, "dictionary_sha256": digest}))


if __name__ == "__main__":
    main()
