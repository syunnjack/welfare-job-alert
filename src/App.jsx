import { useMemo, useState } from 'react'
import './App.css'

const saveKey = 'welfare-job-alert.saved'
const postKey = 'welfare-job-alert.posts'
const alerts = [
  {
    "id": "welfare-job-alert-1",
    "title": "障害者雇用 alert seed 1",
    "area": "名古屋",
    "category": "障害者雇用",
    "score": 95,
    "summary": "障害者雇用、福祉事業所、支援員求人を通知し、人材送客、事業所掲載、相談導線へつなげる。 障害者雇用の条件一致時に通知し、保存、送客、課金へつなげます。",
    "channels": [
      "LINE",
      "X"
    ],
    "tags": [
      "障害者雇用",
      "通知",
      "UGC",
      "収益導線"
    ],
    "revenue": "人材送客"
  },
  {
    "id": "welfare-job-alert-2",
    "title": "福祉求人 alert seed 2",
    "area": "東京",
    "category": "福祉求人",
    "score": 92,
    "summary": "障害者雇用、福祉事業所、支援員求人を通知し、人材送客、事業所掲載、相談導線へつなげる。 福祉求人の条件一致時に通知し、保存、送客、課金へつなげます。",
    "channels": [
      "LINE",
      "X",
      "メール"
    ],
    "tags": [
      "福祉求人",
      "通知",
      "UGC",
      "収益導線"
    ],
    "revenue": "事業所掲載"
  },
  {
    "id": "welfare-job-alert-3",
    "title": "支援員 alert seed 3",
    "area": "大阪",
    "category": "支援員",
    "score": 89,
    "summary": "障害者雇用、福祉事業所、支援員求人を通知し、人材送客、事業所掲載、相談導線へつなげる。 支援員の条件一致時に通知し、保存、送客、課金へつなげます。",
    "channels": [
      "LINE",
      "X",
      "メール",
      "Slack"
    ],
    "tags": [
      "支援員",
      "通知",
      "UGC",
      "収益導線"
    ],
    "revenue": "相談送客"
  },
  {
    "id": "welfare-job-alert-4",
    "title": "事業所 alert seed 4",
    "area": "静岡",
    "category": "事業所",
    "score": 86,
    "summary": "障害者雇用、福祉事業所、支援員求人を通知し、人材送客、事業所掲載、相談導線へつなげる。 事業所の条件一致時に通知し、保存、送客、課金へつなげます。",
    "channels": [
      "LINE",
      "X"
    ],
    "tags": [
      "事業所",
      "通知",
      "UGC",
      "収益導線"
    ],
    "revenue": "広告"
  }
]
const revenuePlans = [
  "人材送客",
  "事業所掲載",
  "相談送客",
  "広告",
  "資料請求"
]
const channels = [
  "LINE",
  "X",
  "メール",
  "Slack"
]
const faqs = [
  ['通知からどう収益化しますか？', '無料通知で接点を作り、条件一致時に予約、掲載、クーポン、有料通知、スポンサー枠へ誘導します。'],
  ['LINE・X・メール・Slackの使い分けは？', 'LINEは個人の即時通知、Xは拡散、メールは週次まとめ、Slackは店舗や法人運用向けです。'],
  ['SEO/AIO/LLMOの狙いは？', '地域名、カテゴリ、条件、通知、口コミ、FAQを組み合わせたロングテールページを作ります。'],
]

function readArray(key) {
  try { return JSON.parse(localStorage.getItem(key)) ?? [] } catch { return [] }
}

