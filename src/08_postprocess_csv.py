"""Postprocess the CSV file.

Prepare JSON file for deck generation.
"""

import ast
import json
import os

import pandas as pd
from utils.constants import (
    EXAMPLE_TRANSLATIONS_FIX_PATH,
    POSTPROCESSED_WORDLIST_JSON_PATH,
    PREPROCESSED_WORDLIST_CSV_PATH,
    TRANSLATIONS_DIR_PATH,
    WORD_TRANSLATIONS_FIX_JSON_PATH,
)
from utils.logger import logger

if not os.path.exists(PREPROCESSED_WORDLIST_CSV_PATH):
    logger.error(
        'Preprocessed wordlist CSV file not found. Did you run "05_preprocess_csv.py"?'
    )
    logger.error(f'{PREPROCESSED_WORDLIST_CSV_PATH} does not exist')
    raise SystemExit('Aborting')

df = pd.read_csv(PREPROCESSED_WORDLIST_CSV_PATH)

# Assert that all translations are in place.
for row in df.itertuples():
    if not os.path.exists(
        os.path.join(TRANSLATIONS_DIR_PATH, row.word, 'translation.txt')
    ):
        logger.error(f'Translation TXT file for word {row.word} does not exist')
        logger.error('Try running "07_translate.py"')
        raise SystemExit('Aborting')


def extract_word_translation(word: str) -> str:
    """Extract word translation from saved DeepL response."""
    path_to_translation_txt = os.path.join(
        TRANSLATIONS_DIR_PATH,
        word,
        'translation.txt',
    )

    with open(path_to_translation_txt, 'r', encoding='utf-8') as file:
        contents = file.read()

    split_contents = contents.split('---')
    # First item is a word
    word_translation = split_contents[0].strip()
    return str([word_translation])


df['word_translation'] = df['word'].apply(extract_word_translation)


def extract_examples_translations(word: str) -> str:
    """Extract examples translations from saved DeepL response."""
    path_to_translation_txt = os.path.join(
        TRANSLATIONS_DIR_PATH,
        word,
        'translation.txt',
    )

    with open(path_to_translation_txt, 'r', encoding='utf-8') as file:
        contents = file.read()

    split_contents = contents.split('---\n')
    translated_examples = []
    # First item is word, everything else is examples
    for example in split_contents[1:]:
        translated_examples.append(example.strip())

    return str(translated_examples)


df['examples_translations'] = df['word'].apply(extract_examples_translations)

with open(WORD_TRANSLATIONS_FIX_JSON_PATH, 'r') as file:
    word_translations_fix = json.load(file)
with open(EXAMPLE_TRANSLATIONS_FIX_PATH, 'r') as file:
    example_translations_fix = json.load(file)

manually_verified_words = set()
if os.path.exists(POSTPROCESSED_WORDLIST_JSON_PATH):
    with open(POSTPROCESSED_WORDLIST_JSON_PATH, 'r', encoding='utf-8') as file:
        objects = json.load(file)

    for obj in objects:
        if obj['manually_verified']:
            manually_verified_words.add(obj['word_de'])


data = []
for row in df.itertuples():
    ex_de = ast.literal_eval(row.examples)
    ex_bg = ast.literal_eval(row.examples_translations)
    if row.word in example_translations_fix:
        ex_bg = example_translations_fix[row.word].values()
    examples_list = []
    for de, bg in zip(ex_de, ex_bg):
        examples_list.append({'example_de': de, 'example_bg': bg})

    xword = row.word
    if row.word in word_translations_fix:
        xword = word_translations_fix[row.word]

    data.append(
        {
            'manually_verified': row.word in word_translations_fix,
            'word_de': row.word,
            'word_bg': xword,
            'examples': examples_list,
        }
    )


with open(POSTPROCESSED_WORDLIST_JSON_PATH, 'w', encoding='utf-8') as file:
    json.dump(data, file, ensure_ascii=False, indent=4)