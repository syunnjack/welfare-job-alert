# -*- coding: utf-8 -*-
"""自治体ごとの障害福祉制度ページと、その索引ページを作る。

出すのは「制度名と、その自治体の公式ページへのリンク」だけにする。
金額や対象等級は自治体ごとに違い、改定もされるため転記しない
（/discount/ で書いている方針をそのまま引き継ぐ）。

制度リンクが1件でも取れた自治体には個別ページを作る。件数が少ない
ページでは、取れた件数がそれだけであることと、公式サイトの障害福祉
ページを先に見てほしいことを本文に書く。少ない一覧を、その自治体の
制度の全部であるかのように見せないため。
"""
import json
import os
import re
import sys
from html import escape

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from romaji import SUFFIX_RANK, kana_to_romaji, suffix_romaji
from program_groups import GROUPS, MIN_MUNICIPALITIES

SITE = 'https://welfarejob.jp'
OUT = 'public/seido'
# 個別ページを作る最低件数。1件でも取れていれば作る
MIN_PROGRAMS = 1
# 巡回の対象にしている自治体数。data から数えて入れ替える
TARGET_COUNT = 0

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


BY_GROUP = """
      <h2>制度名から、ほかの自治体を探す</h2>

      <p>{full}の一覧に出てきた制度のうち、ほかの自治体の公式ページもまとめているものです。</p>

      <ul class="city-list">
{links}
      </ul>
"""

KIND_LEAD = {
    'national': '<strong>{name}は国の制度です。</strong>全国どの市区町村でも窓口があります。'
                'ここに載っていない自治体に制度が無いという意味ではありません。'
                '当サイトが公式ページのリンクを確認できた自治体を並べています。',
    'local': '<strong>{name}は、市区町村や都道府県が独自に設けている制度です。</strong>'
             '設けていない自治体もあり、名称も条件も自治体ごとに違います。'
             'ここに載っていない自治体に無いとは限りません（公式ページのリンクを'
             '確認できなかっただけの場合があります）。',
    'operator': '<strong>{name}は、自治体ではなく交通事業者などが定めているものです。</strong>'
                '下の一覧は、この割引について案内している自治体の公式ページです。'
                '載っていない自治体で使えないという意味ではありません。',
}

PROGRAM_BODY = """      <header><a href="/">福祉の求人アラート</a></header>
      <nav class="crumbs"><a href="/">ホーム</a> ＞ <a href="/seido/">自治体の障害福祉制度</a> ＞ {name}</nav>

      <h1>{name}を案内している自治体</h1>

      <p class="lead">{kind_lead}</p>

      <h2>{name}とは</h2>

      <p>{about}</p>

      <h2>公式ページを確認できた自治体（{n}件）</h2>

      <ul class="programs">
{items}
      </ul>

      <p class="count">制度名は各自治体の公式ページでの表記のままです。同じ制度でも自治体によって名前が違います。</p>

      <div class="note">
        <p><strong>この一覧は「制度がある自治体の一覧」ではありません。</strong>全国の市と東京23区、あわせて{target}自治体の公式サイトを機械的にたどって、この制度に当たるページのリンクを集めたものです。サイトの作りによっては、制度があってもリンクを拾えません。</p>
        <p>お住まいの自治体が載っていない場合は、<a href="/seido/">自治体の一覧</a>からその自治体の公式ページを開くか、障害福祉の担当窓口にお尋ねください。</p>
      </div>

      <h2>金額と条件を載せていない理由</h2>

      <p>支給額、対象になる等級、所得の条件は載せていません。自治体ごとに違ううえ、年度の途中でも改定されます。当サイトに転記した時点で、いずれ実際とずれます。ずれた数字を見て窓口に行くことになるより、公式ページを直接開いていただくほうが確実です。</p>

{sources}
      <p class="sources">一覧の取得日は {checked} です。手続きの前に必ず公式ページと窓口でご確認ください。</p>
"""

