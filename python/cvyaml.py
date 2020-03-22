
'''
Simple script to convert the yaml file into either json or an HTML table

Usage:
  cvyaml.py [--type=TYPE] INPUT

Options:
  --type=TYPE       output type, json or html [default: json]
'''

import yaml
import json
import sys
import html
from docopt import docopt


config = docopt(__doc__)

data = yaml.safe_load(open(config['INPUT'], 'r'))
if config['--type'] == 'json':
    json.dump(data, sys.stdout, indent=4)
    print()

elif config['--type'] == 'html':
    print('<table class="table table-striped">')
    for topic in data:
        print('<tr><th colspan=2>{}</th></tr>'.format(html.escape(topic['topic'])))
        for k,v in topic['indicators'].items():
            print('<tr><td>{0}</td><td><a href="https://data.worldbank.org/indicator/{0}">{1}</a></td></tr>'.format(k, html.escape(v)))

    print('</table>')

else:
    raise ValueError('Unknown output type: {}'.format(config['--type']))
