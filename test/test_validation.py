import unittest
from util.validator import Validator
from pydantic import ValidationError


class TestValidation(unittest.TestCase):

    def setUp(self):
        self.validator = Validator(
            path_to_valid_pmids="dummy_data/pubmed_ids_last_20_years.json.gz",
            path_to_topics="dummy_data/BioGen2024topics-json.txt",
        )

    def test_die_on_malformed_file(self):
        path_to_file = "dummy_data/dummy_malformed_submission.json"
        with self.assertRaises(ValidationError):
            v = self.validator.validate_submission(path_to_file)

    def test_load_valid_file(self):
        path_to_file = "dummy_data/dummy_valid_submission.json"
        try:
            v = self.validator.validate_submission(path_to_file)
        except Exception as e:
            self.fail(e.message)

        self.assertEqual(len(v.errors), 0)
