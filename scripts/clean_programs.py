# -*- coding: utf-8 -*-
"""収集した制度リンクから、制度そのものではないものを落とす。

巡回で拾ったリンクには、申請書PDF・事業者向けの通知・FAQ の文・
ページ内の見出しだけのカテゴリリンクが混ざっている。それらを載せると
「制度の一覧」ではなくなるため、公開前にここで落とす。
"""
import json
import re
import sys

# 添付ファイルへのリンク（[PDFファイル／92KB]、（PDF：78KB）など）
FILE_MARK = re.compile(r'(PDF|Excel|Word|ＰＤＦ|エクセル|ワード|ピーディーエフ)[^、。]{0,20}(ファイル|：|:)|[（(]\s*(PDF|Excel|Word)[^）)]*[)）]|[\[［][^\]］]*(PDF|Excel|Word|エクセル|ワード)[^\]］]*[\]］]|[（(][^）)]*(エクセル|ワード)[^）)]*[)）]', re.I)
# 申請様式そのもの
FORM = re.compile(r'(申請書|届出書|請求書|意見書|報告書|届出|申立書|同意書|委任状|記入例|様式|変更届|再交付申請)')
# 事業者・自治体内部向け
INTERNAL = re.compile(r'(事業者|事業所|指定申請|指定更新|運営規程|報酬改定|算定に係る|加算の取扱|集団指導|実地指導|自己点検|人材募集|会計年度任用|入札|公募|パブリックコメント|要綱|要領|規則|条例|向けのお知らせ|向け情報|向けお知らせ|保険医療機関|意向調査|施設整備|交付金における|区役所|市民課|保険年金課|窓口混雑|来庁予約|マイナ手続き)')
# FAQ の文、お知らせの文
SENTENCE = re.compile(r'(ですか。|でしょうか。|ください。|しています$|します$|お知らせします|について$|たい$|ませんか$|ですか$|ますか$|でしょうか$|ください$|行ってください|変わります$|わりました$|ました$|ました！$|始まりました)')
# 障害福祉と関係ないもの
OFFTOPIC = re.compile(r'(高齢者|介護保険|介護サービス|保育所|幼稚園|子育て|子ども|子供|児童手当|生活保護|保護費|住居確保|ひとり親|母子家庭|父子家庭|遺児|高等職業訓練|教育訓練給付|児童扶養手当|国民年金|新型コロナ|ワクチン|マイナンバー|住民票|戸籍|ごみ|防災|選挙)')
# 障害福祉であることを示す語（OFFTOPIC より優先する）
ONTOPIC = re.compile(r'(障害|障がい|手帳|難病|マル障|補装具|日常生活用具|自立支援医療|療育|特別児童扶養|手話|点字|補聴器|盲ろう|失語)')
# 事業者向けの区画に置かれているページ。名前だけでは住民向けと区別が
# つかないものがあるため、URLでも落とす（広島市の介護テクノロジー導入
# 支援補助金など、名前に「事業者」と入らない事業者向け補助金がある）
BUSINESS_PATH = re.compile(r'/(business|jigyou|jigyousya|jigyousha|jigyosha|office|for-business)[/-]', re.I)
# 見出しだけの短いカテゴリ名
CATEGORY = re.compile(r'^[^。]{1,7}$')
CATEGORY_WORDS = re.compile(r'^(手当|助成|給付|割引|軽減|減免|支援|貸付|年金|医療|制度|案内|一覧|その他|保険|税金|窓口|相談|サービス|届出|手続)')

# 日付や登録情報の付記を落とす
TRAILING = re.compile(r'\s*[（(]\s*\d{4}年\d{1,2}月\d{1,2}日[^）)]*[)）]\s*$')
SPACES = re.compile(r'[\s　]+')