function App() {
  const [query, setQuery] = useState('名古屋')
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
          <p className="eyebrow">障害者雇用・福祉系求人通知</p>
          <h1>Welfare Job Alert</h1>
          <p className="lead">障害者雇用、福祉事業所、支援員求人を通知し、人材送客、事業所掲載、相談導線へつなげる。</p>
        </div>
        <aside className="hero-panel">
          <span>welfarejob.jp / welfare-job-alert</span>
          <strong>通知の瞬間に、予約・掲載・クーポン・有料導線へつなげる。</strong>
          <p>LINE、X、メール、Slackを入口に、UGCで鮮度を作りながら収益導線を太くします。</p>
        </aside>
      </section>
      <section className="controls" aria-label="検索条件">
        <input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="地域・カテゴリ・通知条件で検索" />
        <select value={category} onChange={(event) => setCategory(event.target.value)}>{categories.map((item) => <option key={item}>{item}</option>)}</select>
      </section>
      <section className="metrics">
        <article><span>Alert seeds</span><strong>{alerts.length}</strong></article>
        <article><span>Channels</span><strong>{channels.length}</strong></article>
        <article><span>Saved</span><strong>{saved.length}</strong></article>
        <article><span>UGC</span><strong>{posts.length}</strong></article>
      </section>
      <section className="alert-grid">
        {filtered.map((alert) => (
          <article className="alert-card" key={alert.id}>
            <div className="card-top"><span>{alert.area} / {alert.category}</span><b>{alert.score}</b></div>
            <h2>{alert.title}</h2>
            <p>{alert.summary}</p>
            <div className="tag-row">{alert.tags.map((tag) => <span key={tag}>{tag}</span>)}</div>
            <div className="channel-row">{alert.channels.map((channel) => <span key={channel}>{channel}</span>)}</div>
            <p className="revenue">収益導線: {alert.revenue}</p>
            <button type="button" onClick={() => toggleSave(alert.id)}>{saved.includes(alert.id) ? '保存済み' : '通知導線に保存'}</button>
          </article>
        ))}
      </section>
      <section className="split">
        <div className="panel">
          <h2>技術選定</h2>
          <article><b>Frontend</b><p>Vite + React 19。静的MVPとして軽く、GitHub Pagesへ展開しやすい構成です。</p></article>
          <article><b>通知連携</b><p>初期はUI設計、次段階でLINE Messaging API、X API、SendGrid/Mailgun、Slack Incoming Webhooksを接続します。</p></article>
          <article><b>Data</b><p>MVPは静的seed + localStorage。運用時はSupabaseまたはCloudflare D1へ移行します。</p></article>
          <article><b>収益ルート</b><p>{revenuePlans.join(' / ')}</p></article>
        </div>
        <div className="panel">
          <h2>UGC・通知リクエスト</h2>
          <p>現地確認、在庫、空席、価格、閉店、口コミ、通知希望条件を集めて、鮮度と検索ページを増やします。</p>
          <form className="ugc-form" onSubmit={addPost}>
            <input value={form.title} onChange={(event) => setForm({ ...form, title: event.target.value })} placeholder="通知リクエスト名" />
            <input value={form.channel} onChange={(event) => setForm({ ...form, channel: event.target.value })} placeholder="LINE / X / メール / Slack" />
            <input value={form.memo} onChange={(event) => setForm({ ...form, memo: event.target.value })} placeholder="条件・口コミ・現地メモ" />
            <button>投稿</button>
          </form>
          <div className="post-list">
            {posts.length === 0 && <p className="empty">公開後は通知希望とUGCで鮮度を作ります。</p>}
            {posts.map((post) => <article key={post.id}><b>{post.title}</b><p>{post.memo}</p><small>{post.channel} / {post.date}</small></article>)}
          </div>
        </div>
      </section>
      <section className="seo-section">
        <h2>SEO / AIO / LLMO</h2>
        <div className="seo-grid">
          <article><b>地域ページ</b><p>地域名、駅名、施設名ごとに通知ニーズを拾います。</p></article>
          <article><b>条件ページ</b><p>空き、値下げ、閉店、在庫、混雑、期限など行動直前の検索を狙います。</p></article>
          <article><b>法人ページ</b><p>掲載、スポンサー、Slack通知、レポート、SaaS契約へつなげます。</p></article>
        </div>
      </section>
      <section className="faq-section">
        <h2>FAQ</h2>
        <div className="faq-grid">{faqs.map(([q, a]) => <article key={q}><h3>{q}</h3><p>{a}</p></article>)}</div>
      </section>
    </main>
  )
}

export default App
