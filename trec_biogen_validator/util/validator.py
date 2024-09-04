import json, gzip, logging
from trec_biogen_validator.util import (
    TopicList,
    Submission,
    ValidationResults,
    Output,
    ParsedAnswer,
    SubmissionValidationError,
)
import spacy

from trec_biogen_validator.util.answer import AnswerParser

logger = logging.getLogger(__name__)

DEFAULT_MAX_SENTENCES_PER_ANSWER = 10
DEFAULT_MAX_WORDS_PER_ANSWER = 150
DEFAULT_SPACY_MODEL = "en_core_web_lg"


class Validator:
    def __init__(
        self,
        path_to_valid_pmids: str,
        path_to_topics: str,
        max_sentences_per_output: int = DEFAULT_MAX_SENTENCES_PER_ANSWER,
        max_words_per_output: int = DEFAULT_MAX_WORDS_PER_ANSWER,
        spacy_model: str = DEFAULT_SPACY_MODEL,
    ):
        self.max_sentences_per_output = max_sentences_per_output
        self.max_words_per_output = max_words_per_output

        self.valid_pmids = set(json.load(gzip.open(path_to_valid_pmids, "r")))
        logger.debug("Loaded %d valid PMIDs", len(self.valid_pmids))

        with open(path_to_topics, "r") as topic_io:
            self.topics = TopicList.model_validate(json.load(topic_io)).topics

        self.valid_topic_ids = {t.id for t in self.topics}

        logger.debug("Loaded %d topics", len(self.topics))

        self.nlp = spacy.load(spacy_model)

        self.parser = AnswerParser(self.nlp)

    def validate_submission(
        self,
        path_to_submission: str,
    ) -> list[ValidationResults]:

        to_ret = []

        # If the run file is malformed, this will let us know
        with open(path_to_submission, "r") as submission_io:
            s = Submission.model_validate(json.load(submission_io))

        # visit each Output, validate it
        for o in s.results:
            to_ret.append(self._validate_output(o))

        return to_ret

    def _validate_output(self, this_output: Output) -> ValidationResults:
        to_ret = ValidationResults()
        to_ret.errors = []
        to_ret.warnings = []

        if int(this_output.topic_id) not in self.valid_topic_ids:
            to_ret.errors.append(
                (
                    SubmissionValidationError.INVALID_TOPIC,
                    f"{this_output.topic_id} is not a valid topic!",
                )
            )

        parsed = self.parser.parse(this_output)
        to_ret.parsed_answer = parsed

        # checks: length
        wc = parsed.final_non_citation_word_count()
        if wc > self.max_words_per_output:
            to_ret.errors.append(
                (
                    SubmissionValidationError.TOO_MANY_WORDS,
                    f"{wc} non-citation, non-punctuation words found, max is {self.max_words_per_output}",
                )
            )

        if len(parsed.sentences) > self.max_sentences_per_output:
            to_ret.errors.append(
                (
                    SubmissionValidationError.TOO_MANY_SENTENCES,
                    f"{len(this_output.sentences)} sentences found, max is {self.max_sentences_per_output}",
                )
            )

        # now, check citations
        # first check: are all citations mentioned in refs valid ones?
        for c in this_output.references:
            if c not in self.valid_pmids:
                to_ret.errors.append(
                    (
                        SubmissionValidationError.INVALID_PMID,
                        f"{c} from main references list is not a valid PMID",
                    )
                )

        # next, see if any of our sentences had invalid PMIDs:
        for s_idx, s in enumerate(parsed.sentences):
            for c in s.cited_pmids:
                if c not in self.valid_pmids:
                    to_ret.errors.append(
                        (
                            SubmissionValidationError.INVALID_PMID,
                            f"PMID cited in sentence {s_idx+1} is not a valid PMID.",
                        )
                    )
            # Now also make a note of any citation parsing issues we found; those are all just warnings
            if s.citation_parse_errors:
                for ce in s.citation_parse_errors:
                    to_ret.warnings.append(ce)

        return to_ret
