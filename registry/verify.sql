set search_path = prompt_trace, public;
select author_id, public_display_name, status, claimed_order from author_identities where author_id = 'AC';
select table_name from information_schema.tables where table_schema = 'prompt_trace' order by table_name;
select tablename, rowsecurity from pg_tables where schemaname = 'prompt_trace' order by tablename;
