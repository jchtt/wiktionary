#! /usr/bin/env python2

# Strip html
from bs4 import BeautifulSoup

# Yaml parsing; make it fast by using the C routines
import yaml
from yaml import CLoader as Loader, CDumper as Dumper

# Regex
import re

from jc_utils import unique

# Roman numerals
import roman

# Timing
import time

import string
import codecs
import pattern.en as pat

def escape_characters(text):
    # table = {0xa: '\\n', 0x5c: '\\'}
    # return text.translate(table)
    # text = re.sub(r'\\', r'\\\\', text)
    text = re.sub(r'\n', r'<BR>', text)
    return text

def contract_tabs(text):
    return re.sub(r'\t\s*', r'\t', text)

def stripHtml(s):
    def escape_tags(text):
        """Transform special tags into character representation so they are preserved."""
        def repl_func(m):
            return '&lt;' + m.group(1) + m.group(2).upper() + '&gt;'
        # return re.sub(r'<(/{0,1})(i|b)(.*?)>', r'&lt;\1\2\3&gt;', text)
        # print(re.sub(r'<(/{0,1})(i|b|I|B)(.*?)>', repl_func, text))
        return re.sub(r'<(/{0,1})(i|b|I|B)(.*?)>', repl_func, text)

    def filter_newlines(text):
        """Replace newlines and surrounding whitespace by a single space."""
        return re.sub(r'(\s*\n\s*)+', r' ', text)

    s = escape_tags(s)
    soup = BeautifulSoup(s, 'lxml')
    # print(soup)

    # def escape_tags(soup):
    #     """Transform special tags into character representation so they are preserved."""
    #     print(soup)
    #     for tag in soup.find_all('b'):
    #         tag.string = '&lt;b&gt;' + tag.string + '&lt;/b&gt;'
    #     for tag in soup.find_all('i'):
    #         print(tag)
    #         print(tag.string)
    #         tag.string = '&lt;i&gt;' + tag.string + '&lt;/i&gt;'
    
    # Get rid of defdate
    def filter_tags1(tag):
        ret = False
        ret = ret or 'defdate' in tag.get('class', [])
        ret = ret or 'cited-source' in tag.get('class', [])
        ret = ret or tag.name == 'a' and tag.text.startswith('File:')
        return ret
    for tag in soup.find_all(filter_tags1):
        tag.decompose()

    # escape_tags(soup)
    r = soup.get_text().strip()
    r = escape_tags(r)
    # Do the soup thing twice, for good measure, to get rid of things like <ref> tags
    # This might need a more careful solution later when things actually contain <> characters
    soup = BeautifulSoup(r, 'lxml')
    def filter_tags2(tag):
        ret = False
        ret = ret or tag.name == 'ref'
        return ret
    for tag in soup.find_all(filter_tags2):
        tag.decompose()
    # escape_tags(soup)
    # r = filter_newlines(soup.get_text().strip())
    r = soup.get_text().strip()
    return r

def prep_string(string, lead = ' '):
    if not string:
        return ''
    else:
        return lead + string

def clean_synonyms(l):
    l = [re.sub(r'^Wikisaurus:', '', elem) for elem in l]
    return unique(l)

