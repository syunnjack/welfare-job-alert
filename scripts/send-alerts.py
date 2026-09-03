"""登録された届け先に、確認メッセージと求人のお知らせを送る。

この画面には以前 LINE / X / メール / Slack のラベルが並んでいたが、
登録先も送信処理も無く、押しても何も起きなかった。その実体を作る。

やること:
  1. 未確認の登録に、確認メッセージを送る（メール / LINE）
     確認が済むまで通知は送らない。いたずら登録で他人に送りつけないため
  2. 確認済みの登録に、条件に合う求人を送る
     求人データ（data/jobs.json）が無いときは、ここは何もしない

必要な環境変数:
  SUPABASE_URL / SUPABASE_SERVICE_ROLE   登録の読み書き（RLSを迂回する）
  LINE_CHANNEL_ACCESS_TOKEN              LINE Messaging API の push に使う
  RESEND_API_KEY / MAIL_FROM             メール送信に使う

**サービスロールキーとアクセストークンは、絶対にリポジトリへ置かない。**
GitHub Secrets に入れ、環境変数で渡す。

使い方:
  python scripts/send-alerts.py            送信する
  python scripts/send-alerts.py --dry-run  送らずに、対象だけ出す
"""
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

SITE_URL = 'https://welfarejob.jp'
TABLE = 'job_alert_subscriptions'
JOBS_FILE = Path(__file__).resolve().parent.parent / 'data' / 'jobs.json'

DRY_RUN = '--dry-run' in sys.argv


def api(path: str, method: str = 'GET', payload=None):
    """Supabase の REST を叩く。サービスロールキーなので RLS は効かない。"""
    base = os.environ['SUPABASE_URL'].rstrip('/')
    key = os.environ['SUPABASE_SERVICE_ROLE']
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(f'{base}/rest/v1/{path}', data=data, method=method, headers={
        'apikey': key,
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
        'Prefer': 'return=representation',
    })
    with urllib.request.urlopen(request, timeout=45) as response:
        body = response.read().decode()
        return json.loads(body) if body else []


def send_mail(to: str, subject: str, text: str) -> bool:
    key = os.environ.get('RESEND_API_KEY')
    sender = os.environ.get('MAIL_FROM')
    if not key or not sender:
        print(f'  メールの設定が無いので送れません: {to}', file=sys.stderr)
        return False
    payload = json.dumps({'from': sender, 'to': [to], 'subject': subject, 'text': text}).encode()
    request = urllib.request.Request('https://api.resend.com/emails', data=payload, method='POST', headers={
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json',
    })
    try:
        with urllib.request.urlopen(request, timeout=45):
            return True
    except urllib.error.HTTPError as error:
        print(f'  メール送信に失敗: {to} / {error.code} {error.read().decode()[:200]}', file=sys.stderr)
        return False


def send_line(user_id: str, text: str) -> bool:
    token = os.environ.get('LINE_CHANNEL_ACCESS_TOKEN')
    if not token:
        print(f'  LINEの設定が無いので送れません: {user_id}', file=sys.stderr)
        return False
    payload = json.dumps({'to': user_id, 'messages': [{'type': 'text', 'text': text}]}).encode()
    request = urllib.request.Request('https://api.line.me/v2/bot/message/push', data=payload, method='POST', headers={
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    })
    try:
        with urllib.request.urlopen(request, timeout=45):
            return True
    except urllib.error.HTTPError as error:
        print(f'  LINE送信に失敗: {user_id} / {error.code} {error.read().decode()[:200]}', file=sys.stderr)
        return False


def deliver(row: dict, text: str, subject: str) -> bool:
    if DRY_RUN:
        print(f'  [dry-run] {row["channel"]} → {row["address"]}: {text.splitlines()[0]}')
        return True
    if row['channel'] == 'email':
        return send_mail(row['address'], subject, text)
    return send_line(row['address'], text)


def send_confirmations() -> int:
    """未確認の登録に、確認のリンクを送る。"""
    query = urllib.parse.urlencode({
        'select': 'id,area,category,channel,address,confirm_token',
        'confirmed_at': 'is.null',
        'unsubscribed_at': 'is.null',
        'order': 'created_at.asc',
        'limit': 200,
    })
    rows = api(f'{TABLE}?{query}')
    if not rows:
        return 0

    sent = 0
    for row in rows:
        link = f'{SITE_URL}/confirm/?token={row["confirm_token"]}'
        text = (
            '福祉の求人アラートの登録を受け付けました。\n\n'
            f'地域: {row["area"]}\n'
            f'種類: {row["category"]}\n\n'
            '下のリンクを開くと、通知が始まります。\n'
            f'{link}\n\n'
            'このリンクを開くまで通知は送りません。\n'
            'お心当たりが無い場合は、何もせず削除してください。'
        )
        if deliver(row, text, '【福祉の求人アラート】登録の確認'):
            sent += 1
    return sent


def load_jobs() -> list:
    if not JOBS_FILE.exists():
        return []
    with JOBS_FILE.open(encoding='utf-8') as handle:
        data = json.load(handle)
    return data.get('jobs', [])


def send_job_alerts(jobs: list) -> int:
    """確認済みの登録に、条件に合う求人を送る。"""
    query = urllib.parse.urlencode({
        'select': 'id,area,category,conditions,channel,address',
        'confirmed_at': 'not.is.null',
        'unsubscribed_at': 'is.null',
        'limit': 500,
    })
    rows = api(f'{TABLE}?{query}')
    sent = 0

    for row in rows:
        # 地域と種類が一致するものだけ。あいまいな推測で送らない。
        matched = [
            job for job in jobs
            if row['area'] in job.get('area', '') and job.get('category') == row['category']
        ]
        if not matched:
            continue

        lines = [f'{row["area"]}の{row["category"]}の募集が {len(matched)}件 出ています。', '']
        for job in matched[:5]:
            lines += [f'・{job.get("title", "")}', f'  {job.get("url", "")}', '']
        lines += ['通知を止めるときは、このメッセージに返信するか、下のページから解除してください。', f'{SITE_URL}/']

        if deliver(row, '\n'.join(lines), '【福祉の求人アラート】条件に合う募集'):
            sent += 1
            if not DRY_RUN:
                api(f'{TABLE}?id=eq.{row["id"]}', method='PATCH', payload={'last_sent_at': 'now()'})
    return sent


def main() -> None:
    if not os.environ.get('SUPABASE_URL') or not os.environ.get('SUPABASE_SERVICE_ROLE'):
        print('環境変数 SUPABASE_URL と SUPABASE_SERVICE_ROLE が必要です。', file=sys.stderr)
        raise SystemExit(1)

    confirmations = send_confirmations()
    print(f'確認メッセージ: {confirmations}件')

    jobs = load_jobs()
    if not jobs:
        print('求人データ（data/jobs.json）がありません。お知らせの送信はしません。')
        print('求人の取得元をつなぐまで、送れるのは確認メッセージだけです。')
        return

    alerts = send_job_alerts(jobs)
    print(f'求人のお知らせ: {alerts}件（求人 {len(jobs)}件から照合）')


if __name__ == '__main__':
    main()
