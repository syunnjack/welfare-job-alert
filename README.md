# Welfare Job Alert

障害者雇用枠の求人と、福祉の仕事の募集を通知するサイト。本番は https://welfarejob.jp

## Concept

障害者雇用、福祉事業所、支援員求人を通知し、人材送客、事業所掲載、相談導線へつなげる。

## Technical Selection

- Frontend: Vite + React 19
- Styling: Plain CSS
- Initial data: Static alert seed records in `src/App.jsx`
- Local state: localStorage for MVP saved alerts and UGC requests
- Notification integrations: LINE Messaging API, X API, transactional email provider, Slack Incoming Webhooks
- Future data layer: Supabase or Cloudflare D1
- SEO/AIO/LLMO: structured data, answer block, FAQ, sitemap, robots and `llms.txt`

## Revenue Paths

- 人材送客
- 事業所掲載
- 相談送客
- 広告
- 資料請求

## Commands

```bash
npm install
npm run dev
npm run lint
npm run build
```