# この件数を下回るページには、公式ページを先に見るよう促す注記を入れる
SCARCE_BELOW = 5

SCARCE_NOTE = """
      <div class="note">
        <p><strong>{full}の公式サイトから機械で追えたのは、この{n}件だけでした。</strong>{full}の制度がこれだけということではありません。サイトの作りによっては、制度のページまで自動でたどり着けないことがあります。</p>
        <p>制度の全体は、{full}の障害福祉のページに載っています。→ <a href="{welfare_attr}" target="_blank" rel="noopener">{full}の障害福祉のページを開く</a></p>
      </div>
"""

CITY_BODY = """      <header><a href="/">福祉の求人アラート</a></header>
      <nav class="crumbs"><a href="/">ホーム</a> ＞ <a href="/seido/">自治体の障害福祉制度</a> ＞ <a href="/seido/{slug_pref}/">{pref}</a> ＞ {name}</nav>

      <h1>{full}の障害福祉制度</h1>

      <p class="lead">{full}の公式サイトから、障害福祉に関する制度のページを<strong>{n}件</strong>見つけました。制度名と、その説明が載っている公式ページへのリンクだけを並べています。{checked}時点のものです。</p>

      <h2>制度の一覧（{n}件）</h2>

      <ul class="programs">
{items}
      </ul>

      <p class="count">リンク先はすべて {host}（{full}の公式サイト）です。</p>
{scarce}
      <h2>この一覧について</h2>

      <div class="note">
        <p><strong>金額・対象等級・所得の条件は載せていません。</strong>これらは自治体ごとに違ううえ、年度の途中でも改定されます。当サイトに転記した時点で、いずれ実際とずれます。ずれた数字を見て窓口に行くことになるより、公式ページを直接開いていただくほうが確実です。</p>
        <p>一覧は公式サイトの障害福祉のページをたどって機械的に集めたもので、<strong>{full}の制度すべてではありません。</strong>公式サイトに載っていない制度や、別の課が所管している制度は入っていません。申請書のPDFや事業者向けの通知は、制度そのものではないため除いています。</p>
      </div>

{bygroup}
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


def city_page(entry, slug_pref, slug_city, checked_on, group_links):
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
               (pref, '{0}/seido/{1}/'.format(SITE, slug_pref)),
               (full, url)]),
    ]}

    items = '\n'.join(
        '        <li><a href="{0}" target="_blank" rel="noopener">{1}</a></li>'.format(
            escape(p['url'], quote=True), escape(p['name'])) for p in progs)

    welfare = entry.get('welfarePage') or entry['url']
    # 件数が少ないときは、それが全部ではないことをその場で書く。
    # 一覧が短いほど、全部だと読まれやすいため。
    scarce = ''
    if len(progs) < SCARCE_BELOW:
        scarce = SCARCE_NOTE.format(
            full=escape(full), n=len(progs),
            welfare_attr=escape(welfare, quote=True))
    bygroup = ''
    if group_links:
        links = '\n'.join(
            '        <li><a href="/seido/program/{0}/">{1}</a></li>'.format(g['slug'], escape(g['name']))
            for g in group_links)
        bygroup = BY_GROUP.format(full=escape(full), links=links)
    body = CITY_BODY.format(
        scarce=scarce, bygroup=bygroup, slug_pref=slug_pref,
        pref=escape(pref), name=escape(name),
        full=escape(full), n=len(progs), items=items, checked=checked_on,
        host=escape(entry['url'].split('/')[2]),
        welfare_attr=escape(welfare, quote=True), welfare_text=escape(welfare),
        top_attr=escape(entry['url'], quote=True), top_text=escape(entry['url']))
    return head(title, desc, url, jsonld) + body + FOOT


def program_page(group, hits, checked_on):
    """hits: [(自治体名, 当サイトの自治体ページのURL, [制度リンク])] を件数の多い順に"""
    url = '{0}/seido/program/{1}/'.format(SITE, group['slug'])
    n = len(hits)
    name = group['name']
    title = '{0}を案内している自治体{1}件｜公式ページへのリンク｜福祉の求人アラート'.format(name, n)
    desc = ('{0}について、全国{1}自治体のうち公式ページを確認できた{2}自治体の'
            'リンクをまとめました。金額や条件は改定されるため転記していません。'
            '{3}時点。'.format(name, TARGET_COUNT, n, checked_on))

    items = []
    for muni, muni_url, progs in hits:
        inner = '／'.join(
            '<a href="{0}" target="_blank" rel="noopener">{1}</a>'.format(
                escape(p['url'], quote=True), escape(p['name'])) for p in progs)
        if muni_url:
            head_ = '<a href="{0}">{1}</a>'.format(muni_url, escape(muni))
        else:
            head_ = escape(muni)
        items.append('        <li><strong>{0}</strong><br />{1}</li>'.format(head_, inner))

    src = ''
    if group.get('sources') or group.get('related'):
        lines = []
        for label, u in group.get('sources', []):
            lines.append('        <li>{0} — <a href="{1}" target="_blank" rel="noopener">{1}</a></li>'.format(
                escape(label), escape(u, quote=True)))
        if group.get('related'):
            ru, rlabel = group['related']
            lines.append('        <li>当サイト内 — <a href="{0}">{1}</a></li>'.format(ru, escape(rlabel)))
        src = ('      <h2>出典</h2>\n\n      <ul class="sources">\n'
               + '\n'.join(lines) + '\n      </ul>\n\n')

    jsonld = {'@context': 'https://schema.org', '@graph': [
        {
            '@type': 'CollectionPage', 'name': '{0}を案内している自治体'.format(name),
            'description': desc, 'url': url, 'inLanguage': 'ja',
            'isPartOf': {'@type': 'WebSite', 'name': '福祉の求人アラート', 'url': SITE + '/'},
            'mainEntity': {
                '@type': 'ItemList', 'numberOfItems': n,
                'itemListElement': [
                    {'@type': 'ListItem', 'position': i + 1, 'name': muni,
                     'url': (SITE + muni_url) if muni_url else progs[0]['url']}
                    for i, (muni, muni_url, progs) in enumerate(hits)
                ],
            },
        },
        crumb([('福祉の求人アラート', SITE + '/'),
               ('自治体の障害福祉制度', SITE + '/seido/'),
               (name, url)]),
    ]}

    body = PROGRAM_BODY.format(
        name=escape(name),
        kind_lead=KIND_LEAD[group['kind']].format(name=escape(name)),
        about=group['about'], n=n, items='\n'.join(items),
        sources=src, checked=checked_on, target=TARGET_COUNT)
    return head(title, desc, url, jsonld) + body + FOOT


INDEX_BODY = """      <header><a href="/">福祉の求人アラート</a></header>
      <nav class="crumbs"><a href="/">ホーム</a> ＞ 自治体の障害福祉制度</nav>

      <h1>自治体の障害福祉制度を、公式ページからたどる</h1>

      <p class="lead">障害福祉の制度は市区町村ごとに違い、全国を横断した公的な一覧がありません。ここでは<strong>全国の市と東京23区、あわせて{n}自治体</strong>について、公式サイトに載っている制度{p}件へのリンクを整理しました。{checked}時点です。</p>

      <p>都道府県を選ぶと、その中の市区町村の一覧に移ります。<strong>金額や対象等級は転記していません。</strong>改定されると当サイトの表示が誤りになるためです。</p>

      <h2>都道府県から探す</h2>

