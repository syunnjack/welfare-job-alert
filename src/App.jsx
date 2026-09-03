import { useMemo, useState } from 'react'
import './App.css'

const saveKey = 'welfare-job-alert.saved'

// 掲載しているのは表示例。実際の求人情報とは連動していないため、
// 読者が実在の募集と誤解しないよう、タイトルと画面上の注記で「表示例」と明示する。
const alerts = [
  {
    "id": "welfare-job-alert-1",
    "title": "名古屋の障害者雇用の求人（表示例）",
    "area": "名古屋",
    "category": "障害者雇用",
    "summary": "勤務地、勤務時間、通院への配慮など、決めた条件に合う募集が出たときにお知らせします。求人票のどこを見ればよいかも一緒に載せます。",
    "channels": [
      "LINE",
      "X"
    ],
    "tags": [
      "障害者雇用",
      "条件を指定",
      "みんなの投稿"
    ]
  },
  {
    "id": "welfare-job-alert-2",
    "title": "東京の福祉の仕事の求人（表示例）",
    "area": "東京",
    "category": "福祉求人",
    "summary": "介護、保育、生活支援など、福祉の現場の募集をまとめてお知らせします。夜勤の有無や資格の条件で絞り込めます。",
    "channels": [
      "LINE",
      "X",
      "メール"
    ],
    "tags": [
      "福祉求人",
      "資格で絞る",
      "みんなの投稿"
    ]
  },
  {
    "id": "welfare-job-alert-3",
    "title": "大阪の支援員の求人（表示例）",
    "area": "大阪",
    "category": "支援員",
    "summary": "就労支援や生活介護などの支援員の募集をお知らせします。未経験から応募できるか、研修があるかも合わせて確認できます。",
    "channels": [
      "LINE",
      "X",
      "メール",
      "Slack"
    ],
    "tags": [
      "支援員",
      "未経験可",
      "みんなの投稿"
    ]
  },
  {
    "id": "welfare-job-alert-4",
    "title": "静岡の事業所からの募集（表示例）",
    "area": "静岡",
    "category": "事業所",
    "summary": "福祉事業所が出した募集をお知らせします。事業所の方は、募集を載せて求職中の方に届けることができます。",
    "channels": [
      "LINE",
      "X"
    ],
    "tags": [
      "事業所",
      "募集を載せる",
      "みんなの投稿"
    ]
  }
]

const faqs = [
  ['障害者雇用枠と一般枠は何が違いますか？', '障害者雇用枠は、障害があることを勤め先に伝えたうえで応募する枠です。通院や勤務時間への配慮を相談しやすい一方、募集している職種が限られることがあります。違いは企業ごとに異なるので、気になる求人それぞれで確認してください。'],
  ['障害者手帳は必要ですか？', '障害者雇用枠の求人では、手帳を持っていることを条件にしている場合が多くあります。ただし条件は求人ごとに違うため、応募の前に募集要項をご確認ください。'],
  ['求人を探すほかに相談できる場所はありますか？', 'お住まいの地域のハローワーク（障害のある方の相談窓口）、地域障害者職業センター、就労移行支援事業所などで相談できます。求人探しと並行して使えます。'],
]

// 通知の届け先。実際に送信できるものだけを並べる。
// 以前は LINE / X / メール / Slack のラベルが出ていたが、送信処理も
// 登録先も無かった。押せそうに見えて何も起きない状態だったため、
// 実装したものだけを出すようにした。
const deliveryChannels = [
  { id: 'email', label: 'メール', hint: '確認メールが届きます' },
  { id: 'line', label: 'LINE', hint: '公式アカウントを友だち追加してから登録してください' },
]

// 登録先。未設定のときは登録欄を出さず、その旨を書く。
// 匿名キーは公開してよい値で、守りはデータベース側の RLS。
const SUPABASE_URL = import.meta.env.VITE_SUPABASE_URL || ''
const SUPABASE_ANON_KEY = import.meta.env.VITE_SUPABASE_ANON_KEY || ''
const canSubscribe = Boolean(SUPABASE_URL && SUPABASE_ANON_KEY)

function readArray(key) {
  try { return JSON.parse(localStorage.getItem(key)) ?? [] } catch { return [] }
}

