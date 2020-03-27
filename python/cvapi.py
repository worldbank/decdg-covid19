
'''
Read COVID-19 case data from HDX and store as a set of json files.

This can be used to provide a no-backend API if the files are saved
in the DocumentRoot of a server. For example:

http://some.host/all.json  # global data, plus manifest of other countries
http://some.host/CAN.json  # a specific country

Usage:
  cvapi.py [--source=SRC] TARGET_DIR

Options:
  --source=SRC     Source data: either hdx or csse (JHU github) [default: csse]

'''

import requests
import pandas as pd
import numpy as np
from wbgapi.economy import coder
from datetime import datetime
from github import Github
import os
import json
from docopt import docopt

options = docopt(__doc__)

config = {
  'build_date': datetime.strftime(datetime.utcnow(), '%Y-%m-%dT%H:%M:%S'),
  'build_dir': options['TARGET_DIR'],
}

def hdx_refs():

    url = 'https://data.humdata.org/api/3/action/package_show?id=novel-coronavirus-2019-ncov-cases'
    ckan = requests.get(url).json()['result']
    last_modified = datetime.strptime(ckan['metadata_modified'], '%Y-%m-%dT%H:%M:%S.%f')
    c, d, r = map(lambda x: x['url'], ckan['resources'][0:3])
    return c, d, r, last_modified

def csse_refs():

    try:
        git_token = os.environ['GITHUB_ANONYMOUS_TOKEN']
    except KeyError:
        raise OSError('GITHUB_ANONYMOUS_TOKEN must be defined as a valid access token in your environment')

    git = Github(git_token)
    repo = git.get_repo('CSSEGISandData/COVID-19')
    c_url, d_url, r_url = map(lambda x: 'csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_{}_global.csv'.format(x), ['confirmed', 'deaths', 'recovered'])
    c = repo.get_contents(c_url)
    d = repo.get_contents(d_url)
    r = repo.get_contents(r_url)
    
    # get the modification date from the latest commit for the confirmed case file
    last_modified = repo.get_commits(path=c_url)[0].last_modified
    last_modified = datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S %Z')    # assumes this is GMT, b/c strptime actually ignores the timezone. Else use dateutils.parser

    return c.download_url, d.download_url, r.download_url, last_modified


def to_json(c, d, r, **kwargs):
    global config

    data = {
        'meta': {
            'build_date': config['build_date'],
            'update_date': config['update_date'],
        },
        'data': []
    }

    data['meta'].update(kwargs)

    for i in c.index:
        ts = datetime.strptime(i, '%m/%d/%y')   # e.g., 3/12/20
        key = datetime.strftime(ts, '%Y/%m/%d')

        row = {'date': key, 'confirmed': int(np.nan_to_num(c[i])), 'deaths': int(np.nan_to_num(d[i]))}
        if r is None:
            row['recovered'] = None
        else:
            row['recovered'] = int(np.nan_to_num(r[i]))

        data['data'].append(row)

    return data

if options['--source'] == 'hdx':
    confirmed_url, deaths_url, recovery_url, last_modified = hdx_refs()
elif options['--source'] == 'csse':
    confirmed_url, deaths_url, recovery_url, last_modified = csse_refs()
else:
    raise ValueError('Unrecognized --source: {}'.format(options['--source']))

config['update_date'] = datetime.strftime(last_modified, '%Y-%m-%dT%H:%M:%S')

manifest = {'world': {'name': 'World', 'locales': []}}
c = pd.read_csv(confirmed_url).replace(0, np.nan).dropna(how='all', axis=1)
d = pd.read_csv(deaths_url).replace(0, np.nan).dropna(how='all', axis=1)

date_columns = list(filter(lambda x: x not in ['Lat', 'Long', 'Province/State', 'Country/Region'], c.columns))

# this is the file name for subnational estimates
c['stp_key'] = c['Province/State'].fillna('').str.replace(r'\W','').str.upper()

# c, d & r aren't always in the same order, so we need to create a common index
c['geokey'] = c['Province/State'].fillna('_') + ':' + c['Country/Region'].fillna('_')
d['geokey'] = d['Province/State'].fillna('_') + ':' + d['Country/Region'].fillna('_')

c.set_index('geokey', inplace=True)
d.set_index('geokey', inplace=True)

# aggregate by country
prov_count = c.groupby('Country/Region')[['Province/State']].count()
lat_long   = c.groupby('Country/Region')[['Lat', 'Long']].min()

c2 = c.groupby('Country/Region').sum()[date_columns]
d2 = d.groupby('Country/Region').sum()[date_columns]

if recovery_url:
    r = pd.read_csv(recovery_url).replace(0, np.nan).dropna(how='all', axis=1)
    r['geokey'] = r['Province/State'].fillna('_') + ':' + r['Country/Region'].fillna('_')
    r.set_index('geokey', inplace=True)
    r2 = r.groupby('Country/Region').sum()[date_columns]
else:
    r = None
    r2 = None

data = to_json(c.sum()[date_columns], d.sum()[date_columns], None if r is None else r.sum()[date_columns], iso='WLD', name='World')
with open(os.path.join(config['build_dir'], 'world.json'), 'w') as fd:
    json.dump(data, fd)


for key in c2.index:
    iso = coder(key)
    if iso:
        manifest[iso] = {'name': key, 'locales': []}
        with open(os.path.join(config['build_dir'], iso + '.json'), 'w') as fd:
            meta = dict(iso=iso, name=key)
            if prov_count.loc[key]['Province/State'] == 0:
                meta['lon'] = lat_long.loc[key]['Long']
                meta['lat'] = lat_long.loc[key]['Lat']

            data = to_json(c2.loc[key], d2.loc[key], None if r2 is None else r2.loc[key], **meta)
            json.dump(data, fd)

# now write subnational data
for key in c.dropna(subset=['Province/State']).index:
    row = c.loc[key]
    iso = coder(row['Country/Region'])

    # we skip rows where the latest day is empty. This eliminates county-level records
    # in the US where a handful of cases were recorded but later counted at the state level
    if iso and not np.isnan(row[date_columns[-1]]):
        manifest[iso]['locales'].append(os.path.join(iso, row['stp_key']))

        try:
            os.mkdir(os.path.join(config['build_dir'], iso))
        except:
            pass

        with open(os.path.join(config['build_dir'], iso, row['stp_key'] + '.json'), 'w') as fd:
            data = to_json(c.loc[key][date_columns], d.loc[key][date_columns], None if (r is None or key not in r.index) else r.loc[key][date_columns], iso=iso, name=row['Province/State'], lat=row['Lat'], lon=row['Long'])
            json.dump(data, fd)

with open(os.path.join(config['build_dir'], 'manifest.json'), 'w') as fd:
    json.dump(manifest, fd)

# Write an HTML file too
with open(os.path.join(config['build_dir'], 'index.html'), 'w') as fd:
    print('<!DOCTYPE html>', file=fd)
    print('<html>\n<head><title>{}</title>\n</head>'.format('API Documentation'), file=fd)
    print('<body>', file=fd)
    print('<p>This list in <a href="manifest.json">json format</a></p>', file=fd)

    print('<ul>', file=fd)
    for k,v in manifest.items():
        print('<li><a href="{}.json">{}</a>'.format(k, v['name']), end='', file=fd)
        if len(v['locales']) > 0:
            print('\n  <ul>', file=fd)
            for elem in v['locales']:
                print('  <li><a href="{0}.json">{0}</a></li>'.format(elem), file=fd)

            print('  </ul></li>', file=fd)
        else:
            print('', file=fd)
    
    print('</ul>\n</body>\n</html>', file=fd)