{blocks}

      <h2>制度から探す</h2>

      <p>制度の名前から、その制度を案内している自治体をたどれます。同じ制度でも自治体によって呼び方が違うため、公式ページでの表記のまま並べています。</p>

      <ul class="city-list">
{programs}
      </ul>

      <h2>一覧の作り方と、含まれていないもの</h2>

      <div class="note">
        <p>総務省の全国地方公共団体コードから全国の市と東京23区、{n}自治体を機械的に選び、各自治体の公式サイトの障害福祉のページをたどって制度のリンクを集めました。自治体名ではなく団体コードで突き合わせています。巡回は robots.txt に従っています。</p>
        <p><strong>{nomatch}自治体は制度のリンクを取れていません。</strong>サイトの作りが機械で追えない形になっているためで、制度が無いという意味ではありません。無いように見せたくないので、公式ページへのリンクだけ残しています。</p>
        <p>また、障害福祉のページとは別のページを拾ってしまった自治体は、拾った内容ごと外しています。1件ずつ見ると制度らしく見えるものでも、その自治体の障害福祉のものでなければ意味がないためです。</p>
        <p>制度ごとのページは、{TARGET}自治体のうち{minmuni}自治体以上で公式ページを確認できた制度だけ作っています。少ない数の自治体から「この制度があるのはここだけ」と読めてしまう形にしないためです。</p>
        <p>個別のページを作っているのは、制度のリンクが1件でも取れた{withpage}自治体です。取れた件数が少ない自治体のページには、それが全部ではないことと、公式サイトの障害福祉のページを先に見ていただきたいことを書いています。短い一覧を、その自治体の制度の全部であるかのように見せないためです。</p>
      </div>

      <h2>制度を調べる前に</h2>

      <ol>
        <li><strong>手帳の種別と等級を控える。</strong>身体障害者手帳・療育手帳・精神障害者保健福祉手帳のどれで、何級か。ほとんどの制度がここで対象が分かれます</li>
        <li><strong>市区町村と都道府県の両方を見る。</strong>それぞれ別に制度を持っています</li>
        <li><strong>窓口に直接聞く。</strong>担当は「障害福祉課」「福祉課」などです。サイトに載っていない制度を教えてもらえることがあります</li>
      </ol>

      <p>全国共通の制度でも、申請の窓口は住んでいる市区町村です。→ <a href="/discount/">障害者手帳の割引は自分の市区町村で手続きする</a>／<a href="/discount/transport/">公共交通機関の障害者割引</a></p>