// Xの共有は認証がいらないので、リンクだけで本当に動く。
function shareUrl(alert) {
  const text = `${alert.area}の${alert.category}の求人を探しています`
  const url = 'https://welfarejob.jp/'
  return `https://x.com/intent/post?text=${encodeURIComponent(text)}&url=${encodeURIComponent(url)}`
}

function App() {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('すべて')
  const [saved, setSaved] = useState(() => readArray(saveKey))
  const [form, setForm] = useState({ area: '', category: '障害者雇用', conditions: '', channel: 'email', address: '' })
  const [state, setState] = useState({ status: 'idle', message: '' })
  const categories = ['すべて', ...new Set(alerts.map((item) => item.category))]

  const filtered = useMemo(() => alerts.filter((item) => {
    const text = [item.title, item.area, item.category, item.summary, item.tags.join(' ')].join(' ')
    return text.includes(query) && (category === 'すべて' || item.category === category)
  }), [query, category])

  function toggleSave(id) {
    const next = saved.includes(id) ? saved.filter((item) => item !== id) : [...saved, id]
    setSaved(next)
    localStorage.setItem(saveKey, JSON.stringify(next))
  }

  async function subscribe(event) {
    event.preventDefault()
    if (!canSubscribe) return
    if (!form.area.trim() || !form.address.trim()) {
      setState({ status: 'error', message: '地域と届け先を入力してください。' })
      return
    }
    setState({ status: 'sending', message: '' })
    try {
      const response = await fetch(`${SUPABASE_URL}/rest/v1/job_alert_subscriptions`, {
        method: 'POST',
        headers: {
          'apikey': SUPABASE_ANON_KEY,
          'Authorization': `Bearer ${SUPABASE_ANON_KEY}`,
          'Content-Type': 'application/json',
          'Prefer': 'return=minimal',
        },
        body: JSON.stringify({
          area: form.area.trim(),
          category: form.category,
          conditions: form.conditions.trim() || null,
          channel: form.channel,
          address: form.address.trim(),
        }),
      })
      if (response.status === 409) {
        setState({ status: 'error', message: 'その届け先と地域の組み合わせは、すでに登録されています。' })
        return
      }
      if (!response.ok) throw new Error(`status ${response.status}`)
      setState({
        status: 'done',
        message: form.channel === 'email'
          ? '登録を受け付けました。確認のメールをお送りしますので、本文のリンクを開いてください。開くまで通知は始まりません。'
          : '登録を受け付けました。LINEの公式アカウントから確認のメッセージをお送りします。',
      })
      setForm({ area: '', category: '障害者雇用', conditions: '', channel: form.channel, address: '' })
    } catch {
      setState({ status: 'error', message: '登録できませんでした。時間をおいて、もう一度お試しください。' })
    }
  }

  return (
    <main className="app-shell">
      <section className="hero">
        <div>
          <p className="eyebrow">障害者雇用と福祉の仕事の求人通知</p>
          <h1>福祉の求人アラート</h1>
          <p className="lead">障害者雇用枠の求人と、支援員など福祉の仕事の募集を、条件に合ったときにお知らせします。勤務地、勤務時間、配慮してほしいことから探せます。</p>
        </div>
        <aside className="hero-panel">
          <span>welfarejob.jp</span>
          <strong>毎日探し続けなくても、条件に合えば届く。</strong>
          <p>通知の届け先はメールとLINEです。求人カードは表示例で、実際の募集とは連動していません。地域ごとに、対応でき次第お知らせを始めます。</p>
          <p><a href="/seido/">お住まいの自治体の障害福祉制度を調べる</a>／<a href="/discount/">障害者手帳の割引の調べ方</a></p>
        </aside>
      </section>
      <section className="controls" aria-label="検索条件">
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="地域や仕事の種類で探す" />
        <select value={category} onChange={(event) => setCategory(event.target.value)}>{categories.map((item) => <option key={item}>{item}</option>)}</select>
      </section>
      <section className="metrics">
        <article><span>掲載中の例</span><strong>{alerts.length}</strong></article>
        <article><span>通知の届け先</span><strong>{deliveryChannels.length}</strong></article>
        <article><span>保存した数</span><strong>{saved.length}</strong></article>
        <article><span>登録の状態</span><strong>{canSubscribe ? '受付中' : '準備中'}</strong></article>
      </section>
      <section className="alert-grid">
        {filtered.map((alert) => (
          <article className="alert-card" key={alert.id}>
            <div className="card-top"><span>{alert.area} / {alert.category}</span></div>
            <h2>{alert.title}</h2>
            <p>{alert.summary}</p>
            <div className="tag-row">{alert.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>
            <div className="channel-row">
              <a href={shareUrl(alert)} target="_blank" rel="noopener">Xで共有</a>
              <a href="#subscribe" onClick={() => setForm((prev) => ({ ...prev, area: alert.area, category: alert.category }))}>この地域の通知を受け取る</a>
            </div>
            <button type="button" onClick={() => toggleSave(alert.id)}>{saved.includes(alert.id) ? '保存済み' : 'あとで見るために保存'}</button>
          </article>
        ))}
      </section>
      <section className="split">
        <div className="panel">
          <h2>使い方</h2>
          <article><b>1. 条件を決める</b><p>通える範囲、働ける時間帯、相談したい配慮など、ゆずれない条件を決めます。</p></article>
          <article><b>2. 届け先を登録する</b><p>メールかLINEを選び、確認の手続きまで済ませます。確認が済むまで通知は届きません。</p></article>
          <article><b>3. 気になった募集を保存する</b><p>あとで見返せるように保存できます。応募の前に、募集要項と配慮の内容を確認してください。</p></article>
          <article><b>いまの状態</b><p>求人カードは表示例です。通知は、対応できた地域から順に配信を始めます。登録は先に受け付けています。</p></article>
        </div>
        <div className="panel" id="subscribe">
          <h2>求人通知を受け取る</h2>
          {canSubscribe ? (
            <>
              <p>探している地域と届け先を登録してください。確認の手続きが済んだ方から、条件に合う募集が出たときにお知らせします。いつでも解除できます。</p>
              <form className="ugc-form" onSubmit={subscribe}>
                <input value={form.area} onChange={(event) => setForm({ ...form, area: event.target.value })} placeholder="通える地域（例: 名古屋市、東京23区）" required />
                <select value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })}>
                  {[...new Set(alerts.map((item) => item.category))].map((item) => <option key={item}>{item}</option>)}
                </select>
                <select value={form.channel} onChange={(event) => setForm({ ...form, channel: event.target.value })}>
                  {deliveryChannels.map((item) => <option key={item.id} value={item.id}>{item.label}</option>)}
                </select>
                <input
                  value={form.address}
                  onChange={(event) => setForm({ ...form, address: event.target.value })}
                  type={form.channel === 'email' ? 'email' : 'text'}
                  placeholder={form.channel === 'email' ? 'メールアドレス' : 'LINEのユーザーID'}
                  required
                />
                <input value={form.conditions} onChange={(event) => setForm({ ...form, conditions: event.target.value })} placeholder="働ける時間帯、配慮してほしいこと、資格など（任意）" />
                <button disabled={state.status === 'sending'}>{state.status === 'sending' ? '送信中…' : '登録する'}</button>
              </form>
              <p className="empty">{deliveryChannels.find((item) => item.id === form.channel)?.hint}</p>
              {state.message && <p className="empty">{state.message}</p>}
              <p className="empty">登録いただいた届け先は通知の送信にだけ使い、他の目的では使いません。他の利用者から見えることはありません。</p>
            </>
          ) : (
            <p className="empty">通知の登録は準備中です。受け付けを始めるまで、登録欄は出していません。動かない入力欄を置いておくより、状態をそのまま書いておきます。</p>
          )}
        </div>
      </section>
      <section className="seo-section">
        <h2>これから増やしていくもの</h2>
        <div className="seo-grid">
          <article><b>地域ごとのページ</b><p>市区町村や沿線ごとに、通える範囲の求人をまとめます。</p></article>
          <article><b>働き方ごとのページ</b><p>短時間勤務、在宅勤務、通院への配慮、未経験から始められる仕事など、条件から探せるようにします。</p></article>
          <article><b>制度の調べ方</b><p><a href="/seido/">自治体ごとの障害福祉制度</a>と<a href="/discount/">障害者手帳の割引</a>について、手続きの窓口と確かめ方をまとめています。</p></article>
        </div>
      </section>
      <section className="faq-section">
        <h2>よくある質問</h2>
        <div className="faq-grid">{faqs.map(([q, a]) => <article key={q}><h3>{q}</h3><p>{a}</p></article>)}</div>
      </section>
    </main>
  )
}

export default App
