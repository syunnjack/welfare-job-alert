# -*- coding: utf-8 -*-
"""巡回の対象リストを作る。

  python scripts/build-city-list.py           全国の市 → data/cities.json
  python scripts/build-city-list.py --towns   全国の町村 → data/towns.json

すでに巡回した自治体は除く（data/welfare-programs.json にあるもの）。

順番は人口の多い順にする。全部を回すには時間がかかるため、届く人の
多いところから先に整える。人口は Wikidata の P1082（人口）を、
全国地方公共団体コード（P429）で突き合わせて取る。名前で突き合わせる
と同名の自治体で取り違えるため、コードだけで結合する。

人口が取れなかった市は、コード順（北から南）で後ろに置く。推測した
数字で並べ替えることはしない。

出力: data/cities.json（fetch-welfare-programs.py の SITES_FILE に渡す）
"""
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = 'welfarejob.jp/1.0 (+https://welfarejob.jp/)'
SPARQL = 'https://query.wikidata.org/sparql'

QUERY = """
SELECT ?code (MAX(?pop) AS ?population) WHERE {
  ?city wdt:P429 ?code ; wdt:P1082 ?pop .
}
GROUP BY ?code
"""


def populations():
    url = SPARQL + '?' + urllib.parse.urlencode({'query': QUERY, 'format': 'json'})
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=120) as res:
        data = json.loads(res.read())
    out = {}
    for row in data['results']['bindings']:
        code = row['code']['value']
        try:
            out[code] = int(float(row['population']['value']))
        except (KeyError, ValueError):
            continue
    return out


def main():
    towns = '--towns' in sys.argv
    sites = json.loads((ROOT / 'data' / 'municipality-sites.json').read_text(encoding='utf-8'))['sites']

    # すでに巡回したものは除く。前回の結果をそのまま引き継ぐ
    done_codes = set()
    out_path = ROOT / 'data' / 'welfare-programs.json'
    if out_path.exists():
        done_codes |= set(json.loads(out_path.read_text(encoding='utf-8'))['entries'])
    for name in ('priority-municipalities.json', 'cities.json'):
        path = ROOT / 'data' / name
        if path.exists():
            done_codes |= {s['code'] for s in json.loads(path.read_text(encoding='utf-8'))['sites']}

    pops = populations()
    print('Wikidata から人口を取得: {0:,}件'.format(len(pops)))

    if towns:
        target = [s for s in sites if s['name'].endswith(('町', '村'))]
        label, filename = '全国の町村', 'towns.json'
    else:
        target = [s for s in sites if s['name'].endswith('市')]
        label, filename = '全国の市', 'cities.json'
    new = [s for s in target if s['code'] not in done_codes]

    matched = sum(1 for s in new if s['code'] in pops)
    print('{0} {1}件、うち未処理 {2}件、人口が取れた {3}件'.format(
        label, len(target), len(new), matched))

    # 人口の多い順。人口不明はコード順で末尾へ
    new.sort(key=lambda s: (-pops.get(s['code'], -1), s['code']))
    for s in new:
        if s['code'] in pops:
            s['population'] = pops[s['code']]

    out = {
        'note': '{0}のうち、すでに巡回したものを除いたもの。人口の多い順。'
                '人口は Wikidata の P1082 を全国地方公共団体コード（P429）で'
                '突き合わせた。'.format(label),
        'urlSource': 'data/municipality-sites.json',
        'sites': new,
    }
    path = ROOT / 'data' / filename
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('data/{0} に {1}件を書いた。先頭:'.format(filename, len(new)))
    for s in new[:10]:
        print('  {0}{1} {2:,}人'.format(s['pref'], s['name'], s.get('population', 0)))


if __name__ == '__main__':
    main()
