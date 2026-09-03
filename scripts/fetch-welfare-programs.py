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
import urllib.robotparser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _path(name: str, default: str) -> Path:
    """data/ の下のファイル名でも、絶対パスでも受ける。

    巡回の最中に抽出の直しを試すとき、本番の出力ファイルを触らずに
    別の場所へ書けるようにしてある（同じファイルを2つのプロセスで
    書くと、片方の結果が消える）。
    """
    value = os.environ.get(name) or default
    path = Path(value)
    return path if path.is_absolute() else ROOT / 'data' / value


SITES = _path('SITES_FILE', 'municipality-sites.json')
OUT = _path('OUT_FILE', 'welfare-programs.json')
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
    # 給付を表す動詞を含まない制度名がある。「補装具」「日常生活用具」は
    # それ自体が制度の名前で、上の語をひとつも含まない。74自治体のとき、
    # これらを取りこぼしていた。
    '補装具', '日常生活用具', '手帳', '医療費', '手話', '要約筆記',
    'タクシー', '住宅改修', '駐車', '乗車', '運賃',
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


# robots.txt をホストごとに1度だけ読んで覚える。
# False は「取得できなかった」の意味で、その場合は制限なしとして扱う。
_ROBOTS: dict = {}
# 間隔の下限。robots.txt に Crawl-delay があればそちらを使う。
MIN_DELAY = 1.0


def robots(url: str):
    parts = urllib.parse.urlparse(url)
    origin = '{0}://{1}'.format(parts.scheme, parts.netloc)
    if origin not in _ROBOTS:
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(origin + '/robots.txt')
        try:
            parser.read()
        except Exception:
            parser = False
        _ROBOTS[origin] = parser
    return _ROBOTS[origin]


def allowed(url: str) -> bool:
    """robots.txt で禁じられていないか確かめる。

    741市を機械的に回すので、拒否の表明は必ず見る。robots.txt が
    無い・取得できない場合は、制限なしとして扱う（規約上の既定）。
    """
    parser = robots(url)
    if not parser:
        return True
    try:
        return parser.can_fetch(UA, url)
    except Exception:
        return True


def delay_for(url: str) -> float:
    parser = robots(url)
    if not parser:
        return MIN_DELAY
    try:
        declared = parser.crawl_delay(UA)
    except Exception:
        declared = None
    return max(MIN_DELAY, float(declared or 0))


def fetch(url: str, timeout: int = 25) -> str | None:
    if not allowed(url):
        return None
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
    finally:
        time.sleep(delay_for(url))


def ranked_links(base_url: str, html: str, hints: list, limit: int = 8) -> list:
    """手がかり語を含むリンクを、具体的な手がかりに当たったものから順に返す。

    以前は「先に出てきた3本」を辿っていた。トップページに障害福祉への
    直リンクが無い自治体では、その3本が「社会福祉協議会」のような
    関係のないリンクで埋まってしまい、そこで打ち切られていた。
    GATEWAY_HINTS は具体的なものから並べてあるので、その順で辿る。
    """
    ranked = [normalize(h) for h in hints]
    host = urllib.parse.urlparse(base_url).netloc
    found = []
    seen = set()
    for match in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.I | re.S):
        label = normalize(re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', '', match.group(2))).strip())
        if not label or len(label) > 30:
            continue
        rank = next((i for i, hint in enumerate(ranked) if hint in label), None)
        if rank is None:
            continue
        url, _fragment = urllib.parse.urldefrag(urllib.parse.urljoin(base_url, match.group(1)))
        if urllib.parse.urlparse(url).netloc != host or url in seen:
            continue
        if url.rstrip('/') == base_url.rstrip('/'):
            continue
        seen.add(url)
        found.append((rank, len(label), url))
    found.sort()
    return [url for _rank, _length, url in found[:limit]]


def find_welfare_page(top_url: str, html: str) -> str | None:
    """トップページから、障害福祉のページへのリンクを探す。

    以前は「文言が短いもの」を選んでいたが、それだと「障害」の2文字が
    「障害福祉」より優先されてしまい、相談窓口の一覧などに降りていた
    （堺市がそうなっていた）。PAGE_HINTS は具体的なものから並べてある
    ので、何番目の手がかりに当たったかで優先する。
    """
    hints = [normalize(h) for h in PAGE_HINTS]
    best = None
    host = urllib.parse.urlparse(top_url).netloc
    for match in re.finditer(r'<a[^>]+href=["\']([^"\']+)["\'][^>]*>(.*?)</a>', html, re.I | re.S):
        href, label = match.group(1), re.sub(r'<[^>]+>', '', match.group(2))
        label = normalize(label.strip())
        if not label or len(label) > 40:
            continue
        rank = next((i for i, hint in enumerate(hints) if hint in label), None)
        if rank is None:
            continue
        url = urllib.parse.urljoin(top_url, href)
        # 同じドメイン内に限る。外部サイトへ飛ぶリンクは採らない。
        if urllib.parse.urlparse(url).netloc != host:
            continue
        # URLに障害を表す綴りがあれば、より確からしいとみなす。
        in_path = 0 if re.search(r'shogai|shougai|syougai|shohai', url, re.I) else 1
        score = (rank, in_path, len(label))
        if best is None or score < best[0]:
            best = (score, url)
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


def sub_pages(page_url: str, html: str, limit: int = 8) -> list:
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
        # ページ内リンク（#本文へ など）は同じページなので落とす。
        # 残しておくと、たどる本数の枠を食いつぶす（津市がそうなっていた）。
        url, _fragment = urllib.parse.urldefrag(url)
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
    """障害福祉ページと、その下の階層から制度を集める。

    2階層でも足りない自治体がある。障害福祉の入口が「高齢・介護・障害」
    のような大きな分類で、その下に「障がい福祉の制度・サービス」があり、
    制度はさらにその下、という作りになっている（北九州市、津市）。
    2階層で1件も取れなかったときに限り、もう1段だけ降りる。
    取れているときは降りない。無駄に相手のサーバーを叩かないため。
    """
    programs = extract_programs(page_url, html)
    seen = {normalize(item['name']) for item in programs}
    children = []

    for url in sub_pages(page_url, html):
        child = fetch(url)
        if not child:
            continue
        children.append((url, child))
        for item in extract_programs(url, child):
            key = normalize(item['name'])
            if key in seen:
                continue
            seen.add(key)
            programs.append(item)
        if len(programs) >= 40:
            break

    if not programs:
        for url, child in children[:3]:
            for grandchild_url in sub_pages(url, child, limit=4):
                page = fetch(grandchild_url)
                if not page:
                    continue
                for item in extract_programs(grandchild_url, page):
                    key = normalize(item['name'])
                    if key in seen:
                        continue
                    seen.add(key)
                    programs.append(item)
                if len(programs) >= 40:
                    break
            if programs:
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
        if not top:
            why = ('robots.txt で巡回を禁じられている' if not allowed(site['url'])
                   else 'トップページを取得できなかった')
            entries[site['code']] = {'pref': site['pref'], 'name': site['name'], 'url': site['url'], 'error': why}
            processed += 1
            continue

        page = find_welfare_page(site['url'], top)

        # トップに直リンクが無ければ、「健康・福祉」などを1段挟んで探す。
        if not page:
            for gateway in ranked_links(site['url'], top, GATEWAY_HINTS, limit=8):
                middle = fetch(gateway)
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
