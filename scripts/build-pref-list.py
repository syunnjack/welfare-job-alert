# -*- coding: utf-8 -*-
"""都道府県の公式サイトURLを確かめて、巡回の対象リストを作る。

市区町村と違い、都道府県のURLは手元のマスタに無い。`www.pref.<ローマ字>.lg.jp`
のような型があるので候補を作るが、**当て推量のまま使わない。**候補を実際に
開いて、ページに都道府県名が入っていることを確かめたものだけを採る。
（東京都は metro、京都府と大阪府は .lg.jp でないなど、型から外れるものがある）

出力: data/prefectures.json（fetch-welfare-programs.py の SITES_FILE に渡す）
"""
import json
import re
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UA = 'welfarejob.jp/1.0 (+https://welfarejob.jp/)'

ROMAJI = {
    '北海道': 'hokkaido', '青森県': 'aomori', '岩手県': 'iwate', '宮城県': 'miyagi',
    '秋田県': 'akita', '山形県': 'yamagata', '福島県': 'fukushima', '茨城県': 'ibaraki',
    '栃木県': 'tochigi', '群馬県': 'gunma', '埼玉県': 'saitama', '千葉県': 'chiba',
    '東京都': 'tokyo', '神奈川県': 'kanagawa', '新潟県': 'niigata', '富山県': 'toyama',
    '石川県': 'ishikawa', '福井県': 'fukui', '山梨県': 'yamanashi', '長野県': 'nagano',
    '岐阜県': 'gifu', '静岡県': 'shizuoka', '愛知県': 'aichi', '三重県': 'mie',
    '滋賀県': 'shiga', '京都府': 'kyoto', '大阪府': 'osaka', '兵庫県': 'hyogo',
    '奈良県': 'nara', '和歌山県': 'wakayama', '鳥取県': 'tottori', '島根県': 'shimane',
    '岡山県': 'okayama', '広島県': 'hiroshima', '山口県': 'yamaguchi', '徳島県': 'tokushima',
    '香川県': 'kagawa', '愛媛県': 'ehime', '高知県': 'kochi', '福岡県': 'fukuoka',
    '佐賀県': 'saga', '長崎県': 'nagasaki', '熊本県': 'kumamoto', '大分県': 'oita',
    '宮崎県': 'miyazaki', '鹿児島県': 'kagoshima', '沖縄県': 'okinawa',
}


# 型から外れるもの。実際に開いて確かめたURLだけを置く
EXTRA = {
    '東京都': ['https://www.metro.tokyo.lg.jp/'],
    '兵庫県': ['https://web.pref.hyogo.lg.jp/'],
}

# こちらの取得を拒否している。理由を書いて対象から外す
DECLINED = {
    '愛知県': 'トップページが 403 を返す（Cookieを持たせても同じ）',
}


def candidates(name):
    r = ROMAJI[name]
    return EXTRA.get(name, []) + [
        'https://www.pref.{0}.lg.jp/'.format(r),
        'https://www.pref.{0}.jp/'.format(r),
    ]


def fetch(url):
    try:
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
    except Exception:
        return None, None


def main():
    prefs = json.loads((ROOT / 'data' / 'municipalities.json').read_text(encoding='utf-8'))['prefectures']
    sites = []
    failed = []
    declined = []
    for p in prefs:
        name = p['name']
        if name in DECLINED:
            declined.append('{0}（{1}）'.format(name, DECLINED[name]))
            print('  － {0:<6} 対象外: {1}'.format(name, DECLINED[name]))
            continue
        # 「東京都」→「東京」のように、都道府県の字を落とした形でも探す
        short = re.sub(r'[都道府県]$', '', name)
        found = None
        for url in candidates(name):
            final, html = fetch(url)
            if not html:
                continue
            title = (re.search(r'<title>(.*?)</title>', html, re.S) or [None, ''])[1]
            if name in html or name in title or short in title:
                found = final
                break
        if found:
            sites.append({'code': p['code'], 'pref': '', 'name': name,
                          'kana': p['kana'], 'url': found})
            print('  ◯ {0:<6} {1}'.format(name, found))
        else:
            failed.append(name)
            print('  × {0:<6} 確かめられなかった'.format(name))

    out = {
        'note': '都道府県の公式サイト。候補URLを実際に開き、ページに都道府県名が'
                '入っていることを確かめたものだけ。拒否された都道府県は含めない。',
        'declined': DECLINED,
        'checkedOn': __import__('time').strftime('%Y-%m-%d'),
        'sites': sites,
    }
    (ROOT / 'data' / 'prefectures.json').write_text(
        json.dumps(out, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('確かめられた: {0}/47。data/prefectures.json に書いた。'.format(len(sites)))
    if failed:
        print('確かめられなかった: {0}'.format('、'.join(failed)))
    if declined:
        print('拒否されたため対象外: {0}'.format('、'.join(declined)))


if __name__ == '__main__':
    main()
