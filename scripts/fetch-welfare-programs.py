"""各自治体の公式サイトから、障害者向け制度の「名称」だけを集める。

方針（案A）:
  - **制度名と、それが載っていたページのURL、取得した日付だけを記録する。**
  - 金額・対象等級・所得制限は記録しない。改定されると誤りになり、
    古い情報のまま窓口へ行かせることになるため。
  - 決めた語彙に一致したものだけを拾う。ページの文章から制度名を
    作り出すことはしない。推測で「ありそう」と書かない。

やり方:
  1. 公式サイトのトップを取り、障害福祉のページへのリンクを探す
  2. そのページを取り、語彙に一致する制度名を拾う
  3. 見つかった制度名を、出典URLと取得日つきで記録する

相手は自治体のサーバーなので、1件ごとに間隔を空ける。
1回の実行で全件は回さず、続きから進める（--limit）。

使い方:
  python scripts/fetch-welfare-programs.py --limit 30
  python scripts/fetch-welfare-programs.py --limit 30 --retry   失敗したものを再試行
"""
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITES = ROOT / 'data' / (os.environ.get('SITES_FILE') or 'municipality-sites.json')
OUT = ROOT / 'data' / 'welfare-programs.json'
# HTTPヘッダは latin-1 でしか送れない。日本語を入れると送信時に例外になる。
UA = 'welfarejob.jp/1.0 (+https://welfarejob.jp/)'

# 障害福祉のページへ辿るための手がかり。リンク文字列に含まれるかで判断する。
PAGE_HINTS = ['障害福祉', '障がい福祉', '障害者福祉', '障がい者福祉', '障害のある方', '障がいのある方', '障害者の方', '障がい者の方',
              '障害者支援', '障がい者支援', '障害者', '障がい者', '障害', '障がい']

# トップに障害福祉への直リンクが無い自治体が多い。その場合は
# 「健康・福祉」のような中間カテゴリを1段挟んで探す。
# 74自治体で試したとき、直リンクだけでは22%にしか届かなかった。
GATEWAY_HINTS = ['健康・福祉', '福祉・健康', '健康と福祉', '福祉', '健康', 'くらし', '暮らし', '子育て・福祉', '医療・福祉']

# リンク文言がこれらの語を含むときだけ、制度として拾う。
# 給付・割引・手続きを表す語に限り、お知らせや組織案内は拾わない。
BENEFIT_WORDS = [
    '減免', '助成', '割引', '給付', '支給', '手当', '貸付', '補助',
    '交付', '無料', '免除', '派遣', '利用券', '費用', '料金',
]

# 上の語を含んでいても、制度そのものではないもの。
EXCLUDE_WORDS = [
    '一覧', '目次', 'ページ', 'よくある', '問い合わせ', 'お問合せ', 'アンケート',
    '募集', '入札', '職員', '採用', '議会', '広報', '計画', '統計', '条例',
]

# 参考: よくある制度名。抽出には使わないが、語彙の目安として残す。
PROGRAMS = [
    '水道料金の減免', '下水道使用料の減免', '上下水道料金の減免',
    '福祉タクシー', 'タクシー利用券', 'タクシー料金の助成',
    '自動車燃料費の助成', 'ガソリン費の助成',
    '駐車禁止除外指定車標章', '駐車禁止除外',
    '自動車税の減免', '軽自動車税の減免',
    '有料道路の割引',
    '粗大ごみ手数料の減免', 'ごみ処理手数料の減免',
    '心身障害者医療費助成', '重度心身障害者医療費助成', '医療費の助成',
    '補装具費の支給', '日常生活用具の給付',
    '移動支援', '同行援護', '行動援護',
    '手話通訳者の派遣', '要約筆記者の派遣',
    'コミュニティバスの割引', 'バス運賃の割引',
    '公共施設使用料の減免',
    '住宅改修費の助成', '住宅リフォームの助成',
    'NHK放送受信料の減免',
    '就労移行支援', '就労継続支援', '就労定着支援',
    '障害者就労施設等からの優先調達',
]


def normalize(text: str) -> str:
    return text.replace('障がい', '障害').replace('障碍', '障害')


def fetch(url: str, timeout: int = 25) -> str | None:
    request = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read(1_500_000)
            charset = response.headers.get_content_charset()
            for encoding in filter(None, [charset, 'utf-8', 'cp932', 'euc-jp']):
                try:
                    return raw.decode(encoding)
                except (UnicodeDecodeError, LookupError):
                    continue
            return raw.decode('utf-8', errors='replace')
    except Exception:
        return None


def find_links(base_url: str, html: str, hints: list, limit: int = 3) -> list:
    """指定した手がかり語を含むリンクを、同じドメイン内から拾う。"""
    found = []
    seen = set()
    host = urllib.parse.urlparse(base_url).netloc
    for match in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.I | re.S):
        label = normalize(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', match.group(2))).strip())
        if not label or len(label) > 30:
            continue
        if not any(hint in label for hint in map(normalize, hints)):
            continue
        url = urllib.parse.urljoin(base_url, match.group(1))
        if urllib.parse.urlparse(url).netloc != host or url in seen:
            continue
        seen.add(url)
        found.append(url)
        if len(found) >= limit:
            break
    return found


def find_welfare_page(top_url: str, html: str) -> str | None:
    """トップページから、障害福祉のページへのリンクを探す。"""
    best = None
    for match in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.I | re.S):
        href, label = match.group(1), re.sub(r'<[^>]+>', '', match.group(2))
        label = normalize(label.strip())
        if not label or len(label) > 40:
            continue
        if any(hint in label for hint in map(normalize, PAGE_HINTS)):
            url = urllib.parse.urljoin(top_url, href)
            # 同じドメイン内に限る。外部サイトへ飛ぶリンクは採らない。
            if urllib.parse.urlparse(url).netloc == urllib.parse.urlparse(top_url).netloc:
                # 「障害福祉」により近い文言を優先する。
                if best is None or len(label) < best[0]:
                    best = (len(label), url)
    return best[1] if best else None


