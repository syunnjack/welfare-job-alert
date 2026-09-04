# -*- coding: utf-8 -*-
"""自治体の公式サイトURLが、本当にその自治体のものかを確かめる。

data/municipality-sites.json のURLは型から機械的に作ったもので、検証されて
いない（`verified: false`）。**失効して第三者に取られているものがあった。**
三重県御浜町の tiktocoins.info は、ベトナム語の賭博アプリへ誘導するページに
なっていた。索引からその自治体の公式サイトとしてリンクしていた。

ここでは1件ずつ開き、ページに自治体名（「町」「村」を落とした形も含む）が
入っているかを見る。入っていなければ「確かめられなかった」として記録し、
サイトからはリンクしない。名前が出ないだけで公式なこともあるが、
**確かめられないものを公式として出さない**ほうを選ぶ。

出力: data/site-verification.json
使い方: python scripts/verify-sites.py [--limit 200]
"""
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = 'welfarejob.jp/1.0 (+https://welfarejob.jp/)'
OUT = ROOT / 'data' / 'site-verification.json'


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=25) as res:
        raw = res.read(400_000)
        charset = res.headers.get_content_charset()
        for enc in filter(None, [charset, 'utf-8', 'cp932', 'euc-jp']):
            try:
                return res.geturl(), raw.decode(enc)
            except (UnicodeDecodeError, LookupError):
                continue
        return res.geturl(), raw.decode('utf-8', errors='replace')


def main():
    limit = 100000
    if '--limit' in sys.argv:
        limit = int(sys.argv[sys.argv.index('--limit') + 1])

    sites = json.loads((ROOT / 'data' / 'municipality-sites.json').read_text(encoding='utf-8'))['sites']
    state = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {'results': {}}
    results = state.get('results', {})

    todo = [s for s in sites if s['code'] not in results][:limit]
    print('未確認 {0}件。今回は {1}件を見ます。'.format(
        sum(1 for s in sites if s['code'] not in results), len(todo)))

    for i, s in enumerate(todo, 1):
        name = s['name']
        # 「町」「村」を落とした形でも探す（「七ヶ浜町」→「七ヶ浜」）
        short = re.sub(r'[市区町村]$', '', name)
        row = {'url': s['url'], 'name': name}
        try:
            final, html = fetch(s['url'])
            title = (re.search(r'<title>(.*?)</title>', html, re.S) or [None, ''])[1].strip()
            row['title'] = title[:60]
            row['final'] = final
            row['ok'] = bool(name in html or short in html)
            if not row['ok']:
                row['reason'] = 'ページに自治体名が出てこない'
        except Exception as exc:
            row['ok'] = False
            row['reason'] = '取得できなかった: {0}'.format(type(exc).__name__)
        results[s['code']] = row
        if not row['ok']:
            print('  × {0}{1}  {2}  {3}'.format(
                s['pref'], name, s['url'], row.get('title') or row.get('reason')))
        time.sleep(1.0)
        if i % 100 == 0:
            state = {'checkedOn': time.strftime('%Y-%m-%d'), 'results': results}
            OUT.write_text(json.dumps(state, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
            print('  … {0}件まで保存'.format(len(results)))

    state = {'checkedOn': time.strftime('%Y-%m-%d'), 'results': results}
    OUT.write_text(json.dumps(state, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    ng = [r for r in results.values() if not r.get('ok')]
    print('確認済み {0}件、確かめられなかった {1}件'.format(len(results), len(ng)))


if __name__ == '__main__':
    main()
