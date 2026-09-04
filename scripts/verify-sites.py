# -*- coding: utf-8 -*-
"""自治体の公式サイトURLが、本当にその自治体のものかを確かめる。

data/municipality-sites.json のURLは型から機械的に作ったもので、検証されて
いない（`verified: false`）。**失効して第三者に取られているものがあった。**
三重県御浜町の tiktocoins.info は、ベトナム語の賭博アプリへ誘導するページに
なっていた。索引からその自治体の公式サイトとしてリンクしていた。

ここで防ぎたいのは、**そのURLが別人のものになっていること**であって、
サイトが落ちているかどうかではない。証明書の期限切れやUAの拒否で
こちらが取れなくても、ブラウザでは開ける自治体がある（富岡市と多可町は
curl なら200が返る）。取れないことを理由にリンクを外すと、正しいURLまで
落としてしまう。

判定は2段。ページに自治体名が出れば良し。出なくても、ホスト名に自治体の
ローマ字が入っていれば良しとする（トップがJavaScriptで描かれていて、
HTMLに名前が出ない自治体がある）。この2段で、青森県板柳町のURLが
鶴田町のサイト（www.town.tsuruta.lg.jp）を指している誤りを切り分けられた。
板柳町の制度として鶴田町の子育て制度を5件拾っていた。

出力: data/site-verification.json
使い方:
  python scripts/verify-sites.py [--limit 200]
  python scripts/verify-sites.py --retry     取得できなかったものを再試行
"""
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from romaji import kana_to_romaji
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

    retry = '--retry' in sys.argv
    todo = [s for s in sites
            if s['code'] not in results
            or (retry and not results[s['code']].get('ok'))][:limit]
    print('未確認 {0}件。今回は {1}件を見ます。'.format(
        sum(1 for s in sites if s['code'] not in results), len(todo)))

    for i, s in enumerate(todo, 1):
        name = s['name']
        # 「町」「村」を落とした形でも探す（「七ヶ浜町」→「七ヶ浜」）
        short = re.sub(r'[市区町村]$', '', name)
        row = {'url': s['url'], 'name': name}
        host = s['url'].split('/')[2].replace('-', '')
        # ホスト名に自治体のローマ字が入っていれば、名前が出なくても本物とみなす
        by_host = kana_to_romaji(s['kana']) in host
        try:
            final, html = fetch(s['url'])
            title = (re.search(r'<title>(.*?)</title>', html, re.S) or [None, ''])[1].strip()
            row['title'] = title[:60]
            row['final'] = final
            if name in html or short in html:
                row['ok'] = True
            elif by_host:
                row['ok'] = True
                row['note'] = 'ページに名前は出ないが、ホスト名がローマ字と一致する'
            else:
                row['ok'] = False
                row['reason'] = 'ページに自治体名が出てこず、ホスト名も一致しない'
        except Exception as exc:
            # こちらが取れないことと、URLが間違っていることは別。
            # 証明書の期限切れ、PythonのTLSが弾く古い設定、UAの拒否などが
            # あるが、いずれもブラウザでは開ける（富岡市と多可町は curl では
            # 200 が返る）。ホスト名が自治体のローマ字と一致するなら、
            # URL自体は正しいものとして扱う。
            row['fetchError'] = type(exc).__name__
            if by_host:
                row['ok'] = True
                row['note'] = 'こちらからは取得できないが、ホスト名がローマ字と一致する'
            else:
                row['ok'] = False
                row['reason'] = '取得できず、ホスト名も一致しない: {0}'.format(type(exc).__name__)
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
