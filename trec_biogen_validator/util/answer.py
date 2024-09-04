import logging
from typing import Optional

from spacy.tokens import Span

logger = logging.getLogger(__name__)

import spacy
from spacy import Language
from trec_biogen_validator.util import (
    Output,
    ParsedAnswer,
    ParsedSentence,
    SubmissionValidationError,
    CitationSpan,
    ValidationErrorWithMessage,
    Submission,
)
import re

CITATION_SECTION_REGEX = re.compile(r"(\[(?:\d+,?\s*)+\])")
INDIVIDUAL_CITATION_REGEX = re.compile(r"\d+")
SENTENCE_FINAL_PUNCTUATION_REGEX = re.compile(r"([\.\!\?])")


class AnswerParser:
    def __init__(self, nlp: Language):
        self.nlp = nlp

    def parse(self, some_output: Output) -> ParsedAnswer:

        doc = self.nlp(some_output.answer)  # sentence tokenize

        parsed_sentences = []

        for sentence_idx, this_sent in enumerate(doc.sents):
            parsed_sentences.append(
                self._parse_answer_sentence(this_sent, sentence_id=sentence_idx)
            )

        return ParsedAnswer(raw=some_output, sentences=parsed_sentences)

    def parse_citations(
        self, raw_sentence: str, sentence_id: Optional[int] = None
    ) -> tuple[
        list[str],
        list[CitationSpan],
        Optional[ValidationErrorWithMessage],
    ]:
        """
        We need to find bracketed citations, like "blah blah [1,2] blah [2,3,4]."

        Goal is to identify the uniqued list of cited numbers, with their order in the original sentence preserved.

        Cases to handle: brackets outside sentences, empty bracket, duplicates. All should be ignored.

        Assumptions: raw_sentence contains a single sentence; if that's not the case, or if the sentence ends with random fragments, this might not work.

        :param raw_sentence:
        :param sentence_id: Optional identifier to include in error messages
        :return:
        """

        if sentence_id is None:
            sentence_label = "sentence"
        else:
            sentence_label = f"sentence {sentence_id}"

        # first, find the list of all candidate spans
        candidate_spans = self._find_citation_spans(raw_sentence)
        if len(candidate_spans) == 0:
            return [], [], None

        citation_parse_errors: list[ValidationErrorWithMessage] = []

        # next, remove invalid candidate spans.
        # To be valid, a span must occur INSIDE A SENTENCE - i.e., it can't be at the beginning of raw_sentence, and it can't be after
        # raw_sentence's sentence-final punctuation.

        # find the location of the last final punctuation mark
        possible_final_punct = list(
            SENTENCE_FINAL_PUNCTUATION_REGEX.finditer(raw_sentence)
        )
        if len(possible_final_punct) == 0:
            final_punct_loc = -1
        else:
            final_punct_loc = possible_final_punct[-1].start()

        validated_spans = []
        for span_start, span_stop in candidate_spans:
            # check- are we at the beginning of the sentence?
            # trivial case- does this span start at 0?
            if span_start == 0:
                # skip if so, we must be before the sentence started - or the sentence consists entirely
                # of a citation span, which also isn't what we want
                citation_parse_errors.append(
                    (
                        SubmissionValidationError.IGNORED_CITATION_BLOCK,
                        f"Citation block found at start of {sentence_label}; ignored.",
                    )
                )
                continue

            # next case: the sentence starts with whitespace, up to this span- if so, skip
            if len(raw_sentence[0:span_start].strip()) == 0:
                citation_parse_errors.append(
                    (
                        SubmissionValidationError.IGNORED_CITATION_BLOCK,
                        f"Citation block found at start of {sentence_label}; ignored.",
                    )
                )
                continue

            # next case: deal with citation spans that come after the sentence-final punctuation
            if final_punct_loc > 0:  # did we even have a final punctuation mark?
                # where is this span in relation to the final punctuation mark?
                if (
                    span_start > final_punct_loc
                ):  # this citation span is after the final punctuation location
                    citation_parse_errors.append(
                        (
                            SubmissionValidationError.IGNORED_CITATION_BLOCK,
                            f"Citation block found at end of {sentence_label}, after final punctuation; ignored.",
                        )
                    )
                    continue
            else:
                # no final punctuation was found which is pretty weird and suggests that Spacy did something anomalous with
                # this sentence, and so we are going to ignore it altogether
                citation_parse_errors.append(
                    (
                        SubmissionValidationError.IGNORED_CITATION_BLOCK,
                        f"No final punctuation in {sentence_label}, ignoring citations since we don't know where they belong.",
                    )
                )
                continue

            # if we made it this far, we must be good to go
            validated_spans.append((span_start, span_stop))

        found_citations = []
        for citation_span in validated_spans:
            matches = INDIVIDUAL_CITATION_REGEX.finditer(
                raw_sentence[citation_span[0] : citation_span[1]]
            )
            for m in matches:
                found_citations.append(m.group())

        # now, take the first instance of each of these citations, preserving order
        seen_citations = {}
        final_citation_list = []
        duplicate_citations = []
        for f in found_citations:
            if f not in seen_citations:
                seen_citations[f] = True  # mark down that we've already seen this one
                final_citation_list.append(f)
            else:
                duplicate_citations.append(f)

        for dup_cit in set(duplicate_citations):
            citation_parse_errors.append(
                (
                    SubmissionValidationError.REPEATED_PMID,
                    f"PMID {dup_cit} repeated in {sentence_label}.",
                )
            )

        if len(citation_parse_errors) > 0:
            err_to_ret = citation_parse_errors
        else:
            err_to_ret = None

        return final_citation_list, validated_spans, err_to_ret

    def _find_citation_spans(self, some_input: str) -> list[CitationSpan]:
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

    def _parse_answer_sentence(
        self, sent: Span, sentence_id: Optional[int] = None
    ) -> ParsedSentence:
        cited_pmids, citation_spans, err = self.parse_citations(sent.text, sentence_id)

        # compute a word count
        official_word_count = self._non_punct_word_count(
            self._remove_citation_spans(sent.text)
        )

        return ParsedSentence(
            answer_content=sent.text,
            cited_pmids=cited_pmids,
            valid_citation_spans=citation_spans,
            official_word_count=official_word_count,
            citation_parse_errors=err,
        )

    def _non_punct_word_count(self, some_text: str) -> int:
        as_span = self.nlp(some_text)
        return len([tok for tok in as_span if not tok.is_punct])


if __name__ == "__main__":
    nlp = spacy.load("en_core_web_lg")
    d = nlp(
        "A minor corneal abrasion can take 1-3 days to heal on its own [32091909]. However, this timeframe may vary depending on the severity and location of the injury. Studies have shown that most superficial corneal abrasions will recover in a week or less with minimal treatment [28678410]. The healing process may be slowed in people with pre-existing conditions such as diabetes or vitamin deficiencies. In general, if symptoms worsen or do not improve within 3-5 days, medical attention should be sought. Delaying treatment can lead to complications and prolonged recovery times [31886449]."
    )
    for s in d.sents:

        print(s)
        for t in s:
            print("\t", t, "\t", t.pos_, "\t", t.is_punct)
