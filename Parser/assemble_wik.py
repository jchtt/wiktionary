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
import pattern.en as en

import multiprocessing as multip
import os
import signal
import glob

from tqdm import tqdm

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

def replace_newlines(text):
    return re.sub(r'\n', r'/', text)

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
    partsOfSpeechHeads = []
    etymology_entries = set();
    synonyms = []
    word_forms = []

    # Preprocessing
    for entry in y.get('entries', []):
        # Parts of speech
        psos = entry.get('partsOfSpeech') or []
        try:
            psos = map(lambda x: x.replace('proper_noun', 'proper noun'), psos)
        except:
            print(repr(psos))
            print(y['title'])
            raise
        if psos:
            partsOfSpeech.append(u"<B>" + u" ,".join(psos) + u"</B>")
            partsOfSpeechHeads.append(psos[0])
        else:
            partsOfSpeech.append("")
            partsOfSpeechHeads.append("")

        # Word forms
        elems = []
        for wf in entry.get('wordForms') or []:
            form = wf.get('form')
            if form:
                elems.append(form)
        word_forms.append(elems)

        # Synonyms
        synonyms.append(clean_synonyms(entry.get('synonyms', [])))

        # Pronunciations
        elems = []
        elem = ""
        # print(entry.get('pronunciations', []))
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
        # print(repr(pronunciations[-1]))

        # Senses
        gloss_entry = []
        example_entry = []
        quote_entry = []
        for sense in entry.get('senses') or []:
            gloss_entry.append(stripHtml(sense.get('gloss', '')))
            example_entry.append([ replace_newlines(stripHtml(example.get('example', ''))) for example in sense.get('examples', [])])
            quote_entry.append([ replace_newlines(stripHtml(quote.get('quote', ''))) for quote in sense.get('quotations', [])])
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
        s += u" " + pronunciations_filtered[0] + "<BR>"
    else:
        entry_pronuncs = True

    # Entries & glosses
    single_entry = len(glosses) == 1
    for (entry_num, entry_glosses) in enumerate(glosses, 1):
        if entry_num >= 2:
            s += "<BR>"
        if not single_entry:
            s +=u"{0}. ".format(roman.int_to_roman(entry_num))
        if entry_pronuncs:
            s += prep_string(pronunciations[entry_num - 1])
        s += partsOfSpeech[entry_num - 1]

        # Handle word forms
        pos = partsOfSpeechHeads[entry_num - 1]
        word = y['title']
        if pos == "verb":
            p = en.conjugate(word, 'p')
            pp = en.conjugate(word, 'ppart')
            if p != word + 'ed' or pp != word + 'ed':
                s += u" (p. " + p + u", pp. " + pp + u")"
        elif pos == "noun":
            pl = en.pluralize(word)
            if pl != word + u's':
                s += u" (pl. " + pl + ")"
        elif pos == "adjective":
            pass

        # Glosses
        single_gloss = len(entry_glosses) == 1
        for (gloss_num, gloss) in enumerate(entry_glosses, 1):
            if not single_gloss:
                s += u" {0:d}.".format(gloss_num)
            # else:
            #     s += u":"
            s += u" {0}".format(gloss)
        s += prep_string(", ".join(synonyms[entry_num - 1]) + u"." if synonyms[entry_num - 1] else "", " Synonyms: ")
        s += prep_string(etymologies[entry_num - 1], u" Etymology: ")

    # Examples and Quotes
    examples_flat = [example for entry in examples for examples in entry for example in examples if example]
    if examples_flat:
        s += u"<BR><B>Examples:</B>"
        for (num_example, example) in enumerate(examples_flat, 1):
            if len(examples_flat) == 1:
                s += " " + example
            else:
                s += u" {0:d}. {1}".format(num_example, example)

    quotes_flat = [quote for entry in quotations for quotes in entry for quote in quotes if quote]
    if quotes_flat:
        s += u"<BR><B>Quotations:</B>"
        for (num_quote, quote) in enumerate(quotes_flat, 1):
            if len(quotes_flat) == 1:
                s += u" " + quote
            else:
                s += u" {0:d}. {1}".format(num_quote, quote)

    s = escape_characters(s)

    word_forms_flat = [form for entry in word_forms for form in entry if form]
    titles = [y['title']]
    titles.extend(word_forms_flat)
    if 'verb' in partsOfSpeechHeads:
        titles.extend(en.lexeme(y['title']))
    if 'noun' in partsOfSpeechHeads:
        titles.append(en.pluralize(y['title']))
    if 'adjective' in partsOfSpeechHeads:
        adj_forms = [en.comparative(y['title']), en.superlative(y['title'])]
        adj_forms = [form for form in adj_forms if len(form.split(' ')) == 1]
        titles.extend(adj_forms)
    titles = unique(titles)
    if s.strip() == "":
        s = "Empty article."
    s = u'|'.join(titles) + u"\n" + s.strip()

    # return escape_characters(contract_tabs(s))
    return s

