# -*- coding: utf-8 -*-
"""巡回の対象を、県庁所在地・政令指定都市・東京23区の74件から
全国の市（792件）へ広げるための対象リストを作る。

順番は人口の多い順にする。全部を回すには時間がかかるため、届く人の
多いところから先に整える。人口は Wikidata の P1082（人口）を、
全国地方公共団体コード（P429）で突き合わせて取る。名前で突き合わせる
と同名の自治体で取り違えるため、コードだけで結合する。

人口が取れなかった市は、コード順（北から南）で後ろに置く。推測した
数字で並べ替えることはしない。

出力: data/cities.json（fetch-welfare-programs.py の SITES_FILE に渡す）
"""
import json
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
    sites = json.loads((ROOT / 'data' / 'municipality-sites.json').read_text(encoding='utf-8'))['sites']
    done = json.loads((ROOT / 'data' / 'priority-municipalities.json').read_text(encoding='utf-8'))['sites']
    done_codes = {s['code'] for s in done}

    pops = populations()
    print('Wikidata から人口を取得: {0:,}件'.format(len(pops)))

    # 対象は「市」。町村は後回しにする（数が多く、制度のページを持たない
    # ところも多い）。東京23区は74件のほうで済んでいる。
    cities = [s for s in sites if s['name'].endswith('市')]
    new = [s for s in cities if s['code'] not in done_codes]

    matched = sum(1 for s in new if s['code'] in pops)
    print('全国の市 {0}件、うち未処理 {1}件、人口が取れた {2}件'.format(
        len(cities), len(new), matched))

    # 人口の多い順。人口不明はコード順で末尾へ
    new.sort(key=lambda s: (-pops.get(s['code'], -1), s['code']))
    for s in new:
        if s['code'] in pops:
            s['population'] = pops[s['code']]

    out = {
        'note': '全国の市のうち、74自治体の先行分を除いたもの。人口の多い順。'
                '人口は Wikidata の P1082 を全国地方公共団体コード（P429）で突き合わせた。',
        'urlSource': 'data/municipality-sites.json',
        'sites': new,
    }
    path = ROOT / 'data' / 'cities.json'
    path.write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('data/cities.json に {0}件を書いた。先頭:'.format(len(new)))
    for s in new[:10]:
        print('  {0}{1} {2:,}人'.format(s['pref'], s['name'], s.get('population', 0)))


if __name__ == '__main__':
    main()
