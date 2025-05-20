-- Create the breach_raw table
create table breach_raw (
  hash text primary key,
  entity text,
  notice_date date,
  records int,
  notice_url text,
  _portal text,
  inserted_at timestamptz default now(),
  raw jsonb
);

-- Create the notification function for large breaches
create or replace function notify_big()
returns trigger as $$
declare
  payload json;
begin
  if NEW.records >= 2500 then
     payload := json_build_object(
       'text', format('🚨 %s – %s records', NEW.entity, NEW.records));
     perform
       net.http_post(
         url:='${SLACK_WEBHOOK}',
         body:=payload,
         headers:='{"Content-Type":"application/json"}'::json);
  end if;
  return NEW;
end;
$$ language plpgsql security definer;

-- Create the trigger for notifications
create trigger t_big after insert on breach_raw
for each row execute procedure notify_big();
