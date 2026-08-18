import { useMemo, useState } from 'react'
import './App.css'

const saveKey = 'welfare-job-alert.saved'
const postKey = 'welfare-job-alert.posts'

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

const channels = [
  "LINE",
  "X",
  "メール",
  "Slack"
]

const faqs = [
  ['障害者雇用枠と一般枠は何が違いますか？', '障害者雇用枠は、障害があることを勤め先に伝えたうえで応募する枠です。通院や勤務時間への配慮を相談しやすい一方、募集している職種が限られることがあります。違いは企業ごとに異なるので、気になる求人それぞれで確認してください。'],
  ['障害者手帳は必要ですか？', '障害者雇用枠の求人では、手帳を持っていることを条件にしている場合が多くあります。ただし条件は求人ごとに違うため、応募の前に募集要項をご確認ください。'],
  ['求人を探すほかに相談できる場所はありますか？', 'お住まいの地域のハローワーク（障害のある方の相談窓口）、地域障害者職業センター、就労移行支援事業所などで相談できます。求人探しと並行して使えます。'],
]

function readArray(key) {
  try { return JSON.parse(localStorage.getItem(key)) ?? [] } catch { return [] }
}

function App() {
  const [query, setQuery] = useState('')
  const [category, setCategory] = useState('すべて')
  const [saved, setSaved] = useState(() => readArray(saveKey))
  const [posts, setPosts] = useState(() => readArray(postKey))
  const [form, setForm] = useState({ title: '', channel: 'LINE', memo: '' })
  const categories = ['すべて', ...new Set(alerts.map((item) => item.category))]

  const filtered = useMemo(() => alerts.filter((item) => {
    const text = [item.title, item.area, item.category, item.summary, item.channels.join(' '), item.tags.join(' ')].join(' ')
    return text.includes(query) && (category === 'すべて' || item.category === category)
  }), [query, category])

  function toggleSave(id) {
    const next = saved.includes(id) ? saved.filter((item) => item !== id) : [...saved, id]
    setSaved(next)
    localStorage.setItem(saveKey, JSON.stringify(next))
  }

  function addPost(event) {
    event.preventDefault()
    if (!form.title.trim() || !form.memo.trim()) return
    const next = [{ ...form, id: crypto.randomUUID(), date: new Date().toLocaleDateString('ja-JP') }, ...posts]
    setPosts(next)
    localStorage.setItem(postKey, JSON.stringify(next))
    setForm({ title: '', channel: 'LINE', memo: '' })
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
          <p>LINE、X、メール、Slackのうち、普段使っているところに通知が届きます。いまは表示例を公開している段階です。</p>
        </aside>
      </section>
      <section className="controls" aria-label="検索条件">
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="地域や仕事の種類で探す" />
        <select value={category} onChange={(event) => setCategory(event.target.value)}>{categories.map((item) => <option key={item}>{item}</option>)}</select>
      </section>
      <section className="metrics">
        <article><span>掲載中の例</span><strong>{alerts.length}</strong></article>
        <article><span>通知の届け先</span><strong>{channels.length}</strong></article>
        <article><span>保存した数</span><strong>{saved.length}</strong></article>
        <article><span>投稿した数</span><strong>{posts.length}</strong></article>
      </section>
      <section className="alert-grid">
        {filtered.map((alert) => (
          <article className="alert-card" key={alert.id}>
            <div className="card-top"><span>{alert.area} / {alert.category}</span></div>
            <h2>{alert.title}</h2>
            <p>{alert.summary}</p>
            <div className="tag-row">{alert.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>
            <div className="channel-row">{alert.channels.map((channel) => <span key={channel}>{channel}</span>)}</div>
            <button type="button" onClick={() => toggleSave(alert.id)}>{saved.includes(alert.id) ? '保存済み' : 'あとで見るために保存'}</button>
          </article>
        ))}
      </section>
      <section className="split">
        <div className="panel">
          <h2>使い方</h2>
          <article><b>1. 条件を決める</b><p>通える範囲、働ける時間帯、相談したい配慮など、ゆずれない条件を決めます。</p></article>
          <article><b>2. 通知の届け先を選ぶ</b><p>LINE、X、メール、Slackから、普段見ているものを選びます。</p></article>
          <article><b>3. 気になった募集を保存する</b><p>あとで見返せるように保存できます。応募の前に、募集要項と配慮の内容を確認してください。</p></article>
          <article><b>いまの状態</b><p>公開しているのは表示例です。通知の受け付けは準備中で、対応する地域から順に始めます。</p></article>
        </div>
        <div className="panel">
          <h2>探している条件を教えてください</h2>
          <p>どの地域の、どんな働き方を探しているかを教えてください。要望の多い地域と条件から対応していきます。投稿はこの端末にだけ保存されます。</p>
          <form className="ugc-form" onSubmit={addPost}>
            <input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} placeholder="地域や仕事の種類" />
            <input value={form.channel} onChange={(event) => setForm({ ...form, channel: event.target.value })} placeholder="通知の届け先（LINE / X / メール / Slack）" />
            <input value={form.memo} onChange={(event) => setForm({ ...form, memo: event.target.value })} placeholder="働ける時間帯、配慮してほしいこと、資格など" />
            <button>送る</button>
          </form>
          <div className="post-list">
            {posts.length === 0 && <p className="empty">まだ投稿はありません。探している条件を教えていただけると、対応する地域を決める手がかりになります。</p>}
            {posts.map((post) => <article key={post.id}><b>{post.title}</b><p>{post.memo}</p><small>{post.channel} / {post.date}</small></article>)}
          </div>
        </div>
      </section>
      <section className="seo-section">
        <h2>これから増やしていくもの</h2>
        <div className="seo-grid">
          <article><b>地域ごとのページ</b><p>市区町村や沿線ごとに、通える範囲の求人をまとめます。</p></article>
          <article><b>働き方ごとのページ</b><p>短時間勤務、在宅勤務、通院への配慮、未経験から始められる仕事など、条件から探せるようにします。</p></article>
          <article><b>事業所の方向けの案内</b><p>募集を掲載したい福祉事業所の方へ、掲載の方法をご案内します。</p></article>
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