"""


def index_page(rows, checked_on, total_programs, program_rows):
    url = SITE + '/seido/'
    withpage = [r for r in rows if r['slug']]
    title = '自治体の障害福祉制度｜全国{0:,}市区町村の公式ページへの入口｜福祉の求人アラート'.format(len(rows))
    desc = ('全国{0:,}市区町村について、公式サイトに載っている障害福祉の制度{1}件への'
            'リンクを整理しました。金額や条件は転記せず、公式ページへつないでいます。'.format(len(rows), total_programs))
    jsonld = {'@context': 'https://schema.org', '@graph': [
        {
            '@type': 'CollectionPage', 'name': '自治体の障害福祉制度 一覧',
            'description': desc, 'url': url, 'inLanguage': 'ja',
            'isPartOf': {'@type': 'WebSite', 'name': '福祉の求人アラート', 'url': SITE + '/'},
            'mainEntity': {
                '@type': 'ItemList', 'numberOfItems': len({r['pref'] for r in rows}),
                'itemListElement': [
                    {'@type': 'ListItem', 'position': i + 1, 'name': pref,
                     'url': '{0}/seido/{1}/'.format(SITE, PREF_ROMAJI[pref])}
                    for i, pref in enumerate(dict.fromkeys(r['pref'] for r in rows))
                ],
            },
        },
        crumb([('福祉の求人アラート', SITE + '/'),
               ('自治体の障害福祉制度', url)]),
    ]}

    # 800近い自治体を1ページに並べると読めないので、都道府県で1段挟む。
    # /seido/tokyo/ のような中間のURLが404のままなのも直る。
    order = []
    per_pref = {}
    for r in rows:
        if r['pref'] not in per_pref:
            per_pref[r['pref']] = []
            order.append(r['pref'])
        per_pref[r['pref']].append(r)

    body_blocks = '      <ul class="city-list">{0}</ul>'.format(''.join(
        '<li><a href="/seido/{0}/">{1}</a> <span class="count">{2}/{3}自治体</span></li>'.format(
            PREF_ROMAJI[pref], escape(pref),
            sum(1 for r in per_pref[pref] if r['slug']), len(per_pref[pref]))
        for pref in order))

    programs = '\n'.join(
        '        <li><a href="/seido/program/{0}/">{1}</a> <span class="count">{2}自治体</span></li>'.format(
            g['slug'], escape(g['name']), c) for g, c in program_rows)
    body = INDEX_BODY.format(
        programs=programs,
        n=len(rows), p=total_programs, checked=checked_on, blocks=body_blocks,
        TARGET=TARGET_COUNT, minmuni=MIN_MUNICIPALITIES,
        nomatch=sum(1 for r in rows if not r['count']),
        minp=MIN_PROGRAMS, withpage=len(withpage))
    return head(title, desc, url, jsonld) + body + FOOT


PREF_BODY = """      <header><a href="/">福祉の求人アラート</a></header>
      <nav class="crumbs"><a href="/">ホーム</a> ＞ <a href="/seido/">自治体の障害福祉制度</a> ＞ {pref}</nav>

      <h1>{pref}の障害福祉制度を、市区町村から探す</h1>

      <p class="lead">{pref}の<strong>{n}自治体</strong>について、公式サイトに載っている障害福祉の制度{p}件へのリンクを整理しました。{checked}時点です。制度は市区町村ごとに違うので、住んでいる市区町村を選んでください。</p>

      <h2>市区町村を選ぶ</h2>

      <ul class="city-list">{cities}</ul>

      <p class="count">件数のついた自治体には制度の一覧があります。「未取得」は、公式サイトの作りが機械で追えず、こちらがリンクを拾えなかったものです。制度が無いという意味ではありません。その場合は公式ページへ直接つないでいます。</p>

      <h2>都道府県の制度も別にある</h2>

      <p>市区町村と都道府県は、それぞれ別に制度を持っています。両方を確認してください。{pref}の制度は{pref}の公式サイトに載っています。</p>

      <p>全国共通の制度でも、申請の窓口は住んでいる市区町村です。→ <a href="/discount/">障害者手帳の割引は自分の市区町村で手続きする</a>／<a href="/seido/">制度の名前から探す</a></p>
