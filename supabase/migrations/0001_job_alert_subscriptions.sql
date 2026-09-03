-- 求人通知の購読登録。
--
-- 通知の届け先（LINEのユーザーID、メールアドレス）は個人情報なので、
-- 匿名キーでは **書き込みだけ** できて読み出せないようにする。
-- 送信側はサービスロールキーで読む。
--
-- 以前この画面には LINE / X と書かれたラベルが並んでいたが、
-- 実際には登録先も送信処理も無かった。実体を作るためのテーブル。

create table if not exists public.job_alert_subscriptions (
    id          bigint generated always as identity primary key,
    created_at  timestamptz not null default now(),

    -- 探している条件
    area        text        not null,
    category    text        not null default '障害者雇用',
    conditions  text,

    -- 届け先。channel ごとに address の意味が変わる。
    --   email → メールアドレス
    --   line  → LINEのユーザーID（公式アカウントを友だち追加したときに得られる）
    channel     text        not null,
    address     text        not null,

    -- 二重登録と、いたずら登録を防ぐための確認。
    -- 確認が済むまで送信対象にしない。
    confirmed_at timestamptz,
    confirm_token text      not null default encode(gen_random_bytes(24), 'hex'),

    -- 送信の記録
    last_sent_at timestamptz,
    unsubscribed_at timestamptz,

    constraint job_alert_channel_check check (channel in ('email', 'line')),
    constraint job_alert_area_len   check (char_length(area) between 1 and 60),
    constraint job_alert_address_len check (char_length(address) between 3 and 320),
    constraint job_alert_conditions_len check (conditions is null or char_length(conditions) <= 500)
);

-- 同じ届け先で同じ地域を何度も登録させない。
create unique index if not exists job_alert_unique_idx
    on public.job_alert_subscriptions (channel, address, area)
    where unsubscribed_at is null;

-- 送信対象を引くための索引。
create index if not exists job_alert_sendable_idx
    on public.job_alert_subscriptions (area)
    where confirmed_at is not null and unsubscribed_at is null;

alter table public.job_alert_subscriptions enable row level security;

-- 匿名キーは登録だけ。読み出しは一切できない。
-- 届け先はメールアドレスやLINEのIDなので、他人に見えてはいけない。
drop policy if exists "anon can subscribe" on public.job_alert_subscriptions;
create policy "anon can subscribe"
    on public.job_alert_subscriptions
    for insert
    to anon
    with check (
        confirmed_at is null
        and unsubscribed_at is null
        and last_sent_at is null
    );

-- select / update / delete のポリシーは作らない。
-- RLS が有効で該当ポリシーが無ければ、匿名キーからは何も見えない。
-- 送信と確認はサービスロールキーで行う（RLSを迂回する）。