def extract_programs(page_url: str, html: str) -> list:
    """障害福祉ページのリンク文言を、そのまま制度名として拾う。

    固定の語彙に一致させる方式では、自治体ごとの言い回しの違いで
    ほとんど拾えなかった（「水道料金の減免」と「上下水道料金減免」など）。
    **その自治体が自分でそう呼んでいる名前**を、リンク文言のまま記録する。
    こちらのほうが正確で、制度ごとに出典URLも取れる。

    拾うのは、給付や割引を表す語を含むリンクだけ。お知らせや組織案内は除く。
    """
    found = []
    seen = set()
    for match in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.I | re.S):
        href = match.group(1)
        label = re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', match.group(2))).strip()
        if not (3 <= len(label) <= 40):
            continue
        if not any(word in label for word in BENEFIT_WORDS):
            continue
        if any(word in label for word in EXCLUDE_WORDS):
            continue
        url = urllib.parse.urljoin(page_url, href)
        if urllib.parse.urlparse(url).netloc != urllib.parse.urlparse(page_url).netloc:
            continue
        key = normalize(label)
        if key in seen:
            continue
        seen.add(key)
        found.append({'name': label, 'url': url})
        if len(found) >= 40:
            break
    return found


def sub_pages(page_url: str, html: str, limit: int = 5) -> list:
    """障害福祉ページから、その下の階層へのリンクを拾う。

    障害福祉のトップはハブになっていて、制度の実ページは1段下にある。
    1階層しか見ないと「医療助成」「補助・助成」といった目次を拾ってしまう。

    障害に関する範囲から出ないよう、リンク文言かURLに障害を表す語が
    あるものだけを辿る。自治体のサーバーに負荷をかけないので、数も絞る。
    """
    found = []
    seen = set()
    host = urllib.parse.urlparse(page_url).netloc
    for match in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.I | re.S):
        href = match.group(1)
        label = normalize(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', match.group(2))).strip())
        url = urllib.parse.urljoin(page_url, href)
        if urllib.parse.urlparse(url).netloc != host:
            continue
        if url.rstrip('/') == page_url.rstrip('/') or url in seen:
            continue
        # 障害に関する範囲にとどめる。ラベルかURLのどちらかに手がかりが要る。
        in_scope = '障害' in label or 'shogai' in url.lower() or 'shougai' in url.lower() or 'syougai' in url.lower()
        if not in_scope:
            continue
        if any(word in label for word in EXCLUDE_WORDS):
            continue
        seen.add(url)
        found.append(url)
        if len(found) >= limit:
            break
    return found


def collect(page_url: str, html: str) -> list:
    """障害福祉ページと、その下の階層から制度を集める。"""
    programs = extract_programs(page_url, html)
    seen = {normalize(item['name']) for item in programs}

    for url in sub_pages(page_url, html):
        child = fetch(url)
        time.sleep(1.0)
        if not child:
            continue
        for item in extract_programs(url, child):
            key = normalize(item['name'])
            if key in seen:
                continue
            seen.add(key)
            programs.append(item)
        if len(programs) >= 40:
            break
    return programs[:40]


def main() -> None:
    sites = json.loads(SITES.read_text(encoding='utf-8'))['sites']
    state = json.loads(OUT.read_text(encoding='utf-8')) if OUT.exists() else {'checkedOn': '', 'entries': {}}
    entries = state.get('entries', {})

    limit = 30
    if '--limit' in sys.argv:
        limit = int(sys.argv[sys.argv.index('--limit') + 1])
    retry = '--retry' in sys.argv

    todo = [
        site for site in sites
        if site['code'] not in entries or (retry and not entries[site['code']].get('programs'))
    ]
    print(f'未処理 {len(todo):,}件 / 全{len(sites):,}件。今回は最大{limit}件を処理します。')

    processed = 0
    for site in todo[:limit]:
        top = fetch(site['url'])
        time.sleep(1.0)
        if not top:
            entries[site['code']] = {'pref': site['pref'], 'name': site['name'], 'url': site['url'], 'error': 'トップページを取得できなかった'}
            processed += 1
            continue

        page = find_welfare_page(site['url'], top)

        # トップに直リンクが無ければ、「健康・福祉」などを1段挟んで探す。
        if not page:
            for gateway in find_links(site['url'], top, GATEWAY_HINTS, limit=3):
                middle = fetch(gateway)
                time.sleep(1.0)
                if not middle:
                    continue
                page = find_welfare_page(gateway, middle)
                if page:
                    break

        if not page:
            entries[site['code']] = {'pref': site['pref'], 'name': site['name'], 'url': site['url'], 'error': '障害福祉のページが見つからなかった'}
            processed += 1
            continue

        html = fetch(page)
        time.sleep(1.0)
        programs = collect(page, html) if html else []
        entries[site['code']] = {
            'pref': site['pref'],
            'name': site['name'],
            'url': site['url'],
            'welfarePage': page,
            'programs': programs,
            'fetchedOn': time.strftime('%Y-%m-%d'),
        }
        processed += 1
        print(f'  {site["pref"]}{site["name"]}: {len(programs)}件  {page}')

    state = {'checkedOn': time.strftime('%Y-%m-%d'), 'entries': entries}
    OUT.write_text(json.dumps(state, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')

    done = sum(1 for e in entries.values() if e.get('programs'))
    print(f'今回 {processed}件を処理。制度名を取得できた自治体: {done:,} / {len(sites):,}')


if __name__ == '__main__':
    main()
