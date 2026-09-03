# -*- coding: utf-8 -*-
"""制度名でまとめるためのグループ定義。

集めた制度リンクは自治体ごとに名前が違う（「特別障害者手当」「特別障害者
手当の支給」「特別障害者手当 障害児福祉手当（国制度）」）。同じ制度を指す
ものをここでまとめ、制度名から自治体を引けるようにする。

`kind` は、その制度が誰の制度かを表す。国の制度なら全国の市区町村が窓口に
なるので「載っていない自治体には無い」とは言えない。逆に自治体独自の制度は
本当に無いことがある。この違いをページに書き分けるために持たせている。

`source` は根拠を確かめられる公式ページ。すべて実際に開いて表題を確認した。
"""

MHLW_TEATE = ('厚生労働省「特別児童扶養手当・特別障害者手当等」',
              'https://www.mhlw.go.jp/bunya/shougaihoken/jidou/index.html')
MHLW_JIRITSU = ('厚生労働省「自立支援医療」',
                'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/shougaishahukushi/jiritsu/index.html')
MHLW_YOGU = ('厚生労働省「福祉用具」（補装具費支給制度）',
             'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/shougaishahukushi/yogu/index.html')
MHLW_CHIIKI = ('厚生労働省「地域生活支援事業」',
               'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/shougaishahukushi/chiiki/index.html')
MHLW_TECHO = ('厚生労働省「身体障害者手帳」',
              'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/shougaishahukushi/shougaishatechou/index.html')
MHLW_HOJOKEN = ('厚生労働省「身体障害者補助犬」',
                'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/hukushi_kaigo/shougaishahukushi/hojoken/index.html')
MHLW_NANBYO = ('厚生労働省「難病対策」',
               'https://www.mhlw.go.jp/stf/seisakunitsuite/bunya/kenkou_iryou/kenkou/nanbyou/index.html')
NEXCO = ('NEXCO西日本「有料道路における障がい者割引制度についてのご案内」',
         'https://www.w-nexco.co.jp/etc/handicapped/guidance.html')

