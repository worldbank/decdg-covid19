
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

def safe_cast(value, to_type=int, default=None):

    try:
        return to_type(value)
    except (ValueError, TypeError):
        return default
       

def hdx_refs():

    url = 'https://data.humdata.org/api/3/action/package_show?id=novel-coronavirus-2019-ncov-cases'
    ckan = requests.get(url).json()['result']
    last_modified = datetime.strptime(ckan['metadata_modified'], '%Y-%m-%dT%H:%M:%S.%f')
    c, d, r = map(lambda x: x['url'], ckan['resources'][0:3])
    return c, d, r, last_modified

def csse_refs(locale='global'):

    try:
        git_token = os.environ['GITHUB_ANONYMOUS_TOKEN']
    except KeyError:
        raise OSError('GITHUB_ANONYMOUS_TOKEN must be defined as a valid access token in your environment')

    git = Github(git_token)
    repo = git.get_repo('CSSEGISandData/COVID-19')

    # we can't use get_contents to fetch large files directly, so we have to iterate over the directory to get their raw
    # URLs. See https://medium.com/@caludio/how-to-download-large-files-from-github-4863a2dbba3b
    if locale == 'global':
        c_url, d_url, r_url = map(lambda x: 'csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_{}_global.csv'.format(x), ['confirmed', 'deaths', 'recovered'])
        for elem in repo.get_contents('csse_covid_19_data/csse_covid_19_time_series'):
            if elem.path == c_url:
                c = elem
            elif elem.path == d_url:
                d = elem
            elif elem.path == r_url:
                r = elem

        c_path, d_path, r_path = c.download_url, d.download_url, r.download_url
        
    elif locale == 'usa':
        c_url, d_url = map(lambda x: 'csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_{}_US.csv'.format(x), ['confirmed', 'deaths'])
        for elem in repo.get_contents('csse_covid_19_data/csse_covid_19_time_series'):
            if elem.path == c_url:
                c = elem
            elif elem.path == d_url:
                d = elem

        c_path, d_path, r_path = c.download_url, d.download_url, None

    # get the modification date from the latest commit for the confirmed case file
    last_modified = repo.get_commits(path=c_url)[0].last_modified
    last_modified = datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S %Z')    # assumes this is GMT, b/c strptime actually ignores the timezone. Else use dateutils.parser

    return c_path, d_path, r_path, last_modified


def get_date_columns(df):

    return list(filter(lambda x: len(x.split('/')) == 3, df.columns))

def get_covid_frame(url, admin2=False):

    # df = pd.read_csv(url).replace(0, np.nan)
    df = pd.read_csv(url)
    df.rename(columns={'Province_State': 'Province/State', 'Country_Region': 'Country/Region', 'Long_': 'Long'}, inplace=True)
    if admin2:
        df['stp_key'] = df['Admin2'].fillna('').str.replace(r'\W','').str.upper()
        df['geokey'] = df['Province/State'].fillna('_') + ':' + df['Country/Region'].fillna('_') + ':' + df['Admin2'].fillna('_')
    else:
        df['stp_key'] = df['Province/State'].fillna('').str.replace(r'\W','').str.upper()
        df['geokey'] = df['Province/State'].fillna('_') + ':' + df['Country/Region'].fillna('_')

    df.set_index('geokey', inplace=True)
    dates = get_date_columns(df)
    df[dates] = df[dates].replace(-1, np.nan) # this seems to be used as a missing value in the cruise ship data for Canada

    return df

def get_basic_data(level):
    ''' Fetches background data at the country, usstate or uccty level
    '''

    url = 'https://raw.githubusercontent.com/tgherzog/basicdata/master/data/{}.' + level + '.csv'

    pop = pd.read_csv(url.format('pop'), dtype=str).set_index('id')
    pop['population'] = pop.population.astype('int')

    area = pd.read_csv(url.format('area'), dtype=str).set_index('id')[['land_area']]
    area['land_area'] = area.land_area.astype('int')

    cen  = pd.read_csv(url.format('centroid'), dtype=str).set_index('id')[['lat', 'long']]
    cen[['lat', 'long']] = cen[['lat', 'long']].astype('float')

    return pop.join(area).join(cen)


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

        row = {'date': key, 'confirmed': safe_cast(c[i]), 'deaths': safe_cast(d[i])}
        if r is None:
            row['recovered'] = None
        else:
            row['recovered'] = safe_cast(r[i])

        data['data'].append(row)

    return data

if options['--source'] == 'hdx':
    raise ValueError('hdx mode is no longer supported')
    confirmed_url, deaths_url, recovery_url, last_modified = hdx_refs()
elif options['--source'] == 'csse':
    confirmed_url, deaths_url, recovery_url, last_modified = csse_refs()
else:
    raise ValueError('Unrecognized --source: {}'.format(options['--source']))

config['update_date'] = datetime.strftime(last_modified, '%Y-%m-%dT%H:%M:%S')

manifest = {'world': {'name': 'World', 'locales': []}}
c = get_covid_frame(confirmed_url)
d = get_covid_frame(deaths_url)

# date columns are those that look like */*/*
date_columns = get_date_columns(c)

# fetch background data
bg0 = get_basic_data('country')
bg1 = get_basic_data('usstate').reset_index().set_index('name')
bg2 = get_basic_data('uscty')

# aggregate by country
c2 = c.groupby('Country/Region').sum()[date_columns]
d2 = d.groupby('Country/Region').sum()[date_columns]

