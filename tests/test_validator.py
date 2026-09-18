import tempfile
import unittest
from pathlib import Path

from sonnet_validate import read_lexicon, validate_poem, validate_word, word_syllables

ROOT = Path(__file__).resolve().parents[1]
DID_A = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK"
DID_B = "did:key:z6MkereFQqHaUdcF7yVmHvY1rHpAvVjeCggaBVy45hmE8G6C"
LEXICON = {"the": 1, "i": 1, "deeded": 2, "i'd": 1, "wool": 1}


def poem_with(lines: int = 14, words: int = 10) -> str:
    return "\n".join([" ".join(["I"] * words)] * lines)


class WordTests(unittest.TestCase):
    def test_letter_reuse_case_prefix_and_punctuation(self):
        self.assertEqual(validate_word("THE;", DID_A, LEXICON), 1)
        # The shared did:key: prefix supplies d/e, and letter reuse is unlimited.
        self.assertEqual(validate_word("DeeDeD!", DID_B, LEXICON), 2)
        self.assertEqual(validate_word("I'd,", DID_B, LEXICON), 1)

    def test_missing_letters_and_invalid_dids_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "letters absent"):
            validate_word("wool", DID_A, LEXICON)
        for did in ("agent-a", DID_A + "#key", DID_A.upper(), None):
            with self.subTest(did=did), self.assertRaises(ValueError):
                validate_word("I", did, LEXICON)

    def test_unknown_words_and_token_bypasses_are_rejected(self):
        for word in ("notindictionary", "I I", "I\n", "I--", "I!!", "1", "І", "", None):
            with self.subTest(word=word), self.assertRaises(ValueError):
                word_syllables(word, LEXICON)

    def test_zero_syllable_dictionary_entries_are_not_playable(self):
        lexicon = read_lexicon(ROOT / "cmudict.dict")
        zero_syllable_words = ("hm", "hmm", "hmmm", "mm", "sh", "shh", "ths")

        for word in zero_syllable_words:
            with self.subTest(word=word):
                self.assertIn(word, lexicon)
                self.assertEqual(lexicon[word], 0)
                with self.assertRaisesRegex(ValueError, "has no vowel phone"):
                    word_syllables(word, lexicon)

        with self.assertRaisesRegex(ValueError, "not in the frozen dictionary"):
            word_syllables("notindictionary", lexicon)

    def test_largest_pronunciation_count_is_used(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "dict"
            path.write_text(";;; comment\n# comment\nTEST T EH1 S T\n"
                            "TEST(2) T EH1 S AH0 T # variant\n")
            self.assertEqual(read_lexicon(path), {"test": 2})

            path.write_text("# no usable pronunciations\n")
            with self.assertRaisesRegex(ValueError, "no usable"):
                read_lexicon(path)

            path.write_text("SHH SH\n")
            with self.assertRaisesRegex(ValueError, "no usable"):
                read_lexicon(path)


class FormTests(unittest.TestCase):
    def test_exact_ten_and_overflow(self):
        self.assertEqual(validate_poem(poem_with(), LEXICON, exact_ten=True), [10] * 14)
        self.assertEqual(validate_poem(poem_with(words=9), LEXICON), [9] * 14)
        for poem in (poem_with(words=9), poem_with(words=11), poem_with(lines=13),
                     poem_with(lines=15), poem_with().replace("I I", "I  I", 1)):
            with self.subTest(poem=poem[:20]), self.assertRaises(ValueError):
                validate_poem(poem, LEXICON, exact_ten=True)

    def test_stanza_boundaries_and_terminal_newline(self):
        lines = poem_with().splitlines()
        text = "\n\n".join("\n".join(lines[a:b]) for a, b in ((0, 4), (4, 8), (8, 12), (12, 14)))
        self.assertEqual(validate_poem(text + "\n", LEXICON, exact_ten=True), [10] * 14)
        with self.assertRaisesRegex(ValueError, "stanzas"):
            validate_poem("\n\n".join(("\n".join(lines[:7]), "\n".join(lines[7:]))), LEXICON)

    def test_example_with_shipped_dictionary(self):
        lexicon = read_lexicon(ROOT / "cmudict.dict")
        self.assertGreater(len(lexicon), 100_000)
        self.assertEqual(validate_poem((ROOT / "examples/format-poem.txt").read_text(),
                                       lexicon, exact_ten=True), [10] * 14)


if __name__ == "__main__":
    unittest.main()