# kind: 'national' = 国の制度。全国の市区町村が窓口になる
#       'local'    = 自治体が独自に設ける制度。有無が自治体で違う
#       'operator' = 交通事業者など、自治体以外が決めている割引
GROUPS = [
    {
        'slug': 'tokubetsu-shogaisha-teate',
        'name': '特別障害者手当',
        'kind': 'national',
        'pattern': r'特別障害者手当|特別障がい者手当',
        'about': '20歳以上で在宅の方のうち、著しく重度の障害があり、日常生活で常時特別の介護を必要とする方に支給される国の手当です。根拠は特別児童扶養手当等の支給に関する法律で、申請と支給の窓口は住んでいる市区町村になります。',
        'sources': [MHLW_TEATE],
    },
    {
        'slug': 'shogaiji-fukushi-teate',
        'name': '障害児福祉手当',
        'kind': 'national',
        'pattern': r'障害児福祉手当|障がい児福祉手当',
        'about': '20歳未満で在宅の方のうち、重度の障害があり、日常生活で常時の介護を必要とする方に支給される国の手当です。特別障害者手当と同じ法律にもとづく制度で、窓口は市区町村です。',
        'sources': [MHLW_TEATE],
    },
    {
        'slug': 'tokubetsu-jido-fuyo-teate',
        'name': '特別児童扶養手当',
        'kind': 'national',
        'pattern': r'特別児童扶養手当',
        'about': '20歳未満の障害のある児童を育てている父母などに支給される国の手当です。児童本人ではなく、育てている方に支給されます。申請の窓口は市区町村です。',
        'sources': [MHLW_TEATE],
    },
    {
        'slug': 'jichitai-fukushi-teate',
        'name': '自治体独自の福祉手当（心身障害者福祉手当など）',
        'kind': 'local',
        'pattern': r'心身障害者福祉手当|心身障がい者福祉手当|障害者福祉手当|障がい者福祉手当|重度心身障害者手当|心身障害児福祉手当|心身障がい児福祉手当',
        'about': '国の手当とは別に、市区町村や都道府県が独自に設けている手当です。「心身障害者福祉手当」「重度心身障害者手当」など名称が自治体ごとに違い、対象になる等級も違います。設けていない自治体もあります。',
        'sources': [],
    },
    {
        'slug': 'judo-shinshin-iryohi',
        'name': '重度心身障害者の医療費助成（マル障など）',
        'kind': 'local',
        'pattern': r'重度心身障害|重度心身障がい|心身障害者医療費|心身障がい者医療費|障害者医療費|障がい者医療費|マル障|福祉医療費',
        'about': '重度の障害がある方の医療費の自己負担を助成する、都道府県と市区町村の制度です。国の制度ではないため、名称（マル障、福祉医療費助成など）も対象になる等級も自治体ごとに違います。',
        'sources': [],
    },
    {
        'slug': 'jiritsu-shien-iryo',
        'name': '自立支援医療',
        'kind': 'national',
        'pattern': r'自立支援医療',
        'about': '障害者総合支援法にもとづく、医療費の自己負担を軽くする国の制度です。更生医療（18歳以上）、育成医療（18歳未満）、精神通院医療の3つに分かれます。申請の窓口は市区町村です。',
        'sources': [MHLW_JIRITSU],
    },
    {
        'slug': 'hosogu',
        'name': '補装具費の支給',
        'kind': 'national',
        'pattern': r'補装具',
        'about': '義肢、装具、車椅子、補聴器などの購入・修理にかかる費用を支給する、障害者総合支援法にもとづく国の制度です。申請の窓口は市区町村で、判定が必要な種目もあります。',
        'sources': [MHLW_YOGU],
    },
    {
        'slug': 'nichijo-seikatsu-yogu',
        'name': '日常生活用具の給付',
        'kind': 'national',
        'pattern': r'日常生活用具',
        'about': '入浴補助用具、意思伝達装置、住宅改修費などを給付する制度です。地域生活支援事業として市区町村が必ず行う事業ですが、<strong>どの品目を対象にするかは市区町村が決めます</strong>。そのため対象になる用具が自治体で違います。',
        'sources': [MHLW_CHIIKI],
    },
    {
        'slug': 'shuwa-tsuyaku',
        'name': '手話通訳者・要約筆記者の派遣',
        'kind': 'national',
        'pattern': r'手話通訳|要約筆記|意思疎通支援',
        'about': '聴覚障害などで意思疎通に支障がある方のために、手話通訳者や要約筆記者を派遣する制度です。意思疎通支援事業として、市区町村が必ず行う事業に位置づけられています。派遣の申込み方法や対象の場面は自治体で違います。',
        'sources': [MHLW_CHIIKI],
    },
    {
        'slug': 'tenji-daihitsu',
        'name': '点字・代筆代読などの意思疎通支援',
        'kind': 'national',
        'pattern': r'点字|代筆|代読|盲ろう|失語',
        'about': '点字による情報提供、代筆・代読の支援、盲ろう者向け通訳・介助員の派遣など、手話通訳以外の意思疎通支援です。地域生活支援事業の一部で、どこまで行うかは自治体で幅があります。',
        'sources': [MHLW_CHIIKI],
    },
    {
        'slug': 'shogaisha-techo',
        'name': '障害者手帳の交付',
        'kind': 'national',
        'pattern': r'手帳の交付|手帳交付|手帳の申請',
        'about': '身体障害者手帳（身体障害者福祉法）、療育手帳（国の通知にもとづく制度）、精神障害者保健福祉手帳（精神保健福祉法）の3種類があります。申請の窓口は市区町村で、交付するのは都道府県・指定都市・中核市です。ほとんどの制度が、この手帳の種別と等級で対象を分けています。',
        'sources': [MHLW_TECHO],
    },
    {
        'slug': 'fukushi-taxi',
        'name': '福祉タクシー・移送サービスの助成',
        'kind': 'local',
        'pattern': r'福祉タクシー|タクシー(料金|券|利用|助成)|移送サービス|福祉有償運送',
        'about': '通院や外出にタクシーを使うときの費用を助成する、市区町村独自の制度です。利用券を配る形が多いですが、有無も、対象になる等級も、助成の形も自治体ごとに違います。',
        'sources': [],
    },
    {
        'slug': 'jidosha-nenryohi',
        'name': '自動車燃料費の助成',
        'kind': 'local',
        'pattern': r'自動車燃料|ガソリン|給油券|燃料費',
        'about': '障害のある方や介護する家族が使う自動車の燃料費を助成する、市区町村独自の制度です。福祉タクシー券とどちらか一方を選ぶ形にしている自治体もあります。',
        'sources': [],
    },
    {
        'slug': 'jidosha-kaizohi',
        'name': '自動車改造費の助成',
        'kind': 'local',
        'pattern': r'自動車改造|車(両)?改造',
        'about': '障害のある方が自分で運転するために自動車を改造する費用を助成する制度です。市区町村や都道府県が独自に設けており、就労のために運転する方を対象にしている自治体もあります。',
        'sources': [],
    },
    {
        'slug': 'unten-menkyo',
        'name': '運転免許取得費の助成',
        'kind': 'local',
        'pattern': r'免許(の)?取得|運転免許',
        'about': '障害のある方が自動車運転免許を取る費用を助成する、市区町村や都道府県独自の制度です。就労や通勤に必要であることを条件にしている自治体があります。',
        'sources': [],
    },
    {
        'slug': 'hochoki',
        'name': '補聴器購入費の助成',
        'kind': 'local',
        'pattern': r'補聴器',
        'about': '身体障害者手帳の対象にならない軽度・中等度の難聴の方（とくに児童）に、補聴器の購入費を助成する自治体独自の制度です。手帳の対象になる方は、国の補装具費の支給が使えます。',
        'sources': [MHLW_YOGU],
    },
    {
        'slug': 'kami-omutsu',
        'name': '紙おむつの支給・助成',
        'kind': 'local',
        'pattern': r'おむつ',
        'about': '紙おむつを支給する、または購入費を助成する制度です。日常生活用具の一部として行う自治体と、独自の事業として行う自治体があります。対象になる条件は自治体で違います。',
        'sources': [],
    },
    {
        'slug': 'hojoken',
        'name': '身体障害者補助犬（盲導犬・介助犬・聴導犬）',
        'kind': 'national',
        'pattern': r'補助犬|盲導犬|介助犬|聴導犬',
        'about': '身体障害者補助犬法にもとづく制度です。公共施設や店舗などは、補助犬を同伴した方の受け入れを拒めないことになっています。補助犬の給付は都道府県や市が行います。',
        'sources': [MHLW_HOJOKEN],
    },
    {
        'slug': 'nanbyo',
        'name': '難病患者への支援',
        'kind': 'national',
        'pattern': r'難病',
        'about': '指定難病の医療費助成は、都道府県と指定都市が行います。これとは別に、市区町村が難病の方に日常生活用具を給付するなどの支援を行っている場合があります。',
        'sources': [MHLW_NANBYO],
    },
    {
        'slug': 'yuryo-doro',
        'name': '有料道路（高速道路）の割引',
        'kind': 'national',
        'pattern': r'有料道路|高速道路',
        'about': '全国共通の割引制度ですが、<strong>申請の窓口は住んでいる市区町村</strong>です。手帳の種別と等級の確認を市区町村が行うためです。割引率と有効期限は全国で同じです。',
        'sources': [NEXCO],
        'related': ('/discount/transport/', '公共交通機関の障害者割引（割引率と条件つき）'),
    },
    {
        'slug': 'kotsu-waribiki',
        'name': '鉄道・バス・航空運賃の割引',
        'kind': 'operator',
        'pattern': r'(鉄道|JR|バス|航空|旅客|運賃|乗車).{0,8}(割引|軽減|助成|乗車証|無料)',
        'about': 'JRや民営バスなどの運賃割引は、自治体の制度ではなく<strong>各交通事業者が運賃規則で定めているもの</strong>です。手帳を提示すれば全国で使えます。これとは別に、市区町村が独自に配る福祉乗車証や乗車券の助成があります。',
        'sources': [],
        'related': ('/discount/transport/', '公共交通機関の障害者割引（割引率と条件つき）'),
    },
]

# ページを作る最低の自治体数。これを下回るグループはページにしない
MIN_MUNICIPALITIES = 5
