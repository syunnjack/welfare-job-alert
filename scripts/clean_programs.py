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
FILE_MARK = re.compile(r'(PDF|Excel|Word|ＰＤＦ)[^、。]{0,20}(ファイル|：|:)|[（(]\s*(PDF|Excel|Word)[^）)]*[)）]|[\[［][^\]］]*(PDF|Excel|Word)[^\]］]*[\]］]', re.I)
# 申請様式そのもの
FORM = re.compile(r'(申請書|届出書|請求書|意見書|報告書|届出|申立書|同意書|委任状|記入例|様式|変更届|再交付申請)')
# 事業者・自治体内部向け
INTERNAL = re.compile(r'(事業者|事業所|指定申請|指定更新|運営規程|報酬改定|算定に係る|加算の取扱|集団指導|実地指導|自己点検|人材募集|会計年度任用|入札|公募|パブリックコメント|要綱|要領|規則|条例|向けのお知らせ|向け情報|向けお知らせ|保険医療機関|意向調査|施設整備|交付金における)')
# FAQ の文、お知らせの文
SENTENCE = re.compile(r'(ですか。|でしょうか。|ください。|しています$|します$|お知らせします|について$|たい$|ませんか$|ください$|行ってください|変わります$|わりました$)')
# 障害福祉と関係ないもの
OFFTOPIC = re.compile(r'(高齢者|介護保険|介護サービス|保育所|幼稚園|子育て|子ども|子供|児童手当|生活保護|保護費|住居確保|ひとり親|国民年金|新型コロナ|ワクチン|マイナンバー|住民票|戸籍|ごみ|防災|選挙)')
# 障害福祉であることを示す語（OFFTOPIC より優先する）
ONTOPIC = re.compile(r'(障害|障がい|手帳|難病|マル障|補装具|日常生活用具|自立支援医療|療育|特別児童扶養|手話|点字|補聴器|盲ろう|失語)')
# 見出しだけの短いカテゴリ名
CATEGORY = re.compile(r'^[^。]{1,7}$')
CATEGORY_WORDS = re.compile(r'^(手当|助成|給付|割引|軽減|減免|支援|貸付|年金|医療|制度|案内|一覧|その他)')

# 日付や登録情報の付記を落とす
TRAILING = re.compile(r'\s*[（(]\s*\d{4}年\d{1,2}月\d{1,2}日[^）)]*[)）]\s*$')
SPACES = re.compile(r'[\s　]+')


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
    return True


def clean(entry):
    seen_name = set()
    seen_url = set()
    out = []
    for p in entry.get('programs', []):
        name = normalize(p['name'])
        url = p['url']
        if not is_program(name):
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
    for code, v in entries.items():
        before = len(v.get('programs', []))
        v['programs'] = clean(v)
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
