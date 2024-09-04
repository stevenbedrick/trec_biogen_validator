# 2024 TREC Biogen Validation Script

This script's goal is to validate submissions according to the rules described [on the task website](https://dmice.ohsu.edu/trec-biogen/submission_format.html).

## Installation Instructions

You will probably want to set up a virtual/conda environment for this.

1. Clone the repository
2. Install dependencies using pip: `pip install -r requirements.txt
3. Install the `en_core_web_lg` Spacy model: `python -m spacy download en_core_web_lg`
4. Make sure you have the necessary data files handy:
   - `BioGen2024topics-json.txt`
   - `pubmed_ids_last_20_years.json.gz`

## Instructions for Use

The simplest way to run the script is via the command line:

```{bash}
python -m trec_biogen_validator \
    --path_to_submission= PATH_TO_SUBMISSION_JSON_FILE \
    --path_to_valid_pmids PATH_TO_PUBMED_IDS_JSON_FILE \
    --path_to_topics PATH_TO_TOPICS_JSON_FILE
```

The program will open the submission file, go through each topic, and perform appropriate validations, printing out information about errors and warnings along the way.

The program has an optional argument, `--dump_sentence_tokenization`; if this is set, topics that have errors or warnings will be accompanied by a dump of the Spacy sentence tokenization, to aid in debugging.

In addition to this method of command-line use, you can also run the program via a config file. The script uses `[jsonargparse](https://jsonargparse.readthedocs.io/`) so any of its formats will work; for example, YAML is an option:

```{yaml}
path_to_submission: PATH_TO_SUBMISSION_JSON_FILE
path_to_valid_pmids: PATH_TO_PUBMED_IDS_JSON_FILE
path_to_topics: PATH_TO_TOPICS_JSON_FILE
dump_sentence_tokenization: true
```

And then from the terminal:

```{bash}
python -m trec_biogen_validator --config=PATH_TO_CONFIG_FILE
```

## API usage

The real action is happening in the `trec_biogen_validator.util.validator.Validator` class; if you want to "roll your own" wrapper around this functionality, it should be pretty straightforward. 
Take a look at the unit tests or at `trec_biogen_validator/__main__.py` for examples of how the class works.