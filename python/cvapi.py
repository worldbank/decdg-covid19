
'''
Read COVID-19 case data from HDX and store as a set of json files.

This can be used to provide a no-backend API if the files are saved
in the DocumentRoot of a server. For example:

http://some.host/all.json  # global data, plus manifest of other countries
http://some.host/CAN.json  # a specific country

Usage:
  cvapi.py TARGET_DIR

'''

import requests
import pandas as pd
from wbgapi.economy import coder
from datetime import datetime
import os
import json
from docopt import docopt

options = docopt(__doc__)

config = {
  'hdx_url': 'https://data.humdata.org/api/3/action/package_show?id=novel-coronavirus-2019-ncov-cases',
  'build_date': datetime.strftime(datetime.now(), '%Y-%m-%dT%H:%M:%S'),
  'build_dir': options['TARGET_DIR'],
}

def to_json(name, key, c, d, r):
    global config

    data = {
        'meta': {
            'build_date': config['build_date'],
            'update_date': config['update_date'],
            'iso': key,
            'name': name,
        },
        'data': []
    }

    for i in c.index:
        ts = datetime.strptime(i, '%m/%d/%y')   # e.g., 3/12/20

        confirmed, deaths, recovered = int(c[i]), int(d[i]), int(r[i])
        key = datetime.strftime(ts, '%Y/%m/%d')
        data['data'].append({'date': key, 'confirmed': confirmed, 'deaths': deaths, 'recovered': recovered})

    return data

# get the latest data resource links
response = requests.get(config['hdx_url'])
ckan = response.json()
meta_mod = datetime.strptime(ckan['result']['metadata_modified'], '%Y-%m-%dT%H:%M:%S.%f')

config['update_date'] = datetime.strftime(meta_mod, '%Y-%m-%dT%H:%M:%S')

# assume that Confirmed, Deaths, and Recoveries are the 1st-3rd datasets
confirmed_url, deaths_url, recovery_url = map(lambda x: x['url'], ckan['result']['resources'][0:3])

c_ = pd.read_csv(confirmed_url)
d_ = pd.read_csv(deaths_url)
r_ = pd.read_csv(recovery_url)

# aggregate and transform so dates are rows
drop_columns = ['Province/State', 'Lat', 'Long']
c = c_.drop(columns=drop_columns).dropna(how='all', axis=1).groupby('Country/Region').sum().transpose()
d = d_.drop(columns=drop_columns).dropna(how='all', axis=1).groupby('Country/Region').sum().transpose()
r = r_.drop(columns=drop_columns).dropna(how='all', axis=1).groupby('Country/Region').sum().transpose()

keys = []
for key in c.columns:
    iso = coder(key)
    if iso:
        keys.append(iso)
        with open(os.path.join(config['build_dir'], iso + '.json'), 'w') as fd:
            data = to_json(key, iso, c[key], d[key], r[key])
            json.dump(data, fd)


data = to_json('World', 'WLD', c.sum(axis=1), d.sum(axis=1), r.sum(axis=1))
data['meta']['countries'] = keys
with open(os.path.join(config['build_dir'], 'all.json'), 'w') as fd:
    json.dump(data, fd)