"""


def pref_page(pref, slug_pref, rows, checked_on):
    url = '{0}/seido/{1}/'.format(SITE, slug_pref)
    total = sum(r['count'] for r in rows)
    title = '{0}の障害福祉制度｜{1}市区町村の公式ページへの入口｜福祉の求人アラート'.format(pref, len(rows))
    desc = ('{0}の{1}市区町村について、公式サイトに載っている障害福祉の制度{2}件への'
            'リンクを整理しました。金額や条件は転記せず、公式ページへつないでいます。'
            '{3}時点。'.format(pref, len(rows), total, checked_on))
    withpage = [r for r in rows if r['slug']]
    jsonld = {'@context': 'https://schema.org', '@graph': [
        {
            '@type': 'CollectionPage', 'name': '{0}の障害福祉制度'.format(pref),
            'description': desc, 'url': url, 'inLanguage': 'ja',
            'isPartOf': {'@type': 'WebSite', 'name': '福祉の求人アラート', 'url': SITE + '/'},
            'mainEntity': {
                '@type': 'ItemList', 'numberOfItems': len(withpage),
                'itemListElement': [
                    {'@type': 'ListItem', 'position': i + 1, 'name': r['name'],
                     'url': SITE + r['slug']} for i, r in enumerate(withpage)
                ],
            },
        },
        crumb([('福祉の求人アラート', SITE + '/'),
               ('自治体の障害福祉制度', SITE + '/seido/'),
               (pref, url)]),
    ]}
    body = PREF_BODY.format(
        pref=escape(pref), n=len(rows), p=total, checked=checked_on,
        cities=''.join(city_chip(r) for r in rows))
    return head(title, desc, url, jsonld) + body + FOOT


def city_chip(r):
    if r['slug']:
        return '<li><a href="{0}">{1}</a> <span class="count">{2}件</span></li>'.format(
            r['slug'], escape(r['name']), r['count'])
    label = '公式ページへ' if r['count'] else '未取得'
    return ('<li class="plain"><a href="{0}" target="_blank" rel="noopener">{1}</a>'
            ' <span class="count">{2}</span></li>').format(
        escape(r['welfare'], quote=True), escape(r['name']), label)


def city_paths(entries, master):
    """自治体ごとのURLを決める。同じ都道府県での衝突をここで解く。

    カナから末尾（市/区/町/村）を落としてローマ字にすると、同じ都道府県に
    同じ綴りが並ぶことがある。埼玉県の三郷市と美里町がどちらも misato に
    なり、**あとに書いたほうが前のページを上書きしていた**（美里町6件が
    三郷市18件を消していた）。

    衝突したときは、市→区→町→村の順で先に来るものが素のURLを取り、
    残りは末尾を付けて分ける（misato-machi）。読みはカナのとおりに使う
    （府中町は fuchu-cho、美里町は misato-machi）。それでも並ぶときは
    団体コードを付ける。名前の順ではなくコードの順で決めるので、
    データが増えてもURLは動かない。
    """
    groups = {}
    for code, e in entries.items():
        m = master.get(code)
        if not m:
            continue
        base = kana_to_romaji(m['kana'])
        groups.setdefault((e['pref'], base), []).append((code, m['kana']))

    out = {}
    for (pref, base), members in groups.items():
        members.sort(key=lambda x: (SUFFIX_RANK.get(suffix_romaji(x[1]), 9), x[0]))
        used = set()
        for i, (code, kana) in enumerate(members):
            slug = base
            if i > 0:
                slug = '{0}-{1}'.format(base, suffix_romaji(kana) or code)
                if slug in used:
                    slug = '{0}-{1}'.format(base, code)
            used.add(slug)
            out[code] = '/seido/{0}/{1}/'.format(PREF_ROMAJI[pref], slug)
    return out


def main():
    global TARGET_COUNT
    data = json.load(open('data/welfare-programs.clean.json', encoding='utf-8'))
    checked_on = ja_date(data['checkedOn'])
    entries = data['entries']
    TARGET_COUNT = len(entries)
    # カナは municipality-sites.json に全1,741件ぶんある。URLのローマ字は
    # ここからしか作らない（漢字を読ませない）。
    master = {s['code']: s for s in json.load(
        open('data/municipality-sites.json', encoding='utf-8'))['sites']}

    # 先に自治体ページのURLを決めてしまう。制度ページから自治体ページへ、
    # 自治体ページから制度ページへ、双方向にリンクするため。
    paths = city_paths(entries, master)
    slugs = {code: path for code, path in paths.items()
             if len(entries[code]['programs']) >= MIN_PROGRAMS}

    # 制度名でまとめる
    matches = {}   # 制度のslug -> [(自治体名, 自治体ページのURL, [制度リンク])]
    per_muni = {}  # 自治体コード -> [その自治体が当たった制度グループ]
    for g in GROUPS:
        rx = re.compile(g['pattern'])
        hits = []
        for code in sorted(entries):
            e = entries[code]
            found = [p for p in e['programs'] if rx.search(p['name'])]
            if not found:
                continue
            hits.append((e['pref'] + e['name'], slugs.get(code, ''), found))
            per_muni.setdefault(code, []).append(g)
        if len(hits) >= MIN_MUNICIPALITIES:
            matches[g['slug']] = sorted(hits, key=lambda h: -len(h[2]))

    rows = []
    total = 0
    for code in sorted(entries):
        e = entries[code]
        progs = e['programs']
        total += len(progs)
        slug = slugs.get(code, '')
        if slug:
            sp, sc = slug.strip('/').split('/')[1:3]
            linked = [g for g in per_muni.get(code, []) if g['slug'] in matches]
            write(os.path.join(OUT, sp, sc, 'index.html'),
                  city_page(e, sp, sc, checked_on, linked))
        rows.append({'pref': e['pref'], 'name': e['name'], 'count': len(progs),
                     'slug': slug, 'welfare': e.get('welfarePage') or e['url']})

    program_rows = []
    for g in GROUPS:
        hits = matches.get(g['slug'])
        if not hits:
            continue
        write(os.path.join(OUT, 'program', g['slug'], 'index.html'),
              program_page(g, hits, checked_on))
        program_rows.append((g, len(hits)))

    # 都道府県のページ。800近い自治体を1ページに並べない
    pref_rows = []
    for pref in dict.fromkeys(r['pref'] for r in rows):
        mine = [r for r in rows if r['pref'] == pref]
        sp = PREF_ROMAJI[pref]
        write(os.path.join(OUT, sp, 'index.html'),
              pref_page(pref, sp, mine, checked_on))
        pref_rows.append(sp)

    write(os.path.join(OUT, 'index.html'),
          index_page(rows, checked_on, total, program_rows))

    # 前回作ったが今回は対象から外れた自治体のページを消す。
    # 制度リンクが取れなくなった自治体のページが古いまま残ると、
    # 索引から辿れないページが公開され続けるため。
    keep = {os.path.normpath(os.path.join(OUT, 'index.html'))}
    keep |= {os.path.normpath('public' + r['slug'] + 'index.html')
             for r in rows if r['slug']}
    keep |= {os.path.normpath(os.path.join(OUT, 'program', g['slug'], 'index.html'))
             for g, _c in program_rows}
    keep |= {os.path.normpath(os.path.join(OUT, sp, 'index.html'))
             for sp in pref_rows}
    removed = []
    for root, _dirs, files in os.walk(OUT):
        for name in files:
            path = os.path.normpath(os.path.join(root, name))
            if path not in keep:
                os.remove(path)
                removed.append(path)
    for root, dirs, files in os.walk(OUT, topdown=False):
        for d in dirs:
            full = os.path.join(root, d)
            if not os.listdir(full):
                os.rmdir(full)
    if removed:
        print('対象から外れたページを削除: {0}'.format(', '.join(removed)))

    urls = ['/', '/discount/', '/discount/transport/', '/seido/'] + \
           ['/seido/{0}/'.format(sp) for sp in pref_rows] + \
           ['/seido/program/{0}/'.format(g['slug']) for g, _c in program_rows] + \
           [r['slug'] for r in rows if r['slug']]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        if u == '/':
            pri = '1.0'
        elif u.count('/') == 4 and u.startswith('/seido/'):
            pri = '0.7'          # /seido/<都道府県>/<自治体>/
        else:
            pri = '0.8'
        sm.append('  <url><loc>{0}{1}</loc><priority>{2}</priority></url>'.format(SITE, u, pri))
    sm.append('</urlset>')
    write('public/sitemap.xml', '\n'.join(sm) + '\n')

    print('自治体ページ {0}枚 + 都道府県ページ {1}枚 + 制度ページ {2}枚 + 索引1枚、'
          '制度リンク {3}件、sitemap {4} URL'.format(
              sum(1 for r in rows if r['slug']), len(pref_rows),
              len(program_rows), total, len(urls)))


if __name__ == '__main__':
    main()