def assembleHelper(work_q, done_q):
    signal.signal(signal.SIGINT, signal.SIG_IGN)
    try:
        for args in iter(work_q.get, 'STOP'):
            number = args[0]
            inFile = args[1]
            outFile = args[2]
            # print inFile
            # print outFile
        
            with codecs.open(inFile, mode = 'r', encoding = 'utf-8') as handle:
                content = handle.read()
            y = yaml.load(content, Loader = Loader)
            # print(len(y))
            parsed = ""
            for page in y:
                parsed += assembleEntry(page) + '\n\n'
            
            with codecs.open(outFile, mode = 'w', encoding = 'utf-8') as handle:
                # handle.write("\n#stripmethod=keep\n#sametypesequence=h\n\n")
                handle.write(parsed)
    
            done_q.put(number)
            # print('done')
    except:
        print('Error in job {:d}'.format(number))
        emptyQueue(work_q)
        raise

def pbarHelper(work_q, done_q, pbar):
    state = 'START'
    while state != 'STOP':
        state = done_q.get()
        if state == 'STOP':
            pbar.close()
        else:
            pbar.update(1)

def emptyQueue(q):
    for a in iter(q.get, 'STOP'):
        pass
    q.put('STOP')
    print('emptied')

## Main program 

now = time.time()

inDir = "/data/Development/Wiktionary/yaml-parsed/"
outDir = "/data/Development/Wiktionary/dict/"

nprocs = 4
pad = 4

in_numbers = sorted([int(os.path.splitext(f)[0]) for f in os.listdir(inDir)])
out_numbers = sorted([int(os.path.splitext(os.path.basename(f))[0]) for f in glob.glob(os.path.join(outDir,'*.babylon'))])
new_numbers = sorted(set(in_numbers).difference(out_numbers))
# numbers = [int(os.path.splitext(f)[0]) for f in new_files]

in_files = map(lambda x: os.path.join(inDir, str(x).zfill(pad) + ".yaml"), new_numbers)
out_files = map(lambda x: os.path.join(outDir, str(x).zfill(pad) + ".babylon"), new_numbers)

inputs = list(zip(new_numbers, in_files, out_files))
counter = 0

# Multiprocessing handling
work_q = multip.Queue()
done_q = multip.Queue()
for task in inputs:
    work_q.put(task)

pbar = tqdm(total = len(in_numbers), leave = True, initial = len(out_numbers), smoothing = 0.05)

procs = []
for i in xrange(nprocs):
    p = multip.Process(target = assembleHelper, args = (work_q, done_q))
    p.start()
    procs.append(p)
    work_q.put('STOP')

pbarProc = multip.Process(target = pbarHelper, args = (work_q, done_q, pbar))
pbarProc.start()

for p in procs:
    try:
        p.join()
    except:
        emptyQueue(work_q)
        # p_empty = multip.Process(target = emptyQueue, args = (work_q,))
        # p_empty.join()
        for p in procs:
            p.join()
        pbarProc.join()
        raise

done_q.put('STOP')
pbarProc.join()

# inFile = inDir + "0627.yaml"
# with codecs.open(inFile, mode = 'r', encoding = 'utf-8') as handle:
#     content = handle.read()
# y = yaml.load(content, Loader = Loader)
# print(len(y))
# parsed = ""
# for page in y:
#     parsed += assembleEntry(page) + '\n\n'

# outFile = outDir + "0627.babylon"
# with codecs.open(outFile, mode = 'w', encoding = 'utf-8') as handle:
#     handle.write("\n#stripmethod=keep\n#sametypesequence=h\n\n")
#     handle.write(parsed)

# print(time.time()-now)

# assembleHelper((627, inFile, outFile))

# p = multip.Pool(nprocs)
# try:
#     p.map(assembleHelper, inputs)
# except:
#     p.close()
