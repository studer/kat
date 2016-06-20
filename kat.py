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


class KAT(object):
    def __init__(self, search, category=None, do_open_torrent=False):
        self._search = search
        self._category = category
        self._do_open_torrent = do_open_torrent
        self._url = 'https://kat.cr/usearch/{search}/?rss=1'
        self._user_agent = 'Mozilla/5.0 KAT-cli/0.1'
        self._session = requests.Session()

    def _prep_search(self):
        if self._category:
            self._search = '{search} category:{category}'.format(
                            search=self._search, category=self._category)

        return self._search

    def _find_items(self):
        print('Search : {search}'.format(search=self._search))

        req = self._session.get(self._url.format(search=self._search))
        html = bs4(req.text, 'lxml')

        items = html.find_all('item')

        return items

    def _parse_sort_items(self, items):
        item_table = [[
            item.find('title').text[:70],
            human(parser.parse(item.find('pubdate').text, ignoretz=True)),
            int(item.find('torrent:seeds').text),
            item.find('torrent:filename').text,
            item.find('enclosure').get('url')
            ] for item in items]

        sorted_item_table = sorted(item_table, key=itemgetter(2), reverse=True)
        [item.insert(0, i) for (i, item) in
            enumerate(sorted_item_table, start=1)]
        sorted_item_table.insert(
            0, ['ID', 'Title', 'Pubdate', 'Seeders', 'Filename', 'URL'])

        return sorted_item_table

    def _print_items(self, items):
        print(tabulate([[i, t, p, s] for (i, t, p, s, _, _) in items]))

    def _ask_input(self, items):
        sid = 0
        while not (int(sid) > 0 and int(sid) < len(items)):
            sid = input('ID (or quit) : ')
            if sid == 'quit' or sid == 'q':
                sys.exit(0)
            sid = int(sid)

        filename = items[sid][4]
        url = items[sid][5]

        return (filename, url)

    def _download(self, filename, url):
        print('Downloading {filename} from {url}'.format(
            filename=filename, url=url))

        headers = {'user-agent': self._user_agent}
        r = self._session.get(url, headers=headers, stream=True)

        with open(filename, 'wb') as fd:
            for chunk in r.iter_content(1024):
                fd.write(chunk)

    def _open_torrent(self, filename):
        subprocess.run(['open', filename])

    def main(self):
        self._prep_search()
        items = self._find_items()
        sorted_item_table = self._parse_sort_items(items)
        self._print_items(sorted_item_table)
        filename, url = self._ask_input(sorted_item_table)
        self._download(filename, url)
        if self._do_open_torrent:
            self._open_torrent(filename)


if __name__ == '__main__':
    arguments = docopt(__doc__, version='KAT-cli 0.1')

    search = arguments.get('<search>')
    category = arguments.get('-c')
    do_open_torrent = arguments.get('-t')

    kat = KAT(search, category, do_open_torrent)
    kat.main()
