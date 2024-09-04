import json
import logging
import os

from trec_biogen_validator.util import Submission
from trec_biogen_validator.util.validator import Validator
from trec_biogen_validator.util.validator import (
    DEFAULT_MAX_WORDS_PER_ANSWER,
    DEFAULT_MAX_SENTENCES_PER_ANSWER,
    DEFAULT_SPACY_MODEL,
)
from jsonargparse import CLI
from rich.console import Console

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cmd(
    path_to_submission: str,
    path_to_valid_pmids: str,
    path_to_topics: str,
    max_sentences_per_output: int = DEFAULT_MAX_SENTENCES_PER_ANSWER,
    max_words_per_output: int = DEFAULT_MAX_WORDS_PER_ANSWER,
    spacy_model: str = DEFAULT_SPACY_MODEL,
    dump_sentence_tokenization: bool = False,
):
    """
    Perform validation of a TREC Biogen submission, according to the rules described
    on the task website.

    :param path_to_submission: The path to the TREC Biogen submission JSON file we wish to validate.
    :param path_to_valid_pmids: Path to the "pubmed_ids_last_20_years.json.gz" file
    :param path_to_topics: Path to the "BioGen2024topics-json.txt" file distributed to participants
    :param max_sentences_per_output: Maximum number of sentences per answer
    :param max_words_per_output:
    :param spacy_model:
    :param dump_sentence_tokenization: If true, print out the sentence tokenization for topics that have errors or warnings, to help with debugging.
    :return:
    """

    console = Console()

    val = Validator(
        path_to_valid_pmids,
        path_to_topics,
        max_words_per_output=max_words_per_output,
        max_sentences_per_output=max_sentences_per_output,
        spacy_model=spacy_model,
    )

    if not os.path.exists(path_to_valid_pmids):
        raise FileNotFoundError(f"{path_to_valid_pmids} does not exist")

    with open(path_to_submission, "r") as submission_io:
        s = Submission.model_validate(json.load(submission_io))

    v = val.validate_submission(path_to_submission)

    for top_idx, (topic, validation_results) in enumerate(zip(s.results, v)):
        console.print(
            f"Topic {topic.topic_id} ({top_idx+1}/{len(s.results)})", style="bold"
        )

        if validation_results.is_valid():
            console.print("\tOverall: OK", style="green")
        else:
            console.print("\tOverall: Invalid", style="red")

        if len(validation_results.errors) == 0:
            console.print("\t✅ No errors", style="green")
        else:
            console.print(f"\t{len(validation_results.errors)} errors", style="red")
            for err_type, msg in validation_results.errors:
                console.print(f"\t\t❌ {msg}")

            console.print("\tSentence-level tokenization, in case it helps:")
        if len(validation_results.warnings) == 0:
            console.print("\t✅ No warnings", style="green")
        else:
            console.print(
                f"\t{len(validation_results.warnings)} warnings", style="dark_orange"
            )
            for err_type, msg in validation_results.warnings:
                console.print(f"\t\t⚠️ {msg}")

        if (
            len(validation_results.errors) > 0 or len(validation_results.warnings) > 0
        ) and dump_sentence_tokenization:
            console.print("\tSentence-level tokenization, in case it helps:")
            for sentence_idx, parsed_sentence in enumerate(
                validation_results.parsed_answer.sentences
            ):
                console.print(f"\t\t{sentence_idx+1}. {parsed_sentence.answer_content}")


if __name__ == "__main__":
    CLI(cmd)
