import logging
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


class ParsedAnswer(BaseModel):
    raw: Output
    sentences: list[ParsedSentence]


class ValidationResults:
    errors = Optional[list[tuple[SubmissionValidationError, str]]]
