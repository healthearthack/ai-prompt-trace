#!/usr/bin/env python3
"""Provision the first Prompt Trace account without storing a plaintext password."""
import argparse
import getpass
import os

import psycopg
from argon2 import PasswordHasher

parser = argparse.ArgumentParser()
parser.add_argument("--email", required=True)
parser.add_argument("--username", required=True)
parser.add_argument("--display-name", required=True)
parser.add_argument("--author-id", required=True)
args = parser.parse_args()
author_id = args.author_id.strip().upper()
password = getpass.getpass("New Prompt Trace password: ")
confirm = getpass.getpass("Confirm password: ")
if password != confirm or len(password) < 12:
    raise SystemExit("Passwords must match and contain at least 12 characters")
database_url = os.environ.get("PROMPT_TRACE_DATABASE_URL")
if not database_url:
    raise SystemExit("PROMPT_TRACE_DATABASE_URL is required")
password_hash = PasswordHasher().hash(password)

with psycopg.connect(database_url) as db, db.cursor() as cursor:
    cursor.execute("set search_path=prompt_trace,public")
    cursor.execute("""insert into accounts(primary_email,username,display_name,password_hash,status,email_verified_at)
                      values(%s,%s,%s,%s,'active',now()) returning account_id""",
                   (args.email, args.username.lower(), args.display_name, password_hash))
    account_id = cursor.fetchone()[0]
    cursor.execute("select 1 from reserved_author_ids where author_id=%s", (author_id,))
    if cursor.fetchone():
        cursor.execute("""insert into reserved_author_id_requests(author_id,account_id,purpose,status,decided_at,decided_by)
                          values(%s,%s,'Verified founding or internal allocation','approved',now(),%s)""",
                       (author_id, account_id, account_id))
    cursor.execute("""insert into author_identities(author_id,account_id,public_display_name,status,activated_at)
                      values(%s,%s,%s,'active',now())
                      on conflict(author_id) do update set account_id=excluded.account_id,public_display_name=excluded.public_display_name,status='active',activated_at=now()""",
                   (author_id, account_id, args.display_name))
    cursor.execute("""insert into workspaces(kind,owner_account_id,name,portability,retain_raw_content)
                      values('personal',%s,'Personal','full_content',true)""", (account_id,))
    cursor.execute("insert into cyber_cv_profiles(account_id,visibility) values(%s,'private')", (account_id,))
print(f"Provisioned {args.display_name} as [PT:{author_id}] account {account_id}")
