import unittest

from src.ai_answer import validate_citations


class CitationTests(unittest.TestCase):
    def setUp(self):
        self.extracts = [{"page": 161, "text": "Sample evidence"}]

    def test_supplied_page_is_accepted(self):
        validate_citations(
            "Finance cost: PKR 6,170,739 thousand [PDF page 161].",
            self.extracts,
        )

    def test_missing_citation_is_rejected(self):
        with self.assertRaises(RuntimeError):
            validate_citations(
                "Finance cost: PKR 6,170,739 thousand.",
                self.extracts,
            )

    def test_unsupplied_page_is_rejected(self):
        with self.assertRaises(RuntimeError):
            validate_citations(
                "Finance cost [PDF page 999].",
                self.extracts,
            )

    def test_mixed_valid_and_invalid_pages_are_rejected(self):
        with self.assertRaises(RuntimeError):
            validate_citations(
                "One claim [PDF page 161]. Another [PDF page 999].",
                self.extracts,
            )

    def test_missing_information_response_is_accepted(self):
        validate_citations(
            "Not available in the provided extracts.",
            self.extracts,
        )


if __name__ == "__main__":
    unittest.main()