# 制度名ではなく、ページの見出し（分類）だけのリンク。
# 「保険・年金・税金」「各種割引・減免」のように、行政の分類語を
# 中黒でつないだだけのもの。個々の制度名は入っていないので落とす。
NAV_WORDS = {
    '保険', '年金', '税金', '税', '手当', '助成', '給付', '割引', '軽減', '減免',
    '支援', '貸付', '医療', '制度', '案内', '一覧', 'その他', '相談', '窓口',
    'サービス', '届出', '手続', '手続き', '福祉', '健康', 'くらし', '暮らし',
    '生活', '補助', '交付', '共済', '免除', '補償', '在宅福祉', '費用',
}
NAV_TRIM = re.compile(r'^(各種|その他の?|主な)|(等|など|について|の?ご?案内)$')


def is_navigation(name):
    """全部が分類語なら、制度名ではない見出しとみなす。"""
    body = re.sub(r'[（(].*?[)）]', '', name)
    parts = [NAV_TRIM.sub('', p).strip() for p in re.split(r'[・･/／、,]', body)]
    parts = [p for p in parts if p]
    if not parts or len(body) > 20:
        return False
    return all(p in NAV_WORDS for p in parts)


def normalize(name):
    name = TRAILING.sub('', name)
    name = SPACES.sub(' ', name).strip()
    return name


def is_program(name):
    """制度の入口として載せる価値があるものだけ True を返す。"""
    if FILE_MARK.search(name):
        return False
    if FORM.search(name):
        return False
    if INTERNAL.search(name):
        return False
    if SENTENCE.search(name):
        return False
    if OFFTOPIC.search(name) and not ONTOPIC.search(name):
        return False
    if len(name) < 4:
        return False
    # 「給付金」「手当等」のような、中身のない見出しリンク
    if CATEGORY.match(name) and CATEGORY_WORDS.match(name) and not ONTOPIC.search(name):
        return False
    if is_navigation(name) and not ONTOPIC.search(name):
        return False
    return True


def fix_welfare_page(entry, verify=False):
    """索引から公式ページへつなぐ先を直す。

    - 事業者向けの区画を指しているものは落とす（広島市が
      /business/shogai/ を指していた。住民が開く先ではない）。
    - verify=True のときは、実際に開けるかどうかも見る。制度リンクが
      0件の自治体だけを対象にする（北区の指し先が404になっていた）。

    落とした場合、索引は公式サイトのトップへつなぐ。当て推量で別のURLを
    書くことはしない。
    """
    page = entry.get('welfarePage')
    if not page:
        return
    if BUSINESS_PATH.search(page):
        entry.pop('welfarePage', None)
        entry['welfarePageNote'] = '事業者向けの区画を指していたため外した'
        return
    if verify and not entry.get('programs'):
        import urllib.request
        req = urllib.request.Request(page, headers={'User-Agent': 'welfarejob.jp/1.0 (+https://welfarejob.jp/)'})
        try:
            with urllib.request.urlopen(req, timeout=20) as res:
                if res.status >= 400:
                    raise OSError(res.status)
        except Exception:
            entry.pop('welfarePage', None)
            entry['welfarePageNote'] = '指していたページが開けなかったため外した'


def clean(entry):
    seen_name = set()
    seen_url = set()
    out = []
    for p in entry.get('programs', []):
        name = normalize(p['name'])
        url = p['url']
        if not is_program(name) or BUSINESS_PATH.search(url):
            continue
        if name in seen_name or url in seen_url:
            continue
        seen_name.add(name)
        seen_url.add(url)
        out.append({'name': name, 'url': url})
    return out


def main():
    src = json.load(open('data/welfare-programs.json', encoding='utf-8'))
    entries = src['entries']
    total_before = total_after = 0
    verify = '--verify-pages' in sys.argv
    for code, v in entries.items():
        before = len(v.get('programs', []))
        v['programs'] = clean(v)
        fix_welfare_page(v, verify=verify)
        total_before += before
        total_after += len(v['programs'])
    src['cleanedOn'] = src['checkedOn']
    json.dump(src, open('data/welfare-programs.clean.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print('制度リンク %d件 → %d件（%d件を除外）' % (total_before, total_after, total_before - total_after))
    counts = sorted((len(v['programs']) for v in entries.values()), reverse=True)
    print('自治体あたりの件数:', counts)
    for t in (1, 3, 5, 8, 10):
        print('  %2d件以上の自治体: %d' % (t, sum(1 for c in counts if c >= t)))


if __name__ == '__main__':
    main()
