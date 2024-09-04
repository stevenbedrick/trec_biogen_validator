import logging
from functools import lru_cache
from typing import List, Optional
import re
from .errors import SubmissionValidationError

logger = logging.getLogger(__name__)

from pydantic import BaseModel


class Topic(BaseModel):
    id: int
    topic: str
    question: str
    narrative: str


class TopicList(BaseModel):
    topics: list[Topic]


class Output(BaseModel):
    topic_id: str
    answer: str
    references: list[str]


class Submission(BaseModel):
    team_id: str
    run_name: str
    contact_email: str
    results: list[Output]


class ParsedSentence(BaseModel):
    answer_content: str
    cited_pmids: list[str]
    official_word_count: int
    valid_citation_spans: list[tuple[int, int]]
    citation_parse_errors: Optional[list["ValidationErrorWithMessage"]]


class ParsedAnswer(BaseModel):
    raw: Output
    sentences: list[ParsedSentence]

    def final_non_citation_word_count(self):
        return sum([s.official_word_count for s in self.sentences])


ValidationErrorWithMessage = tuple[SubmissionValidationError, str]


class ValidationResults:
    errors: Optional[list[ValidationErrorWithMessage]]
    warnings: Optional[list[ValidationErrorWithMessage]]
    parsed_answer: ParsedAnswer

    def is_valid(self) -> bool:
        if self.errors is None:
            return True
        elif len(self.errors) == 0:
            return True
        else:
            return False


CitationSpan = tuple[int, int]
