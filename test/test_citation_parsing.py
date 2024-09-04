import unittest

from trec_biogen_validator.util import SubmissionValidationError
from trec_biogen_validator.util.answer import AnswerParser
import spacy


class TestValidation(unittest.TestCase):

    def setUp(self):
        self.nlp = spacy.load("en_core_web_lg")
        self.parser = AnswerParser(nlp=self.nlp)

    def test_simple_sentence(self):
        s = "This is a sentence with proper formatting [1,2,3,4]."

        res, spans, err = self.parser.parse_citations(s)

        self.assertEqual(len(res), 4)

        self.assertIsNone(err)

    def test_complex_sentence(self):
        s = "This sentence has [1,2,3] citations that are interspersed [4,5,6] throughout [8,9]."
        res, spans, err = self.parser.parse_citations(s)
        self.assertEqual(len(res), 8)
        self.assertListEqual(res, ["1", "2", "3", "4", "5", "6", "8", "9"])
        self.assertIsNone(err)

    def test_duplicate(self):
        s = "This sentence [1,2] has duplicates [2,3]."  # citation 2 should not be duplicated
        res, spans, err = self.parser.parse_citations(s)
        self.assertEqual(len(res), 3)
        self.assertListEqual(res, ["1", "2", "3"])
        self.assertIsNotNone(err)
        self.assertEqual(len(err), 1)

        # Also make sure the right parse error made it out
        err_type, msg = err[0]
        self.assertEqual(err_type, SubmissionValidationError.REPEATED_PMID)

    def test_after_period(self):
        s = "This sentence has the citations outside of the period; they should be ignored. [1,2,3,14]"
        res, spans, err = self.parser.parse_citations(s)
        self.assertEqual(len(res), 0)
        self.assertListEqual(res, [])

        self.assertIsNotNone(err)
        self.assertEqual(len(err), 1)
        err_type, msg = err[0]
        self.assertEqual(err_type, SubmissionValidationError.IGNORED_CITATION_BLOCK)

        s2 = "This sentence has the citations outside the period and then a bunch of whitespace; that shouldn't mess us up. [1,2,3,14]     "
        res, spans, err = self.parser.parse_citations(s2)
        self.assertEqual(len(res), 0)
        self.assertListEqual(res, [])

        self.assertIsNotNone(err)
        self.assertEqual(len(err), 1)
        err_type, msg = err[0]
        self.assertEqual(err_type, SubmissionValidationError.IGNORED_CITATION_BLOCK)

        s3 = "This sentence has [1,2,4] citations in the sentence and then some outside [1,2,3,4], ignore the ones outside. [5,6,7]"
        res, spans, err = self.parser.parse_citations(s3)

        self.assertEqual(len(res), 4)
        self.assertListEqual(res, ["1", "2", "4", "3"])

        self.assertIsNotNone(err)
        self.assertEqual(len(err), 4)
        codes = {e[0] for e in err}
        self.assertSetEqual(
            codes,
            {
                SubmissionValidationError.IGNORED_CITATION_BLOCK,
                SubmissionValidationError.REPEATED_PMID,
            },
        )

        s4 = "This sentence has citations after the sentence but then also a sentence fragment- ignore the ones outside the sentence. [1,2,3,4] This is a fragment"
        res, spans, err = self.parser.parse_citations(s4)
        self.assertEqual(len(res), 0)
        self.assertIsNotNone(err)
        self.assertEqual(len(err), 1)
        err_type, msg = err[0]
        self.assertEqual(err_type, SubmissionValidationError.IGNORED_CITATION_BLOCK)

    def test_before_sentence(self):
        s = "[1,2,3,4] This sentence has the citations before the sentence even starts; ignore them."
        res, spans, err = self.parser.parse_citations(s)
        self.assertEqual(len(res), 0)
        self.assertIsNotNone(err)
        self.assertEqual(len(err), 1)
        err_type, msg = err[0]
        self.assertEqual(err_type, SubmissionValidationError.IGNORED_CITATION_BLOCK)

        s2 = "     [1,2,3,4] This sentence starts with a bunch of whitespace and then our citations, ignore it all."
        res, spans, err = self.parser.parse_citations(s2)
        self.assertEqual(len(res), 0)
        self.assertIsNotNone(err)
        self.assertEqual(len(err), 1)
        err_type, msg = err[0]
        self.assertEqual(err_type, SubmissionValidationError.IGNORED_CITATION_BLOCK)

        s3 = "[1,2,3] This sentence has the citations before the sentence and then has some good ones; count those [4,5,6,7]."
        res, spans, err = self.parser.parse_citations(s3)
        self.assertEqual(len(res), 4)
        self.assertListEqual(res, ["4", "5", "6", "7"])
        self.assertIsNotNone(err)
        self.assertEqual(len(err), 1)
        err_type, msg = err[0]
        self.assertEqual(err_type, SubmissionValidationError.IGNORED_CITATION_BLOCK)

    def test_find_citation_spans(self):
        s = "blah blah [1,2] blah [2,3,4]."

        res = self.parser._find_citation_spans(s)

        self.assertEqual(len(res), 2)
        self.assertTupleEqual(res[0], (10, 15))
        self.assertTupleEqual(res[1], (21, 28))

        # a string with no citations should not find any
        s2 = "blah blah blah no citations."
        res = self.parser._find_citation_spans(s2)
        self.assertEqual(len(res), 0)
        self.assertListEqual(res, [])

        # a string with citations at the very beginning
        s3 = "[1,2,3] this string starts with a citation"
        res = self.parser._find_citation_spans(s3)
        self.assertEqual(len(res), 1)
        self.assertTupleEqual(res[0], (0, 7))

        # a string where the citation spans include spaces after the commas
        s4 = s = "blah blah [1, 2] blah [2, 3, 4]."
        res = self.parser._find_citation_spans(s4)

        self.assertEqual(len(res), 2)
        self.assertTupleEqual(res[0], (10, 16))
        self.assertTupleEqual(res[1], (22, 31))

    def test_remove_citation_spans(self):
        s = "blah blah [1,2] blah [2,3,4]."
        res = self.parser._remove_citation_spans(s)
        self.assertEqual("blah blah  blah .", res)

        # and now a case where the citation span is at the end of the input
        s2 = "blah blah [1,2] blah [2,3,4]"
        res = self.parser._remove_citation_spans(s2)
        self.assertEqual("blah blah  blah ", res)

        # and at the start
        s3 = "[21, 22] blah blah [1, 2] blah [2,3,4]"
        res = self.parser._remove_citation_spans(s3)
        self.assertEqual(" blah blah  blah ", res)