if recovery_url:
    r = get_covid_frame(recovery_url)
    r2 = r.groupby('Country/Region').sum()[date_columns]
else:
    r = None
    r2 = None

data = to_json(c.sum()[date_columns], d.sum()[date_columns], None if r is None else r.sum()[date_columns],
        iso='WLD', name='World', display_name='World', population=safe_cast(bg0['population'].get('WLD')), land_area=safe_cast(bg0['land_area'].get('WLD')))
with open(os.path.join(config['build_dir'], 'world.json'), 'w') as fd:
    json.dump(data, fd)


for key, row in c2.iterrows():
    iso = coder(key)
    if iso:
        manifest[iso] = {'name': key, 'locales': []}
        with open(os.path.join(config['build_dir'], iso + '.json'), 'w') as fd:
            data = to_json(c2.loc[key], d2.loc[key], None if r2 is None else r2.loc[key],
                     iso=iso, name=key, display_name=key, lat=bg0['lat'].get(iso), long=bg0['long'].get(iso),
                     population=safe_cast(bg0['population'].get(iso)), land_area=safe_cast(bg0['land_area'].get(iso)))
            json.dump(data, fd)

# now write subnational data
for key,row in c.dropna(subset=['Province/State']).iterrows():
    iso = coder(row['Country/Region'])

    if iso:
        manifest[iso]['locales'].append(os.path.join(iso, row['stp_key']))

        try:
            os.mkdir(os.path.join(config['build_dir'], iso))
        except:
            pass

        with open(os.path.join(config['build_dir'], iso, row['stp_key'] + '.json'), 'w') as fd:
            data = to_json(c.loc[key][date_columns], d.loc[key][date_columns], None if (r is None or key not in r.index) else r.loc[key][date_columns],
                     iso=iso, name=row['Province/State'], display_name='{}, {}'.format(row['Province/State'], row['Country/Region']), lat=row['Lat'], lon=row['Long'])
            json.dump(data, fd)

# subnational US data is stored separately at the county level
confirmed_url, deaths_url, recovery_url, last_modified = csse_refs(locale='usa')
config['update_date'] = datetime.strftime(last_modified, '%Y-%m-%dT%H:%M:%S')

c = get_covid_frame(confirmed_url, True)
d = get_covid_frame(deaths_url, True)
r = r2 = None

c['FIPS'] = c['FIPS'].map(lambda x: '{:05d}'.format(int(np.nan_to_num(x))))
d['FIPS'] = d['FIPS'].map(lambda x: '{:05d}'.format(int(np.nan_to_num(x))))

c2 = c.groupby('Province/State').sum().sort_index()
d2 = d.groupby('Province/State').sum().sort_index()
c2['stp_key'] = c2.index.map(lambda x: bg1['code'].get(x))

iso = 'USA'
manifest[iso]['admin2'] = {}
try:
    os.mkdir(os.path.join(config['build_dir'], iso))
except:
    pass

for key, row in c2.iterrows():
    if row['stp_key']:
        manifest[iso]['locales'].append(os.path.join(iso, row['stp_key']))
        manifest[iso]['admin2'][row['stp_key']] = []

        with open(os.path.join(config['build_dir'], iso, row['stp_key'] + '.json'), 'w') as fd:
            data = to_json(c2.loc[key][date_columns], d2.loc[key][date_columns], None, iso=iso,
                    name=key, display_name='{}, {}'.format(key, iso), state_code=row['stp_key'], lat=bg1['lat'].get(key), lon=bg1['long'].get(key),
                    population=safe_cast(bg1['population'].get(key)), land_area=safe_cast(bg1['land_area'].get(key)))

            json.dump(data, fd)


for key, row in c.dropna(subset=['Admin2']).iterrows():
    st_abbr = bg1['code'].get(row['Province/State'])
    if st_abbr:
        manifest[iso]['admin2'][st_abbr].append(os.path.join(iso, st_abbr, row['stp_key']))
        try:
            os.mkdir(os.path.join(config['build_dir'], iso, st_abbr))
        except:
            pass

        with open(os.path.join(config['build_dir'], iso, st_abbr, row['stp_key'] + '.json'), 'w') as fd:
            data = to_json(c.loc[key][date_columns], d.loc[key][date_columns], None, iso=iso,
                    fips=row['FIPS'], state_code=st_abbr, name=row['Admin2'],
                    display_name='{} County, {}'.format(row['Admin2'], st_abbr),
                    lat=bg2['lat'].get(row['FIPS']), lon=bg2['long'].get(row['FIPS']),
                    population=safe_cast(bg2['population'].get(row['FIPS'])), land_area=safe_cast(bg2['land_area'].get(row['FIPS'])))
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
            admin2 = v.get('admin2', {})
            for elem in v['locales']:
                print('  <li><a href="{0}.json">{0}</a>'.format(elem), end='', file=fd)
                (iso,stp) = elem.split('/', maxsplit=1)
                if admin2.get(stp):
                    print('\n    <ul>', file=fd)
                    for cty in admin2[stp]:
                        print('    <li><a href="{0}.json">{0}</a>'.format(cty), file=fd)

                    print('    </ul></li>', file=fd)
                else:
                    print('</li>', file=fd)

            print('  </ul></li>', file=fd)
        else:
            print('</li>', file=fd)
    
    print('</ul>\n</body>\n</html>', file=fd)
