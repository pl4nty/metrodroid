#!/usr/bin/env python3
# -*- mode: python; indent-tabs-mode: nil; tab-width: 2; coding: utf-8 -*-
"""
suica2csv.py - merges Japan IC (Suica) station and bus stop lists into
csv2pb.py inputs.

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

Inputs:

* legacy_rail.csv / legacy_bus.csv: the data previously shipped in
  data/felica_stations.db3 (originally from Farebot / IC SFCard Fan). This is
  the only source of English names and coordinates.

* StationCode.csv, StationCodeExtra.csv, BusCode.csv, BusCodeExtra.csv from
  Kdroidwin/suicanfc-kd (GPLv3). These are Japanese only.

Rules:

* Newer Japanese names win. An English name (and coordinates) from the legacy
  data is only kept when its Japanese name still matches, after normalising
  variant kana/kanji. No names are machine translated.
* Placeholder rows (仮称 / 未定) are skipped.
* Rail station IDs are (area << 16) | (line << 8) | station.
* Bus stop IDs are (operator << 16) | stop, using the full 16-bit codes from
  the card.
* Operator and line IDs are assigned in sorted order, so output is stable.
"""

from argparse import ArgumentParser
from collections import Counter, defaultdict
import csv
import os

NORMALISE = str.maketrans({'ヶ': 'ケ', 'ヵ': 'カ', 'ッ': 'ツ', '鴬': '鶯', '曾': '曽', '廚': '厨', '﨑': '崎', '髙': '高', '　': ' '})
PLACEHOLDERS = ('仮称', '未定')


def norm(s):
  return (s or '').translate(NORMALISE).strip()


def read_rows(path):
  with open(path, encoding='utf-8-sig', newline='') as f:
    return [r for r in csv.reader(f) if r]


def read_dicts(path):
  with open(path, encoding='utf-8-sig', newline='') as f:
    return list(csv.DictReader(f))


def is_placeholder(name):
  return not name or any(p in name for p in PLACEHOLDERS)


def majority(counter_map):
  """Maps each key to its most common value; ties broken by value for stability."""
  return {k: sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))[0][0] for k, c in counter_map.items()}


class Names:
  """Assigns stable IDs to (local, english) names."""

  def __init__(self):
    self.english = {}

  def add(self, local, english=None):
    if not local:
      return
    if english or local not in self.english:
      self.english[local] = english or self.english.get(local) or ''

  def ids(self):
    return {local: i + 1 for i, local in enumerate(sorted(self.english))}

  def write(self, path):
    with open(path, 'w', encoding='utf-8', newline='') as f:
      w = csv.writer(f, lineterminator='\n')
      w.writerow(['id', 'name', 'local_name'])
      for local, i in sorted(self.ids().items(), key=lambda kv: kv[1]):
        w.writerow([i, self.english[local], local])


def write_stations(path, stations, operators, lines):
  op_ids, line_ids = operators.ids(), lines.ids()
  with open(path, 'w', encoding='utf-8', newline='') as f:
    w = csv.writer(f, lineterminator='\n')
    w.writerow(['reader_id', 'stop_name', 'local_name', 'stop_lat', 'stop_lon', 'operator_id', 'line_id'])
    for sid in sorted(stations):
      s = stations[sid]
      w.writerow([
        '0x%x' % sid, s['en'], s['ja'], s.get('lat', ''), s.get('lon', ''),
        op_ids.get(s['company'], ''), line_ids.get(s['line'], '')])


