import json, gzip, logging
from util import (
    TopicList,
    Submission,
    ValidationResults,
    SubmissionValidationError,
    Output,
)
from util.answer import AnswerParser
import spacy

logger = logging.getLogger(__name__)

DEFAULT_MAX_SENTENCES_PER_ANSWER = 10
DEFAULT_MAX_WORDS_PER_ANSWER = 150


class Validator:
    def __init__(self, path_to_valid_pmids: str, path_to_topics: str):
        self.valid_pmids = set(json.load(gzip.open(path_to_valid_pmids, "r")))
        logger.debug("Loaded %d valid PMIDs", len(self.valid_pmids))

        with open(path_to_topics, "r") as topic_io:
            self.topics = TopicList.model_validate(json.load(topic_io)).topics

        self.valid_topic_ids = {t.id for t in self.topics}

        logger.debug("Loaded %d topics", len(self.topics))

        self.nlp = spacy.load("en_core_web_sm")

    def validate_submission(
        self,
        path_to_submission: str,
        max_sentences_per_answer: int = DEFAULT_MAX_SENTENCES_PER_ANSWER,
        max_words_per_answer: int = DEFAULT_MAX_WORDS_PER_ANSWER,
    ) -> ValidationResults:

        to_ret = ValidationResults()
        to_ret.errors = []

        # If the run file is malformed, this will let us know
        with open(path_to_submission, "r") as submission_io:
            s = Submission.model_validate(json.load(submission_io))

        return to_ret

    def validate_output(self, this_output: Output) -> ValidationResults:
        to_ret = ValidationResults()
        to_ret.errors = []

        return to_ret
