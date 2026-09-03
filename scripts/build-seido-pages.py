# -*- coding: utf-8 -*-
"""自治体ごとの障害福祉制度ページと、その索引ページを作る。

出すのは「制度名と、その自治体の公式ページへのリンク」だけにする。
金額や対象等級は自治体ごとに違い、改定もされるため転記しない
（/discount/ で書いている方針をそのまま引き継ぐ）。

制度リンクが少ない自治体には個別ページを作らない。数件のリンクを
定型文で挟んだだけのページを並べても、読む人には公式サイトを開く
以上の意味がないため。索引から公式ページへ直接つなぐ。
"""
import json
import os
import sys
from html import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from romaji import kana_to_romaji

SITE = 'https://welfarejob.jp'
OUT = 'public/seido'
# 個別ページを作る最低件数
MIN_PROGRAMS = 5

PREF_ROMAJI = {
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

STYLE = """
      :root { color-scheme: light dark; }
      * { box-sizing: border-box; }
      body { margin: 0; font-family: "Hiragino Sans", "Yu Gothic", system-ui, sans-serif; line-height: 1.9; color: #1c2331; background: #f6f8fb; }
      .wrap { max-width: 760px; margin: 0 auto; padding: 28px 20px 64px; }
      header a { color: #2a5b9a; font-weight: 700; text-decoration: none; }
      nav.crumbs { font-size: 13px; color: #5c6a80; margin: 14px 0 26px; }
      nav.crumbs a { color: #2a5b9a; }
      h1 { font-size: 25px; line-height: 1.5; margin: 0 0 18px; }
      h2 { font-size: 19px; margin: 40px 0 12px; padding-left: 11px; border-left: 4px solid #2a5b9a; }
      h3 { font-size: 16px; margin: 26px 0 8px; }
      p, li { font-size: 15px; }
      .lead { background: #fff; border: 1px solid #dfe5ee; border-radius: 10px; padding: 16px 18px; }
      .note { background: #fff8e6; border: 1px solid #e8d9a8; border-radius: 10px; padding: 14px 18px; font-size: 14px; }
      .programs { list-style: none; padding: 0; margin: 14px 0; }
      .programs li { background: #fff; border: 1px solid #dfe5ee; border-radius: 8px; margin-bottom: 8px; padding: 11px 14px; }
      .programs li a { text-decoration: none; font-weight: 600; }
      .programs li a:hover { text-decoration: underline; }
      table { width: 100%; border-collapse: collapse; margin: 14px 0; font-size: 14px; }
      th, td { border: 1px solid #dfe5ee; padding: 9px 11px; text-align: left; vertical-align: top; background: #fff; }
      th { background: #eef2f8; white-space: nowrap; }
      .pref-block { margin: 18px 0; }
      .pref-block h3 { margin: 0 0 6px; font-size: 15px; color: #5c6a80; }
      .city-list { list-style: none; padding: 0; margin: 0; display: flex; flex-wrap: wrap; gap: 7px; }
      .city-list li { background: #fff; border: 1px solid #dfe5ee; border-radius: 999px; padding: 5px 13px; font-size: 14px; margin: 0; }
      .city-list li.plain { color: #5c6a80; }
      .count { color: #5c6a80; font-size: 13px; }
      ol li, ul li { margin-bottom: 7px; }
      .sources { font-size: 14px; }
      footer { margin-top: 48px; padding-top: 18px; border-top: 1px solid #dfe5ee; font-size: 13px; color: #5c6a80; }
      a { color: #2a5b9a; }
      @media (prefers-color-scheme: dark) {
        body { background: #12161d; color: #e6eaf2; }
        .lead, th, td, .programs li, .city-list li { background: #1b212b; border-color: #2c3542; }
        th { background: #232b37; }
        .note { background: #26210f; border-color: #4a3f1c; }
        footer { border-color: #2c3542; color: #9aa7bb; }
        a, header a { color: #7fb0f0; }
        .city-list li.plain, .count, .pref-block h3 { color: #9aa7bb; }
      }
"""

GA = """    <script async src="https://www.googletagmanager.com/gtag/js?id=G-9EL2LHTB5P"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){dataLayer.push(arguments);}
      gtag('js', new Date());
      gtag('config', 'G-9EL2LHTB5P');
    </script>
"""

HEAD = """<!doctype html>
<html lang="ja">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>{title}</title>
    <meta name="description" content="{desc}" />
    <link rel="canonical" href="{url}" />
    <meta property="og:title" content="{title}" />
    <meta property="og:description" content="{desc}" />
    <meta property="og:type" content="article" />
    <meta property="og:url" content="{url}" />
    <meta property="og:site_name" content="福祉の求人アラート" />
    <meta property="og:locale" content="ja_JP" />
    <link rel="icon" href="/favicon.svg" />
    <script type="application/ld+json">{jsonld}</script>
{ga}    <style>{style}</style>
  </head>
  <body>
    <div class="wrap">
"""

FOOT = """
      <footer>
        <p>記載内容の誤りに気づかれた場合は、お知らせください。確認のうえ訂正します。</p>
        <p><a href="/">福祉の求人アラート トップへ</a>　<a href="/seido/">自治体の障害福祉制度</a>　<a href="/discount/">障害者手帳の割引</a></p>
      </footer>
    </div>
  </body>
</html>
"""


def head(title, desc, url, jsonld):
    return HEAD.format(
        title=escape(title), desc=escape(desc), url=url,
        jsonld=json.dumps(jsonld, ensure_ascii=False, separators=(',', ':')),
        ga=GA, style=STYLE)


def ja_date(iso):
    """2026-09-03 を 2026年9月3日 と書く。本文に出す日付は日本語の形にする。"""
    y, m, d = iso.split('-')
    return '{0}年{1}月{2}日'.format(int(y), int(m), int(d))


def crumb(items):
    return {
        '@type': 'BreadcrumbList',
        'itemListElement': [
            {'@type': 'ListItem', 'position': i + 1, 'name': n, 'item': u}
            for i, (n, u) in enumerate(items)
        ],
    }


def write(path, text):
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(text)


CITY_BODY = """      <header><a href="/">福祉の求人アラート</a></header>
      <nav class="crumbs"><a href="/">ホーム</a> ＞ <a href="/seido/">自治体の障害福祉制度</a> ＞ {full}</nav>

      <h1>{full}の障害福祉制度</h1>

      <p class="lead">{full}の公式サイトから、障害福祉に関する制度のページを<strong>{n}件</strong>見つけました。制度名と、その説明が載っている公式ページへのリンクだけを並べています。{checked}時点のものです。</p>

      <h2>制度の一覧（{n}件）</h2>

      <ul class="programs">
{items}
      </ul>

      <p class="count">リンク先はすべて {host}（{full}の公式サイト）です。</p>

      <h2>この一覧について</h2>

      <div class="note">
        <p><strong>金額・対象等級・所得の条件は載せていません。</strong>これらは自治体ごとに違ううえ、年度の途中でも改定されます。当サイトに転記した時点で、いずれ実際とずれます。ずれた数字を見て窓口に行くことになるより、公式ページを直接開いていただくほうが確実です。</p>
        <p>一覧は公式サイトの障害福祉のページをたどって機械的に集めたもので、<strong>{full}の制度すべてではありません。</strong>公式サイトに載っていない制度や、別の課が所管している制度は入っていません。申請書のPDFや事業者向けの通知は、制度そのものではないため除いています。</p>
      </div>

      <h2>窓口で確かめる</h2>

      <p>制度の対象になるかどうかは、手帳の種別と等級で決まることがほとんどです。手帳を手元に置いて、{full}の障害福祉の担当窓口にお尋ねください。「障害者手帳を持っています。使える制度の一覧はありますか」と聞くのが早いです。</p>

      <p>都道府県の制度は、市区町村の制度とは別にあります。両方をご確認ください。全国共通の制度でも、申請の窓口は市区町村です。→ <a href="/discount/">障害者手帳の割引は自分の市区町村で手続きする</a></p>

      <h2>出典</h2>

      <ul class="sources">
        <li>{full} 障害福祉のページ — <a href="{welfare_attr}" target="_blank" rel="noopener">{welfare_text}</a></li>
        <li>{full} 公式サイト — <a href="{top_attr}" target="_blank" rel="noopener">{top_text}</a></li>
      </ul>

      <p class="sources">一覧の取得日は {checked} です。制度は改定されることがあるため、手続きの前に必ず公式ページと窓口でご確認ください。</p>
"""


def city_page(entry, slug_pref, slug_city, checked_on):
    pref, name = entry['pref'], entry['name']
    full = pref + name
    progs = entry['programs']
    url = '{0}/seido/{1}/{2}/'.format(SITE, slug_pref, slug_city)
    title = '{0}の障害福祉制度 {1}件｜公式ページへのリンク｜福祉の求人アラート'.format(full, len(progs))
    desc = ('{0}の公式サイトに載っている障害福祉の制度を{1}件、制度名と公式ページへのリンクでまとめました。'
            '金額や対象等級は改定されるため転記していません。{2}時点。'.format(full, len(progs), checked_on))
    jsonld = {'@context': 'https://schema.org', '@graph': [
        {
            '@type': 'CollectionPage',
            'name': '{0}の障害福祉制度'.format(full),
            'description': desc,
            'url': url,
            'inLanguage': 'ja',
            'isPartOf': {'@type': 'WebSite', 'name': '福祉の求人アラート', 'url': SITE + '/'},
            'mainEntity': {
                '@type': 'ItemList',
                'numberOfItems': len(progs),
                'itemListElement': [
                    {'@type': 'ListItem', 'position': i + 1, 'name': p['name'], 'url': p['url']}
                    for i, p in enumerate(progs)
                ],
            },
        },
        crumb([('福祉の求人アラート', SITE + '/'),
               ('自治体の障害福祉制度', SITE + '/seido/'),
               (full, url)]),
    ]}

    items = '\n'.join(
        '        <li><a href="{0}" target="_blank" rel="noopener">{1}</a></li>'.format(
            escape(p['url'], quote=True), escape(p['name'])) for p in progs)

    welfare = entry.get('welfarePage') or entry['url']
    body = CITY_BODY.format(
        full=escape(full), n=len(progs), items=items, checked=checked_on,
        host=escape(entry['url'].split('/')[2]),
        welfare_attr=escape(welfare, quote=True), welfare_text=escape(welfare),
        top_attr=escape(entry['url'], quote=True), top_text=escape(entry['url']))
    return head(title, desc, url, jsonld) + body + FOOT


INDEX_BODY = """      <header><a href="/">福祉の求人アラート</a></header>
      <nav class="crumbs"><a href="/">ホーム</a> ＞ 自治体の障害福祉制度</nav>

      <h1>自治体の障害福祉制度を、公式ページからたどる</h1>

      <p class="lead">障害福祉の制度は市区町村ごとに違い、全国を横断した公的な一覧がありません。ここでは<strong>県庁所在地・政令指定都市・東京23区の{n}自治体</strong>について、公式サイトに載っている制度{p}件へのリンクを整理しました。{checked}時点です。</p>

      <p>自治体名を選ぶと、その自治体の制度の一覧に移ります。<strong>金額や対象等級は転記していません。</strong>改定されると当サイトの表示が誤りになるためです。</p>

      <h2>自治体を選ぶ</h2>

{blocks}

      <h2>一覧の作り方と、含まれていないもの</h2>

      <div class="note">
        <p>総務省の全国地方公共団体コードから対象の{n}自治体を機械的に選び、各自治体の公式サイトの障害福祉のページをたどって制度のリンクを集めました。自治体名ではなく団体コードで突き合わせています。</p>
        <p><strong>{nomatch}自治体は制度のリンクを取れていません。</strong>サイトの作りが機械で追えない形になっているためで、制度が無いという意味ではありません。無いように見せたくないので、公式ページへのリンクだけ残しています。</p>
        <p>個別のページを作っているのは、制度のリンクが{minp}件以上あった{withpage}自治体です。数件しか取れなかった自治体は、公式ページへ直接つないでいます。数件のリンクを説明文で挟んだだけのページを並べても、公式サイトを開く以上のことにならないためです。</p>
      </div>

      <h2>制度を調べる前に</h2>

      <ol>
        <li><strong>手帳の種別と等級を控える。</strong>身体障害者手帳・療育手帳・精神障害者保健福祉手帳のどれで、何級か。ほとんどの制度がここで対象が分かれます</li>
        <li><strong>市区町村と都道府県の両方を見る。</strong>それぞれ別に制度を持っています</li>
        <li><strong>窓口に直接聞く。</strong>担当は「障害福祉課」「福祉課」などです。サイトに載っていない制度を教えてもらえることがあります</li>
      </ol>

      <p>全国共通の制度でも、申請の窓口は住んでいる市区町村です。→ <a href="/discount/">障害者手帳の割引は自分の市区町村で手続きする</a>／<a href="/discount/transport/">公共交通機関の障害者割引</a></p>
"""


def index_page(rows, checked_on, total_programs):
    url = SITE + '/seido/'
    withpage = [r for r in rows if r['slug']]
    title = '自治体の障害福祉制度 一覧｜主要{0}市区町村の公式ページへの入口｜福祉の求人アラート'.format(len(rows))
    desc = ('県庁所在地・政令指定都市・東京23区の{0}自治体について、公式サイトに載っている障害福祉の制度{1}件への'
            'リンクを整理しました。金額や条件は転記せず、公式ページへつないでいます。'.format(len(rows), total_programs))
    jsonld = {'@context': 'https://schema.org', '@graph': [
        {
            '@type': 'CollectionPage', 'name': '自治体の障害福祉制度 一覧',
            'description': desc, 'url': url, 'inLanguage': 'ja',
            'isPartOf': {'@type': 'WebSite', 'name': '福祉の求人アラート', 'url': SITE + '/'},
            'mainEntity': {
                '@type': 'ItemList', 'numberOfItems': len(withpage),
                'itemListElement': [
                    {'@type': 'ListItem', 'position': i + 1,
                     'name': r['pref'] + r['name'], 'url': SITE + r['slug']}
                    for i, r in enumerate(withpage)
                ],
            },
        },
        crumb([('福祉の求人アラート', SITE + '/'),
               ('自治体の障害福祉制度', url)]),
    ]}

    blocks = []
    cur = None
    lis = []
    for r in rows:
        if r['pref'] != cur:
            if cur is not None:
                blocks.append((cur, lis))
            cur, lis = r['pref'], []
        if r['slug']:
            lis.append('<li><a href="{0}">{1}</a> <span class="count">{2}件</span></li>'.format(
                r['slug'], escape(r['name']), r['count']))
        else:
            label = '公式ページへ' if r['count'] else '未取得'
            lis.append('<li class="plain"><a href="{0}" target="_blank" rel="noopener">{1}</a> <span class="count">{2}</span></li>'.format(
                escape(r['welfare'], quote=True), escape(r['name']), label))
    if cur is not None:
        blocks.append((cur, lis))

    body_blocks = '\n'.join(
        '      <div class="pref-block"><h3>{0}</h3><ul class="city-list">{1}</ul></div>'.format(
            escape(pref), ''.join(lis)) for pref, lis in blocks)

    body = INDEX_BODY.format(
        n=len(rows), p=total_programs, checked=checked_on, blocks=body_blocks,
        nomatch=sum(1 for r in rows if not r['count']),
        minp=MIN_PROGRAMS, withpage=len(withpage))
    return head(title, desc, url, jsonld) + body + FOOT


def main():
    data = json.load(open('data/welfare-programs.clean.json', encoding='utf-8'))
    checked_on = ja_date(data['checkedOn'])
    entries = data['entries']
    master = {s['code']: s for s in json.load(
        open('data/priority-municipalities.json', encoding='utf-8'))['sites']}

    rows = []
    total = 0
    for code in sorted(entries):
        e = entries[code]
        m = master.get(code)
        progs = e['programs']
        total += len(progs)
        slug = ''
        if len(progs) >= MIN_PROGRAMS and m:
            sp = PREF_ROMAJI[e['pref']]
            sc = kana_to_romaji(m['kana'])
            slug = '/seido/{0}/{1}/'.format(sp, sc)
            write(os.path.join(OUT, sp, sc, 'index.html'),
                  city_page(e, sp, sc, checked_on))
        rows.append({'pref': e['pref'], 'name': e['name'], 'count': len(progs),
                     'slug': slug, 'welfare': e.get('welfarePage') or e['url']})

    write(os.path.join(OUT, 'index.html'), index_page(rows, checked_on, total))

    urls = ['/', '/discount/', '/discount/transport/', '/seido/'] + \
           [r['slug'] for r in rows if r['slug']]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        pri = '1.0' if u == '/' else ('0.7' if u.startswith('/seido/') and u != '/seido/' else '0.8')
        sm.append('  <url><loc>{0}{1}</loc><priority>{2}</priority></url>'.format(SITE, u, pri))
    sm.append('</urlset>')
    write('public/sitemap.xml', '\n'.join(sm) + '\n')

    print('個別ページ {0}枚 + 索引1枚、制度リンク {1}件、sitemap {2} URL'.format(
        len(urls) - 4, total, len(urls)))


if __name__ == '__main__':
    main()