def assembleEntry(y):
    glosses = []
    examples = []
    etymologies = []
    quotations = []
    pronunciations = []
    pronunciation_entries = set();
    partsOfSpeech = []
    etymology_entries = set();
    synonyms = []
    wordForms = []

    # Preprocessing
    for entry in y.get('entries', []):
        # Parts of speech
        psos = entry.get('partsOfSpeech')
        if psos:
            partsOfSpeech.append(" ,".join(psos))
        else:
            partsOfSpeech.append("")

        # Synonyms
        synonyms.append(clean_synonyms(entry.get('synonyms', [])))

        # Pronunciations
        elems = []
        elem = ""
        for pronunciation in entry.get('pronunciations', []):
            text = pronunciation.get('text')
            if text:
                if text not in pronunciation_entries:
                    pronunciation_entries.add(text)
                    elem += text
                    note = pronunciation.get('note')
                    if note:
                        elem += " (" + note + ")"
                    elems.append(elem)
                    elem = ""
        pronunciations.append(", ".join(elems))

        # Senses
        gloss_entry = []
        example_entry = []
        quote_entry = []
        for sense in entry.get('senses', []):
            gloss_entry.append(stripHtml(sense.get('gloss', '')))
            example_entry.append([ stripHtml(example.get('example', '')) for example in sense.get('examples', [])])
            quote_entry.append([ stripHtml(quote.get('quote', '')) for quote in sense.get('quotations', [])])
        glosses.append(gloss_entry)
        examples.append(example_entry)
        quotations.append(quote_entry)

        etymology_text = stripHtml(entry.get('etymology', ''))
        if etymology_text not in etymology_entries:
            etymology_entries.add(etymology_text)
            etymologies.append(etymology_text)
        else:
            etymologies.append('')

    # Assemble string

    # Title
    s = u""
    # s += y['title'] + "\t"

    # Pronunciations
    entry_pronuncs = False
    # pronunciations_filtered = [text for entry in pronunciations for text in entry]
    pronunciations_filtered = list(filter(None, pronunciations))
    if len(pronunciations_filtered) == 1:
        s += u" " + pronunciations_filtered[0]
    else:
        entry_pronuncs = True

    # Glosses
    single_entry = len(glosses) == 1
    for (entry_num, entry_glosses) in enumerate(glosses, 1):
        if not single_entry:
            s += u" {0}.".format(roman.int_to_roman(entry_num))
        if entry_pronuncs:
            s += prep_string(pronunciations[entry_num - 1])
        s += prep_string(partsOfSpeech[entry_num - 1])
        single_gloss = len(entry_glosses) == 1
        for (gloss_num, gloss) in enumerate(entry_glosses, 1):
            if not single_gloss:
                s += u" {0:d}.".format(gloss_num)
            s += u" {0}".format(gloss)
        s += prep_string(", ".join(synonyms[entry_num - 1]) + u"." if synonyms[entry_num - 1] else "", " Synonyms: ")
        s += prep_string(etymologies[entry_num - 1], u" Etymology: ")

    # Examples and Quotes
    examples_flat = [example for entry in examples for examples in entry for example in examples if example]
    if examples_flat:
        s += u" Examples:"
        for (num_example, example) in enumerate(examples_flat, 1):
            if len(examples_flat) == 1:
                s += " " + example
            else:
                s += u" {0:d}. {1}".format(num_example, example)

    quotes_flat = [quote for entry in quotations for quotes in entry for quote in quotes if quote]
    if quotes_flat:
        s += u" Quotations:"
        for (num_quote, quote) in enumerate(quotes_flat, 1):
            if len(quotes_flat) == 1:
                s += u" " + quote
            else:
                s += u" {0:d}. {1}".format(num_quote, quote)

    s = escape_characters(s)
    s = y['title'] + "\n" + s.strip()

    # return escape_characters(contract_tabs(s))
    return s

## Main program 

now = time.time()

inDir = "/data/Development/Wiktionary/yaml-parsed/"
outDir = "/data/Development/Wiktionary/dict/"

inFile = inDir + "0064.yaml"
with codecs.open(inFile, mode = 'r', encoding = 'utf-8') as handle:
    content = handle.read()
y = yaml.load(content, Loader = Loader)
print(len(y))
parsed = ""
for page in y:
    parsed += assembleEntry(page) + '\n\n'

outFile = outDir + "0064.babylon"
with codecs.open(outFile, mode = 'w', encoding = 'utf-8') as handle:
    handle.write("\n#stripmethod=keep\n#sametypesequence=h\n\n")
    handle.write(parsed)

print(time.time()-now)
