import logging

logger = logging.getLogger(__name__)

from enum import Enum, auto


class SubmissionValidationError(Enum):
    MALFORMED_RUN_FILE = auto()  # Submission JSON file does not match specified schema
    TOO_MANY_SENTENCES = auto()  # A given answer has too many sentences
    TOO_MANY_WORDS = auto()  # a given answer is over the word limit
    MALFORMED_CITATION = (
        auto()
    )  # a sentence's bracketed citations were not formed properly
    INVALID_PMID = auto()  # a provided PMID was not in the release dataset
    REPEATED_PMID = auto()  # a provided PMID was repeated in the references list
    ORPHANED_PMID = (
        auto()
    )  # a PMID in the reference list was not mentioned in any of the sentence-level output
