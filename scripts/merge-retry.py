# -*- coding: utf-8 -*-
"""再試行の結果を data/welfare-programs.json に取り込む。

  python scripts/merge-retry.py <再試行の出力ファイル>

取り込むのは、**いま0件で、再試行では取れた自治体だけ**。すでに取れて
いる自治体は触らない。再試行で減ることもあるため、良くなった場合に
限って入れ替える。

判定には clean_programs.py の除外と信頼性の判定をそのまま使う。生の
件数で比べると、除外で全部落ちるものを「取れた」と数えてしまう。
"""
import importlib.util
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

spec = importlib.util.spec_from_file_location(
    'clean_programs', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'clean_programs.py'))
clean_programs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(clean_programs)


def usable(entry):
    """公開に足る中身が残るか。除外と信頼性の判定を通したあとの件数で見る。"""
    if not entry or not entry.get('programs'):
        return 0
    kept = clean_programs.clean(entry)
    if not clean_programs.looks_reliable(kept):
        return 0
    return len(kept)


def main():
    if len(sys.argv) < 2:
        print('再試行の出力ファイルを渡してください。')
        return 1
    retry_path = Path(sys.argv[1])
    main_path = ROOT / 'data' / 'welfare-programs.json'

    state = json.loads(main_path.read_text(encoding='utf-8'))
    entries = state['entries']
    retried = json.loads(retry_path.read_text(encoding='utf-8'))['entries']

    took = kept = 0
    names = []
    for code, new in retried.items():
        before = usable(entries.get(code))
        after = usable(new)
        if after > 0 and before == 0:
            entries[code] = new
            took += 1
            names.append('{0}{1}（{2}件）'.format(new['pref'], new['name'], after))
        else:
            kept += 1

    state['entries'] = entries
    main_path.write_text(json.dumps(state, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print('再試行 {0}件のうち、{1}件を取り込んだ（{2}件はそのまま）。'.format(
        len(retried), took, kept))
    for n in sorted(names):
        print('  ', n)
    return 0


if __name__ == '__main__':
    sys.exit(main())
