import logging
from typing import Optional

logger = logging.getLogger(__name__)

import spacy
from spacy import Language
from util import Output, ParsedAnswer, ParsedSentence
import re

CITATION_SECTION_REGEX = re.compile(r"(\[(?:\d+,?\s*)+\])")
INDIVIDUAL_CITATION_REGEX = re.compile(r"\d+")


class AnswerParser:
    def __init__(self, nlp: Language):
        self.nlp = nlp

    def parse(self, some_output: Output) -> ParsedAnswer:

        doc = self.nlp(some_output.answer)

        to_return = ParsedAnswer()
        to_return.raw = some_output

        for s in doc.sents:
            this_ps = ParsedSentence()
            this_ps.text = s.text
            this_ps.cited_pmids = self.parse_citations(s.text)

    def parse_citations(self, raw_sentence: str) -> list[str]:
        """
        We need to find bracketed citations, like "blah blah [1,2] blah [2,3,4]."

        Goal is to identify the uniqued list of cited numbers, with their order in the original sentence preserved.

        Cases to handle: brackets outside sentences, empty bracket, duplicates. All should be ignored.
        :param raw_sentence:
        :return:
        """

        # first, find the list of all candidate spans
        candidate_spans = self._find_citation_spans(raw_sentence)
        if len(candidate_spans) == 0:
            return []

        pass

    def _find_citation_spans(self, some_input: str) -> list[tuple[int, int]]:
        """
        Find locations of candidate citation spans in the input, or an empty list if none.
        :param some_input:
        :return: A list of tuples of the start and stop offsets of any citations spans that we found.
        """
        matches = list(re.finditer(CITATION_SECTION_REGEX, some_input))

        if matches:
            return [(m.start(), m.end()) for m in matches]
        else:
            return []

    def _remove_citation_spans(self, some_input: str) -> str:
        """
        Return a version of some_input with all citation spans removed; this is useful for
        word counting. No promises that the resulting sentence won't have some weird whitespace
        issues...

        :param some_input:
        :return:
        """
        spans_to_remove = self._find_citation_spans(some_input)
        if len(spans_to_remove) == 0:
            return some_input

        chunks = []
        last_offset = 0
        for span in spans_to_remove:
            chunks.append(some_input[last_offset : span[0]])
            last_offset = span[1]
        # and then cleanup
        chunks.append(some_input[last_offset:])
        return "".join(chunks)


if __name__ == "__main__":
    nlp = spacy.load("en_core_web_sm")
    d = nlp(
        "A minor corneal abrasion can take 1-3 days to heal on its own [32091909]. [2343243242] However, this timeframe may vary depending on the severity and location of the injury."
    )
    for s in d.sents:

        print(s)
        for t in s:
            print("\t", t)
