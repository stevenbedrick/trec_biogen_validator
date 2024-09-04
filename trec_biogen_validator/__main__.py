import json
import logging
import os
import sys
from typing import Optional
import traceback

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

ERROR_RETURN_CODE = 255


def cmd(
    path_to_submission: str,
    path_to_valid_pmids: str,
    path_to_topics: str,
    max_sentences_per_output: int = DEFAULT_MAX_SENTENCES_PER_ANSWER,
    max_words_per_output: int = DEFAULT_MAX_WORDS_PER_ANSWER,
    spacy_model: str = DEFAULT_SPACY_MODEL,
    dump_sentence_tokenization: bool = False,
    console_output: bool = False,
    output_fname: Optional[str] = None,
):
    """
    Perform validation of a TREC Biogen submission, according to the rules described
    on the task website.

    Exit code of 0 means there were no errors (but there may be warnings); exit code of 255 means errors present.

    :param path_to_submission: The path to the TREC Biogen submission JSON file we wish to validate.
    :param path_to_valid_pmids: Path to the "pubmed_ids_last_20_years.json.gz" file
    :param path_to_topics: Path to the "BioGen2024topics-json.txt" file distributed to participants
    :param max_sentences_per_output: Maximum number of sentences per answer
    :param max_words_per_output:
    :param spacy_model:
    :param dump_sentence_tokenization: If true, print out the sentence tokenization for topics that have errors or warnings, to help with debugging.
    :param console_output: If true, print output to console; otherwise (default) write to output file
    :param output_fname: The name of the output file; defaults to basename(PATH_TO_SUBMISSION).err in current working directory
    :return:
    """

    # compute output file name
    if console_output:
        output_fp = sys.stdout
        logger.info("Console mode, logging to stdout...")
    else:
        base_fname, _ = os.path.splitext(os.path.basename(path_to_submission))
        default_output_fname = f"{base_fname}.errlog"
        if output_fname is None:
            fname_to_use = default_output_fname
        else:
            fname_to_use = output_fname
        logger.info(f"Logging output to {fname_to_use}")
        output_fp = open(fname_to_use, "w")

    if console_output:
        target_width = None  # auto-detect
    else:
        target_width = 1024
    console = Console(file=output_fp, width=target_width)

    val = Validator(
        path_to_valid_pmids,
        path_to_topics,
        max_words_per_output=max_words_per_output,
        max_sentences_per_output=max_sentences_per_output,
        spacy_model=spacy_model,
    )

    if not os.path.exists(path_to_valid_pmids):
        raise FileNotFoundError(f"{path_to_valid_pmids} does not exist")

    try:
        with open(path_to_submission, "r") as submission_io:
            s = Submission.model_validate(json.load(submission_io))
    except Exception as e:
        logger.error(f"Error loading submission file!")
        console.print(f"Error loading submission file: {e}")
        console.print(traceback.format_exc())
        if not console_output:
            output_fp.close()
        sys.exit(ERROR_RETURN_CODE)

    v = val.validate_submission(path_to_submission)

    found_error = False

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
            found_error = True
            console.print(f"\t{len(validation_results.errors)} errors", style="red")
            for err_type, msg in validation_results.errors:
                console.print(f"\t\t❌ {msg}")
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
    if not console_output:
        output_fp.close()
    if found_error:
        sys.exit(ERROR_RETURN_CODE)
    else:
        sys.exit(0)


if __name__ == "__main__":
    CLI(cmd)
