#! /usr/bin/env python

import requests
import re
# import json
import yaml
from yaml import CLoader as Loader, CDumper as Dumper
from bs4 import BeautifulSoup
from itertools import repeat
import os

# Parallelization
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, as_completed, wait
from concurrent.futures._base import CancelledError

# Progress bar
from tqdm import tqdm

# timing
import time

# apiLink = 'https://en.wiktionary.org/w/api.php'
apiLink = 'http://localhost/mediawiki/api.php'

citePattern = r"\s*\*\s*\{\{seeCites\}\}|\{\{rfdate\}\},?.*\n|\{\{RQ:.*\}\}.*\n|\{\{rfquotek\|.*?\}\}|^.*\(\d{4}\-\d{4}\)\n"

def filter_wikitext(s):
    s = re.sub(citePattern, "", s, flags = re.MULTILINE)
    return s

def parse_wikitext(s):
    s = filter_wikitext(s)
    values = { "disablelimitreport" : "true", "action" : "parse", "format" : "json", "contentmodel" : "wikitext", "text" : s }
    r = requests.post(apiLink, data=values)

    # TODO: needs some error handling here
    # print(r.text)
    return r.json()["parse"]["text"]["*"]
    # return r.json()
    # return r

class translation_table:
    def __getitem__(self, ordinal):
        if ordinal >= 65535:
            return "\u25AF"
        else:
            return ordinal

def parse_yaml_files(files):
    try:
        default_max_queries = 10
    
        if type(files) is not list:
            files = [files]
    
        for input_tuple in files:
            # print(input_tuple)
            job_id = input_tuple[0]
            infile_name = input_tuple[1]
            outfile_name = input_tuple[2]
            if len(input_tuple) == 3:
                opts = {}
            else:
                opts = input_tuple[3]
    
            # Load infile_name, make safe and translate to yaml
            with open(infile_name, 'r') as handle:
                content = handle.read()
            
            content = content.translate(translation_table())
            y = yaml.load(content, Loader = Loader)
    
            # Prepare query_strings to give to the Wiktionary instance
            query_strings = []
            query_string = ""
    
            counter = 0 # Counter for building small query chunks
            # Maximum number of queries in one chunk
            max_queries = opts.get('max_queries') or default_max_queries
            max_calls = 0 # Max number of total calls (not used)
            id_counter = 0 # Identify chunks back with this number
            fill_list = [] # Save links to map things back when we are done
            
            # Prepare the query strings
            for page in y:
                for entry in page.get("entries") or []:
                    if entry.get("etymology") is not None:
                        query_string += "= " + str(id_counter) + " =\n"
                        query_string += entry["etymology"]
                        fill_list.append((entry, "etymology"))
                        id_counter += 1
                    for sense in entry.get("senses") or []:
                        if sense.get("gloss") is not None:
                            query_string += "= " + str(id_counter) + " =\n"
                            query_string += sense["gloss"]
                            fill_list.append((sense, "gloss"))
                            id_counter += 1
                        for example in sense.get("examples") or []:
                            query_string += "= " + str(id_counter) + " =\n"
                            query_string += example['example']
                            fill_list.append((example, "example"))
                            id_counter += 1
                        for quote in sense.get("quotations") or []:
                            if quote.get("quote") is not None:
                                query_string += "= " + str(id_counter) + " =\n"
                                query_string += quote["quote"]                    
                                fill_list.append((quote, "quote"))
                                id_counter += 1
                if max_queries > 0 and counter >= max_queries:
                    # Append and reset counter
                    query_strings.append(query_string)
                    counter = 0
                    query_string = ""
                else:
                    counter += 1
                if max_calls > 0 and len(query_strings) >= max_calls:
                    break
    
            # Append last string
            query_strings.append(query_string)
    
            counter = 0
            now = time.time()
            for s in query_strings:
                # print(counter)
                # print(len(s))
            
                parsed = parse_wikitext(s)
                # print(parsed)
    
                # Map elements back, identified by their id, by iterating over the html nodes
                # with soup
                soup = BeautifulSoup(parsed, 'lxml')
                elem = soup.h1
                if elem is not None:
                    soup_exhausted = False
                else:
                    soup_exhausted = True
            
                while not soup_exhausted:
                    id_counter = int(elem.span['id'])
                    new_h1 = False
                    result_str = ""
                    while not new_h1 and not soup_exhausted:
                        if elem.next_sibling is not None:
                            elem = elem.next_sibling
                            if elem.name == 'h1':
                                new_h1 = True
                            else:
                                result_str += str(elem)
                        else:
                            soup_exhausted = True
             
                    fill_list[id_counter][0][fill_list[id_counter][1]] = result_str
    
                counter += 1
            
            # print((time.time()-now)/60)
            
            # Dump yaml file back
            with open(outfile_name, 'w') as handle:
                handle.write(yaml.dump(y, Dumper = Dumper))
    
            # print("Done with {:d}".format(job_id))
            return job_id

    except Exception as e:
        print('Exception when parsing file: ' + infile_name)
        raise

## Main program 

inDir = "/data/Development/Wiktionary/yaml/"
outDir = "/data/Development/Wiktionary/yaml-parsed/"
nprocs = 4
pad = 4

in_contents = sorted(os.listdir(inDir))
out_contents = sorted(os.listdir(outDir))
new_files = sorted(set(in_contents).difference(out_contents))
numbers = [int(os.path.splitext(f)[0]) for f in new_files]

in_files = map(lambda x: os.path.join(inDir, str(x).zfill(pad) + ".yaml"), numbers)
out_files = map(lambda x: os.path.join(outDir, str(x).zfill(pad) + ".yaml"), numbers)

opts = {'max_queries' : 10}

inputs = list(zip(numbers, in_files, out_files, repeat(opts)))
counter = 0

# Progress bar
pbar = tqdm(total = len(in_contents), leave = True, initial = len(out_contents))

now = time.time()
executor = ThreadPoolExecutor(nprocs)
# with ThreadPoolExecutor(nprocs) as executor:
# for future in as_completed(map(lambda x: executor.submit(parse_yaml_files, x), inputs)):
#     future.result()
futures = [executor.submit(parse_yaml_files, input_elem) for input_elem in inputs]
try:
    for (file_num, future) in zip(numbers, as_completed(futures)):
        # print('Querying result')
        if future.exception():
            print('Exception in file {:d}!'.format(file_num))
            print(type(future.exception()))
            raise future.exception()
        res = future.result()
        # print('Done.')
        pbar.update(1)
        counter += 1
        # if counter >= 1:
        #     print("Trying to shutdown...")
        #     executor.shutdown(False)
        #     break
except:
    print("An error occurred, trying to finish gracefully...")
    for future in futures:
        future.cancel()
    # completed_futures = [future.result() for future in as_completed(wait(futures)[0])]
    completed_futures = [future.result() for future in as_completed(futures) if not future.cancelled()]
    print("Last completed job_id: {:d}.".format(max(completed_futures)))
    raise
finally:
    executor.shutdown()

print('Out of the loop')
pbar.close()

print("Total execution time with {:d} processes, threads: {:.2f} min".format(nprocs, (time.time() - now)/60))

# now = time.time()
# with ProcessPoolExecutor(nprocs) as executor:
#     # for future in as_completed(executor.submit(parse_yaml_files, inputs)):
#     #     future.result()
#     for result in executor.map(parse_yaml_files, inputs):
#         pass
# print("Total execution time with {:d} processes, processes: {:.2f} min".format(nprocs, (time.time() - now)/60))