def merge_rail(legacy_dir, src, out):
  legacy = {}
  operators, lines = Names(), Names()
  legacy_line = defaultdict(Counter)
  for r in read_dicts(os.path.join(legacy_dir, 'legacy_rail.csv')):
    key = (int(r['area']), int(r['line']), int(r['station']))
    legacy[key] = r
    operators.add(r['company'], r['company_en'])
    lines.add(r['line_name'], r['line_en'])
    legacy_line[key[:2]][r['line_name']] += 1
  legacy_line = majority(legacy_line)

  # suicanfc-kd: StationCode.csv first, then StationCodeExtra.csv only fills gaps.
  newer = {}
  for name in ('StationCode.csv', 'StationCodeExtra.csv'):
    for r in read_rows(os.path.join(src, name)):
      if len(r) < 6 or is_placeholder(r[5]):
        continue
      key = (int(r[0]), int(r[1]), int(r[2]))
      if key not in newer:
        newer[key] = {'company': r[3], 'line': r[4], 'ja': r[5]}

  # Map suicanfc-kd company names (eg: JR東日本) onto the legacy operator names
  # (eg: 東日本旅客鉄道) where both cover the same stations.
  company_map = defaultdict(Counter)
  for key, n in newer.items():
    if key in legacy and n['company']:
      company_map[n['company']][legacy[key]['company']] += 1
  company_map = majority(company_map)

  # Some stations moved to a different station code (eg: 田町 when 高輪ゲートウェイ
  # was added). Find legacy stations by name within the same area and line.
  by_name = defaultdict(list)
  for key, r in legacy.items():
    by_name[(key[0], key[1], norm(r['station_name']))].append(r)

  stations = {}
  for key in sorted(legacy.keys() | newer.keys()):
    old, new = legacy.get(key), newer.get(key)
    if new is None:
      s = {'ja': old['station_name'], 'en': old['station_en'], 'lat': old['lat'], 'lon': old['lon'],
           'company': old['company'], 'line': old['line_name']}
    else:
      same = old is not None and norm(old['station_name']) == norm(new['ja'])
      if not same:
        moved = by_name.get((key[0], key[1], norm(new['ja'])), [])
        if len(moved) == 1:
          old, same = moved[0], True
      company = old['company'] if old else company_map.get(new['company'], new['company'])
      # suicanfc-kd's StationCode.csv has abbreviated line names (eg: "K"), so
      # prefer the legacy line name for this line code.
      line = legacy_line.get(key[:2]) or (new['line'] if len(new['line']) > 2 else '')
      s = {'ja': new['ja'], 'en': old['station_en'] if same else '',
           'lat': old['lat'] if same else '', 'lon': old['lon'] if same else '',
           'company': company, 'line': line}
      operators.add(company)
      lines.add(line)
    sid = (key[0] << 16) | (key[1] << 8) | key[2]
    if sid:
      stations[sid] = s

  write_stations(os.path.join(out, 'rail_stations.csv'), stations, operators, lines)
  operators.write(os.path.join(out, 'rail_operators.csv'))
  lines.write(os.path.join(out, 'rail_lines.csv'))
  return len(legacy), len(stations)


def merge_bus(legacy_dir, src, out):
  legacy = {}
  operators, lines = Names(), Names()
  for r in read_dicts(os.path.join(legacy_dir, 'legacy_bus.csv')):
    key = (int(r['line'], 16), int(r['stop'], 16))
    legacy[key] = r
    operators.add(r['company'], r['company_en'])
    lines.add(r['line_name'], r['line_en'])

  newer = {}
  for name in ('BusCode.csv', 'BusCodeExtra.csv'):
    for r in read_rows(os.path.join(src, name)):
      if len(r) < 5 or is_placeholder(r[4]):
        continue
      key = (int(r[0], 16), int(r[1], 16))
      if key[0] > 0xffff or key[1] > 0xffff:
        continue
      if key not in newer:
        newer[key] = {'company': r[2], 'line': r[3], 'ja': r[4]}

  stations = {}
  for key in sorted(legacy.keys() | newer.keys()):
    old, new = legacy.get(key), newer.get(key)
    if new is None:
      s = {'ja': old['stop_name'], 'en': old['stop_en'], 'company': old['company'], 'line': old['line_name']}
    else:
      same = old is not None and norm(old['stop_name']) == norm(new['ja'])
      s = {'ja': new['ja'], 'en': old['stop_en'] if same else '',
           'company': new['company'] or (old['company'] if old else ''),
           'line': new['line'] or (old['line_name'] if old else '')}
      operators.add(s['company'])
      lines.add(s['line'])
    sid = (key[0] << 16) | key[1]
    if sid:
      stations[sid] = s

  write_stations(os.path.join(out, 'bus_stations.csv'), stations, operators, lines)
  operators.write(os.path.join(out, 'bus_operators.csv'))
  lines.write(os.path.join(out, 'bus_lines.csv'))
  return len(legacy), len(stations)


def main():
  parser = ArgumentParser(description=__doc__.split('\n')[1])
  parser.add_argument('-l', '--legacy', default='.', help='directory with legacy_rail.csv and legacy_bus.csv')
  parser.add_argument('-s', '--source', default='.', help='directory with the suicanfc-kd CSVs')
  parser.add_argument('-o', '--output', default='.', help='directory to write csv2pb inputs to')
  options = parser.parse_args()
  print('rail: %d legacy -> %d stations' % merge_rail(options.legacy, options.source, options.output))
  print('bus: %d legacy -> %d stops' % merge_bus(options.legacy, options.source, options.output))


if __name__ == '__main__':
  main()
