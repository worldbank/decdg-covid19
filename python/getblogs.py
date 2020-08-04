
'''
getblogs.py: scrape the latest COVID-relevant blog posts from the open data blog

Usage:
  getblogs.py [--count=COUNT] [--format=FMT]

Options:
  --count=COUNT:        number of links to fetch, max of 10 [default: 4]

  --format=FMT:         yaml or json [default: yaml]
'''

from docopt import docopt
import requests
import yaml
import json
from pyquery import PyQuery
from datetime import datetime, timezone
from urllib.parse import urlparse, urlunparse

config = docopt(__doc__)

url = 'https://blogs.worldbank.org/search?f%5B0%5D=channel%3A4&f%5B1%5D=language%3Aen&f%5B2%5D=series%3A881'
p_url = urlparse(url)

response = requests.get(url)

doc = PyQuery(response.text)
posts = doc('div.views-element-container .listing')
links = []
for post in posts:
    link = PyQuery(post).find('h3 a').eq(0)
    title = link.text()
    url = urlparse(link.attr('href'))
    utc_date_str = PyQuery(post).find('time').attr('datetime')

    # simplest way I've found to convert UTC to local
    date = datetime.strptime(utc_date_str, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc).astimezone(tz=None)
    date = '{} {}'.format(date.strftime('%B'), date.day)

    # the HTML provides relative URLs so we need to provide the server name and scheme
    url = urlunparse(url._replace(netloc=p_url.netloc, scheme=p_url.scheme))

    links.append({'title': title, 'date': date, 'link': url})

    if len(links) >= int(config['--count']):
        break

if config['--format'] == 'yaml':
    # we format this as a dict to be compatible with the page header in index.md where this lives
    print(yaml.dump({'blogs': links}, width=150))
elif config['--format'] == 'json':
    print(json.dumps(links, indent=4))
else:
    raise ValueError('Unrecognized format: {}'.format(config['--format']))
