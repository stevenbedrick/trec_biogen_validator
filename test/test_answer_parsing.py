import unittest
from trec_biogen_validator.util.answer import AnswerParser
from trec_biogen_validator.util import Submission
import spacy
import json


class TestAnswerParser(unittest.TestCase):

    def setUp(self):
        self.nlp = spacy.load("en_core_web_lg")
        self.parser = AnswerParser(nlp=self.nlp)

    def test_simple_case(self):
        path_to_file = "dummy_data/dummy_valid_submission.json"

        with open(path_to_file, "r") as submission_io:
            s = Submission.model_validate(json.load(submission_io))

        # sanity check- this file should only have one dummy answer
        self.assertEqual(1, len(s.results))

        a = self.parser.parse(s.results[0])

        # check that we got the right number of sentences
        self.assertEqual(6, len(a.sentences))

        citations_per_sentence = [1, 0, 1, 0, 0, 1]

        for (
            s_idx,
            sent,
        ) in enumerate(a.sentences):
            self.assertEqual(citations_per_sentence[s_idx], len(sent.cited_pmids))

        self.assertEqual(92, a.final_non_citation_word_count())

    def test_word_count_logic(self):
        s = "This sentence should have six words."
        c = self.parser._non_punct_word_count(s)
        self.assertEqual(6, c)

        s2 = "This sentence should have six words [1,2,3,4]."
        no_citation = self.parser._remove_citation_spans(s2)
        c = self.parser._non_punct_word_count(no_citation)
        self.assertEqual(6, c)
