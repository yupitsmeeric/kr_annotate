import os
import json
from konlpy.tag import Kkma
from collections import Counter
import re
import sys
if len(sys.argv) < 2:
    print('please input text file name')
    sys.exit()
TEXT_FILE = sys.argv[1]

if not os.path.isfile( os.path.join('raw', TEXT_FILE) ):
    print('please input a valid file in the `raw folder`')
    sys.exit()

dict_path = 'kr_dict.json'
if not os.path.isfile(dict_path):
    from datapackage import Package
    package = Package('https://raw.githubusercontent.com/garfieldnate/kengdic/master/datapackage.json')
    resource = package.get_resource('kengdic')
    data = resource.read(keyed=True)
    data2 = new_list = [{k: v for k, v in d.items() if k != 'created'} for d in data]
    kr_dict = {x['surface']: x for x in data2}
    with open(dict_path, 'w', encoding="utf-8") as json_file:
        json.dump(kr_dict, json_file)
with open(dict_path, 'r', encoding="utf-8") as json_file:
    kr_dict = json.load(json_file)

# read text file
with open( os.path.join('raw', TEXT_FILE) , 'r', encoding='utf-8') as text_file:
    text_original = text_file.read()

kkma = Kkma()

def lemmatize_text(text):
    '''lemmatize text and count and sort'''
    korean_pattern = re.compile('[가-힣]+')
    # Find all Korean text using the pattern
    korean_text = ' '.join(korean_pattern.findall(text))
    
    text_processed = kkma.pos(korean_text, flatten = False)
    text_processed = [x[0] for x in text_processed] # take first morpheme only
    text_processed = [x[0] + '다'  if x[1][0]=='V' else x[0] for x in text_processed] # convert verbs to dictionary forms
    text_count = sorted(Counter(text_processed).items(), key=lambda x: x[1], reverse=True)

    return text_count

# text_count = Counter(text_raw)
    
# sorted_text = sorted(text_count.items(), key=lambda x: x[1], reverse=True)
lemmatized_text = lemmatize_text(text_original)

def dict_lookup(tup):
    res = {}
    lookup = kr_dict.get(tup[0],
                        {'gloss' : '', 'hanja' : '', 'surface' : ''})
    res['word'] = lookup['surface']
    res['gloss'] = lookup['gloss']
    res['hanja'] = lookup['hanja']
    res['freq'] = tup[1]
    return res

dictionary_text = [dict_lookup(x) for x in lemmatized_text]
# print(lemmatized_text)
# remove empty entries ie. entries where the 'surface' is empty or none
dictionary_text = [x for x in dictionary_text if x['word'] != '']

def create_tooltip(word):
    '''returns annotated word if possible. else return the original word'''
    # first check if there is an entry
    lemma = kkma.pos(word)
    if len(lemma) > 0:
        lemma_word = lemma[0][0]
        if lemma[0][1][0] == 'V': # if the tag starts with `V`, add '다' to the end
            lemma_word += '다'
        lookup = kr_dict.get(lemma_word)
    else:
        lookup = None
    
    if lookup: # if a dictionary entry exists, proceed to make the annotation
        # make tooltip content
        if lookup['gloss'] is not None:
            tooltip_content = lookup['surface'] + '; '
            tooltip_content += lookup['gloss'][:30]
            if len(lookup['gloss']) > 30:
                tooltip_content += '...'
        else:
            tooltip_content = ''

        # add hanja if available
        if lookup['hanja'] is not None:
            tooltip_content += '; ' + lookup['hanja']
#         print(tooltip_content)
        
        # now make the actual annotation tags
        span = f'<span class="tooltip"><span class="tooltiptext">{tooltip_content}</span>{word}</span>'
        return span

    else: # otherwise just return the word as is 
        return word


def annotate_text(text):
    lines = text.split('\n')
    new_lines = []
    for line in lines:
        # e/a line, process each word
        new_lines.append( ' '.join( [create_tooltip(word) for word in line.split(' ')] ) )
    res = '\n'.join(new_lines)
    return res

annotated_text = annotate_text(text_original)

# turn the list/dictionary into an html table
# Generate the HTML table
html_table = '''<!DOCTYPE html>
<html>
<head>
    <title>'''
    
html_table += os.path.splitext(TEXT_FILE)[0]
html_table +='''</title>
    <style>
        body {
            background-color: #f5e5d9; /* Sepia background color */
            font-size: 20px; /* Increase text size */
            text-align: center; /* Center text horizontally */
            color: #704214; /* Sepia text color */
        }
        table {
            border-collapse: collapse;
            margin-left: auto;
            margin-right: auto;

        }
        th, td {
            max-width: 450px;
            border: 1px solid black;
            padding: 8px;

        }
        th {
            background-color: #d7c9ad; /* Sepia header background color */
        }
        /* Tooltip container */
        .tooltip {
          position: relative;
          display: inline-block;
          border-bottom: 1px dotted gray; /* If you want dots under the hoverable text */
        }

        /* Tooltip text */
        .tooltip .tooltiptext {
          visibility: hidden;
          opacity: 0;
          min-width: 140px;
          max-width: 1000px;
          background-color: #2a2a2a;
          color: #ddd;
          text-align: center;
          padding: 5px 0;
          border-radius: 6px;
         
          /* Position the tooltip text - see examples below! */
          position: absolute;
          z-index: 1;
          bottom: 2rem;
          left:50%;
          transform: translate(-50%, 0);
        }

        /* Show the tooltip text when you mouse over the tooltip container */
        .tooltip:hover .tooltiptext {
          visibility: visible;
          opacity: 1;
          transition: opacity 0.18s ease;
        }
        
        .tooltip:hover {
          background-color: #556b2f;
          color: #dddddd;
        }
        
        
    </style>
</head>

<body>
'''

text_paras = [x for x in annotated_text.split("\n\n") if x != '']
text_paras = [x.replace('\n', '<br>') for x in text_paras]
text_paras = '\n'.join([f'<p>{x}</p>' for x in text_paras])
html_table += text_paras

html_table += '<table>'
# Create the table header row using dictionary keys
dict_keys = ['word', 'gloss', 'hanja', 'freq']
headers = ['단어', '의미', '漢字', '빈도']
# html_table += '<tr>' + ''.join(f'<th>{key}</th>' for key in dictionary_text[0].keys()) + '</tr>\n'
html_table += '<tr>' + ''.join(f'<th>{key}</th>' for key in headers) + '</tr>\n'


# Iterate through the list and create table rows
for data_dict in dictionary_text:
#     html_table += '<tr>' + ''.join(f'<td>{data_dict[key]}</td>' for key in data_dict.keys()) + '</tr>\n'
    html_table += '<tr>' + ''.join(f'<td>{data_dict[key]}</td>' for key in dict_keys) + '</tr>\n'

html_table += '''</table>
</body>
</html>
'''

html_path = os.path.join('annotated', TEXT_FILE.replace('.txt', '.html'))

with open(html_path, 'w', encoding='utf-8') as html_file:
    html_file.write(html_table)
    print('successfully written file')

