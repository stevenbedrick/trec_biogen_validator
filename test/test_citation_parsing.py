import unittest
from util.answer import AnswerParser
from pydantic import ValidationError
import spacy


class TestValidation(unittest.TestCase):

    def setUp(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.parser = AnswerParser(nlp=self.nlp)

    def test_simple_sentence(self):
        s = "This is a sentence with proper formatting [1,2,3,4]."

        res = self.parser.parse_citations(s)

        self.assertEqual(len(res), 4)

    def test_complex_sentence(self):
        s = "This sentence has [1,2,3] citations that are interspersed [4,5,6] throughout [8,9]."
        res = self.parser.parse_citations(s)
        self.assertEqual(len(res), 8)
        self.assertListEqual(res, ["1", "2", "3", "4", "5", "6", "8", "9"])

    def test_duplicate(self):
        s = "This sentence [1,2] has duplicates [2,3]."  # citation 2 should not be duplicated
        res = self.parser.parse_citations(s)
        self.assertEqual(len(res), 3)
        self.assertListEqual(res, ["1", "2", "3"])

    def test_after_period(self):
        s = "This sentence has the citations outside of the period; they should be ignored. [1,2,3,14]"
        res = self.parser.parse_citations(s)
        self.assertEqual(len(res), 0)
        self.assertListEqual(res, ["1", "2", "3", "14"])

    def test_before_sentence(self):
        s = "[1,2,3,4] This sentence has the citations before the sentence even starts; ignore them."
        res = self.parser.parse_citations(s)
        self.assertEqual(len(res), 0)

        s2 = "[1,2,3] This sentence has the citations before the sentence and then has some good ones; count those [4,5,6,7]."
        res = self.parser.parse_citations(s2)
        self.assertEqual(len(res), 4)
        self.assertListEqual(res, ["4", "5", "6", "7"])

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
