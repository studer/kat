"""KAT-cli.

Usage:
  kat.py <search> [-c <category>] [-t]
  kat.py (-h | --help)
  kat.py --version

Options:
  -h --help                 Show this screen.
  --version                 Show version.
  -c <category>             Category to search.
  -t                        Launch Torrent.

"""
import sys
import requests
import subprocess

from ago import human
from docopt import docopt
from dateutil import parser
from tabulate import tabulate
from operator import itemgetter
from bs4 import BeautifulSoup as bs4

def main(arguments):
    search = arguments.get('<search>')
    category = arguments.get('-c')

    if category:
        search = '{search} category:{category}'.format(search=search, category=category)

    print('Search : {search}'.format(search=search))

    r = requests.get('https://kat.cr/usearch/{search}/?rss=1'.format(search=search))
    h = bs4(r.text, "lxml")

    ts = h.find_all('item')

    tt = [[t.find('title').text[:70], human(parser.parse(t.find('pubdate').text, ignoretz=True)), int(t.find('torrent:seeds').text), t.find('torrent:filename').text, t.find('enclosure').get('url')] for t in ts]

    stt = sorted(tt, key=itemgetter(2), reverse=True)

    [x.insert(0, i) for (i,x) in enumerate(stt, start=1)]

    stt.insert(0, ['ID', 'Title', 'Pubdate', 'Seeders', 'Filename', 'URL'])

    print(tabulate([[i,t,p,s] for (i,t,p,s,_,_) in stt]))

    sid = int(input('ID : '))

    filename = stt[sid][4]
    url = stt[sid][5]

    print('Downloading {filename} from {url}'.format(filename=filename, url=url))

    headers = {'user-agent': 'Mozilla/5.0 KAT-cli/0.1'}
    r = requests.get(url, headers=headers, stream=True)

    with open(filename, 'wb') as fd:
        for chunk in r.iter_content(1024):
            fd.write(chunk)

    if arguments.get('-t'):
        subprocess.run(['open', filename])

if __name__ == '__main__':
    arguments = docopt(__doc__, version='KAT-cli 0.1')
    main(arguments)
