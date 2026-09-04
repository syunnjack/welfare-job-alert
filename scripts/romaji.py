# -*- coding: utf-8 -*-
"""自治体名のカナからURLに使うローマ字を作る。

自治体マスタが持っている半角カナだけを入力にする。漢字を読む処理は
入れない（読み間違いがそのままURLになるため）。
"""
import re
import unicodedata

TWO = {
    'キャ': 'kya', 'キュ': 'kyu', 'キョ': 'kyo', 'シャ': 'sha', 'シュ': 'shu', 'ショ': 'sho',
    'チャ': 'cha', 'チュ': 'chu', 'チョ': 'cho', 'ニャ': 'nya', 'ニュ': 'nyu', 'ニョ': 'nyo',
    'ヒャ': 'hya', 'ヒュ': 'hyu', 'ヒョ': 'hyo', 'ミャ': 'mya', 'ミュ': 'myu', 'ミョ': 'myo',
    'リャ': 'rya', 'リュ': 'ryu', 'リョ': 'ryo', 'ギャ': 'gya', 'ギュ': 'gyu', 'ギョ': 'gyo',
    'ジャ': 'ja', 'ジュ': 'ju', 'ジョ': 'jo', 'ビャ': 'bya', 'ビュ': 'byu', 'ビョ': 'byo',
    'ピャ': 'pya', 'ピュ': 'pyu', 'ピョ': 'pyo',
}
ONE = {
    'ア': 'a', 'イ': 'i', 'ウ': 'u', 'エ': 'e', 'オ': 'o',
    'カ': 'ka', 'キ': 'ki', 'ク': 'ku', 'ケ': 'ke', 'コ': 'ko',
    'サ': 'sa', 'シ': 'shi', 'ス': 'su', 'セ': 'se', 'ソ': 'so',
    'タ': 'ta', 'チ': 'chi', 'ツ': 'tsu', 'テ': 'te', 'ト': 'to',
    'ナ': 'na', 'ニ': 'ni', 'ヌ': 'nu', 'ネ': 'ne', 'ノ': 'no',
    'ハ': 'ha', 'ヒ': 'hi', 'フ': 'fu', 'ヘ': 'he', 'ホ': 'ho',
    'マ': 'ma', 'ミ': 'mi', 'ム': 'mu', 'メ': 'me', 'モ': 'mo',
    'ヤ': 'ya', 'ユ': 'yu', 'ヨ': 'yo',
    'ラ': 'ra', 'リ': 'ri', 'ル': 'ru', 'レ': 're', 'ロ': 'ro',
    'ワ': 'wa', 'ヲ': 'o', 'ン': 'n',
    'ガ': 'ga', 'ギ': 'gi', 'グ': 'gu', 'ゲ': 'ge', 'ゴ': 'go',
    'ザ': 'za', 'ジ': 'ji', 'ズ': 'zu', 'ゼ': 'ze', 'ゾ': 'zo',
    'ダ': 'da', 'ヂ': 'ji', 'ヅ': 'zu', 'デ': 'de', 'ド': 'do',
    'バ': 'ba', 'ビ': 'bi', 'ブ': 'bu', 'ベ': 'be', 'ボ': 'bo',
    'パ': 'pa', 'ピ': 'pi', 'プ': 'pu', 'ペ': 'pe', 'ポ': 'po',
    'ァ': 'a', 'ィ': 'i', 'ゥ': 'u', 'ェ': 'e', 'ォ': 'o', 'ャ': 'ya', 'ュ': 'yu', 'ョ': 'yo',
}
# 市区町村を表す末尾。URLには自治体名だけを入れる。
# 読みは自治体ごとに違う（府中町は「ふちゅうちょう」、美里町は「みさとまち」）。
# カナに書いてあるとおりに扱い、漢字から推測しない。
SUFFIX = {
    'シ': 'shi', 'ク': 'ku', 'チョウ': 'cho', 'マチ': 'machi',
    'ムラ': 'mura', 'ソン': 'son', 'グン': 'gun',
}
# 同じ都道府県でローマ字が衝突したとき、どれが素のURLを取るか
SUFFIX_RANK = {'shi': 0, 'ku': 1, 'cho': 2, 'machi': 2, 'mura': 3, 'son': 3, 'gun': 4, '': 5}


def split_suffix(kana):
    """カナを「自治体名」と「市区町村の別」に分ける。

    返すのは (名前のカナ, 末尾のローマ字)。末尾が無ければ ('', ) 側は空。
    """
    s = unicodedata.normalize('NFKC', kana)
    for suf in sorted(SUFFIX, key=len, reverse=True):
        if s.endswith(suf) and len(s) > len(suf):
            return s[: -len(suf)], SUFFIX[suf]
    return s, ''


def suffix_romaji(kana):
    return split_suffix(kana)[1]


def kana_to_romaji(kana):
    s = split_suffix(kana)[0]
    out = []
    i = 0
    while i < len(s):
        pair = s[i:i + 2]
        if pair in TWO:
            out.append(TWO[pair])
            i += 2
            continue
        c = s[i]
        if c == 'ッ':
            nxt = s[i + 1:i + 3]
            r = TWO.get(nxt) or ONE.get(s[i + 1], '')
            if r:
                out.append(r[0])
            i += 1
            continue
        if c == 'ー':
            i += 1
            continue
        out.append(ONE.get(c, ''))
        i += 1
    r = ''.join(out)
    # 長音は母音を重ねずに書く（コウチ → kochi、オオサカ → osaka）
    r = re.sub(r'ou|oo', 'o', r)
    r = re.sub(r'uu', 'u', r)
    return r
