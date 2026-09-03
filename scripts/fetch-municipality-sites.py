"""各自治体の公式サイトURLを集める。

自治体マスタ（総務省のコード）に、Wikidata が持っている公式サイトURLを
突き合わせる。Wikidata は全国地方公共団体コード（P429）と公式サイト（P856）を
持っているので、コードで確実に結合できる。名前で突き合わせると同名の
市町村で取り違えるため、コードで結ぶ。

**URLは必ず実在を確認してから記録する。** 取得できただけのURLは載せない。
リンク切れを並べると、利用者を無駄足させることになる。

使い方:
  python scripts/fetch-municipality-sites.py              取得して全件確認
  python scripts/fetch-municipality-sites.py --limit 50   先頭50件だけ確認（動作確認用）
  python scripts/fetch-municipality-sites.py --no-verify  確認せず取得だけ
"""
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MASTER = ROOT / 'data' / 'municipalities.json'
OUT = ROOT / 'data' / 'municipality-sites.json'
UA = 'welfarejob.jp/1.0 (+https://welfarejob.jp/ municipality directory)'

QUERY = """
SELECT ?code ?site WHERE {
  ?item wdt:P429 ?code .
  ?item wdt:P856 ?site .
}
"""


def arg(name: str, fallback=None):
    if name in sys.argv:
        index = sys.argv.index(name)
        return sys.argv[index + 1] if index + 1 < len(sys.argv) else True
    return fallback


def fetch_wikidata() -> dict:
    url = 'https://query.wikidata.org/sparql?format=json&query=' + urllib.parse.quote(QUERY)
    request = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/sparql-results+json'})
    with urllib.request.urlopen(request, timeout=120) as response:
        data = json.loads(response.read().decode())

    sites = {}
    for row in data['results']['bindings']:
        code = row['code']['value'].strip()
        site = row['site']['value'].strip()
        # 同じコードに複数のURLがある場合は、https を優先し、短いものを採る。
        current = sites.get(code)
        if current is None or (not current.startswith('https') and site.startswith('https')) or len(site) < len(current):
            sites[code] = site
    return sites


def verify(url: str) -> bool:
    """本当に開けるURLかを確かめる。開けないものは載せない。"""
    request = urllib.request.Request(url, headers={'User-Agent': UA}, method='GET')
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return 200 <= response.status < 400
    except urllib.error.HTTPError as error:
        # 403 を返す自治体サイトがある（UA制限）。存在はしているので通す。
        return error.code in (403, 405)
    except Exception:
        return False


def main() -> None:
    master = json.loads(MASTER.read_text(encoding='utf-8'))
    sites = fetch_wikidata()
    print(f'Wikidata から {len(sites):,}件のURLを取得しました。')

    limit = arg('--limit')
    limit = int(limit) if limit and limit is not True else None
    do_verify = '--no-verify' not in sys.argv

    rows = []
    missing = []
    checked = 0

    for entry in master['municipalities']:
        url = sites.get(entry['code'])
        if not url:
            missing.append(entry)
            continue
        ok = None
        if do_verify and (limit is None or checked < limit):
            ok = verify(url)
            checked += 1
            time.sleep(0.4)   # 自治体のサーバーに負荷をかけない
            if not ok:
                missing.append({**entry, 'url': url, 'reason': '開けなかった'})
                continue
        rows.append({**entry, 'url': url, 'verified': bool(ok)})

    data = {
        'source': master['source'],
        'urlSource': 'https://www.wikidata.org/ (P429 全国地方公共団体コード / P856 公式サイト)',
        'checkedOn': time.strftime('%Y-%m-%d'),
        'sites': rows,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

    total = len(master['municipalities'])
    print(f'記録: {len(rows):,}件 / 全{total:,}件（{len(rows) * 100 // total}%）')
    print(f'URLが取れなかった、または開けなかったもの: {len(missing):,}件')
    if missing[:5]:
        for entry in missing[:5]:
            print(f'  - {entry["pref"]}{entry["name"]}  {entry.get("reason", "URLなし")}')


if __name__ == '__main__':
    main()
