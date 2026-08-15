set search_path = prompt_trace, public;
insert into author_identities(author_id, public_display_name, status)
values ('AC', 'Andrew Kieckhefer', 'reserved')
on conflict (author_id) do nothing;

-- All one- and two-character IDs are internal/reserved. This covers nation,
-- state, and territory abbreviations plus ambiguous system terms such as AI,
-- IT, UI, UX, QA, RX, and HD. AC is grandfathered as the founding identity.
insert into reserved_author_ids(author_id, reservation_class, reason)
select id, 'short-code', 'Reserved short identifier; requires approved internal allocation'
from (
  select chr(a) || chr(b) as id
  from generate_series(ascii('A'), ascii('Z')) a
  cross join generate_series(ascii('A'), ascii('Z')) b
  union all
  select chr(a) from generate_series(ascii('A'), ascii('Z')) a
) codes
on conflict (author_id) do nothing;
