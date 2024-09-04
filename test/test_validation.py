import unittest

from trec_biogen_validator.util import SubmissionValidationError
from trec_biogen_validator.util.validator import Validator
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

        self.assertEqual(len(v), 1)

        self.assertEqual(len(v[0].errors), 0)
        self.assertEqual(len(v[0].warnings), 0)

    def test_load_file_with_bad_topic(self):
        path_to_file = "dummy_data/dummy_invalid_topic.json"
        try:
            v = self.validator.validate_submission(path_to_file)
        except Exception as e:
            self.fail(e.message)

        self.assertEqual(len(v), 1)

        self.assertEqual(len(v[0].errors), 1)
        self.assertEqual(len(v[0].warnings), 0)

        err_type, msg = v[0].errors[0]
        self.assertEqual(err_type, SubmissionValidationError.INVALID_TOPIC)

    def test_load_file_with_bad_pmid(self):
        path_to_file = "dummy_data/dummy_invalid_pmid.json"

        try:
            v = self.validator.validate_submission(path_to_file)
        except Exception as e:
            self.fail(e.message)

        self.assertEqual(len(v), 1)

        self.assertEqual(len(v[0].errors), 1)
        err_type, msg = v[0].errors[0]
        self.assertEqual(err_type, SubmissionValidationError.INVALID_PMID)

    def test_load_file_with_malformed_citations(self):
        path_to_file = "dummy_data/dummy_malformed_citations.json"

        try:
            v = self.validator.validate_submission(path_to_file)
        except Exception as e:
            self.fail(e.message)

        self.assertEqual(len(v), 1)

        self.assertEqual(len(v[0].errors), 1)
        self.assertEqual(len(v[0].warnings), 2)

        # make sure it caught the bad PMID
        err_type, msg = v[0].errors[0]
        self.assertEqual(err_type, SubmissionValidationError.INVALID_PMID)
