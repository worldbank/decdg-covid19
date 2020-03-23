
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

ntable_columns = 3

data = yaml.safe_load(open(config['INPUT'], 'r'))
if config['--type'] == 'json':
    json.dump(data, sys.stdout, indent=2)
    print()

elif config['--type'] == 'html':
    print('<table class="table table-striped table-indicators">')
    for topic in data:
        print('<tr><th colspan={}>{}</th></tr>'.format(ntable_columns, html.escape(topic['topic'])))
        for k,v in topic['indicators'].items():
            # print('<tr><td>{0}</td><td><a href="https://data.worldbank.org/indicator/{0}">{1}</a></td></tr>'.format(k, html.escape(v)))
            # print('<tr><td><a href="https://data.worldbank.org/indicator/{0}">{1}</a></td></tr>'.format(k, html.escape(v)))
            cells = [
              html.escape(v),
              '<a href="https://data.worldbank.org/indicator/{}">View</a>'.format(k),
              '<a href="https://api.worldbank.org/v2/en/country/all/indicator/{}?source=2&format=json">API</a>'.format(k),
            ]
            print('<tr>' + ''.join(map(lambda x: '<td>{}</td>'.format(x), cells)) + '</tr>')

    print('</table>')

else:
    raise ValueError('Unknown output type: {}'.format(config['--type']))
