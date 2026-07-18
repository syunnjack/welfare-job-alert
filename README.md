# Welfare Job Alert

障害者雇用・福祉系求人通知

## Repository

Recommended repository name: `welfare-job-alert`

## Domain candidates

First candidate: `welfarejob.jp`

Other candidates:

- `welfarejob.jp`
- `fukushijob.jp`
- `supportwork.jp`
- `inclusivejob.jp`

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
