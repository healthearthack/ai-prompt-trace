# Prompt Trace v4 identity database

Separate company registries cannot guarantee that an ID is unique worldwide. Prompt Trace therefore distinguishes:

1. the **global identity directory**, which permanently owns an author ID; and
2. an **organization membership**, which states that the identity works with a company.

Northwestern Mutual and New York Life can both enroll people, but the database primary key prevents them from issuing the same global author ID. An identity can change employers without changing historical authorship.

The schema in `schema.sql` is the deployable PostgreSQL data model. Claims must run in a serializable transaction and require verified authentication. The repository bootstrap records `AC` as founding reservation number 1, pending real-world ownership verification by the production directory administrator.

Signing credentials expire exactly 100 calendar years after issuance. Expiration permits key renewal for the existing identity; it never releases the author ID for reuse. Retired IDs remain tombstoned forever.

The current local application does not contact this service. Until a production directory and verified claim flow are deployed, its JSON registry guarantees uniqueness only inside that registry. The UI and documentation must not claim global enforcement before that service is live.

All one- and two-character author IDs are reserved. This blocks geographic abbreviations and ambiguous internal terms by default. `AC` is the grandfathered founding identity. Any other short code requires an approved record in `reserved_author_id_requests`; ordinary signup never allocates it.

## Identity across devices

The `accounts` row is the person. The `author_identities` row assigns that person one permanent public ID. Every row in `devices` references the same `account_id` while carrying its own public signing key.

Logging in on a second computer therefore does not create another identity and does not copy the first computer's private key. It creates a new device credential under the existing account:

```text
Andrew's account → AC → portable computer key
                    └→ workstation key
                    └→ future worker-node key
```

Revoking one device does not revoke `AC` or the other devices.

## Continuous personal/work timeline

Every `ledger_records` row carries the same account and author ID plus a workspace. The `account_continuity` view returns one chronological history spanning personal and employer contexts.

Workspace portability controls what follows the person:

- `full_content` — signed receipt and encrypted prompt/command content.
- `signed_receipt` — author, time, source, organization, hashes, and signature; raw text remains governed by the organization.
- `organization_only` — the account retains only the minimum cryptographic continuity permitted by policy.

## Start the development database

Requirements: Docker Desktop with Docker Compose.

```powershell
cd registry
Copy-Item .env.example .env
```

Replace the example password in `.env`, then run:

```powershell
docker compose up -d
docker compose exec postgres psql -U prompt_trace_admin -d prompt_trace -f /verify.sql
```

The first two scripts are applied automatically only when the database volume is first created. Do not rerun `schema.sql` against an initialized database; future changes must use numbered migrations.

Provision the founding account from a trusted administrator terminal:

```powershell
$env:PROMPT_TRACE_DATABASE_URL = "postgresql://prompt_trace_admin:YOUR_PASSWORD@127.0.0.1:5432/prompt_trace"
python .\provision_account.py --email "YOUR_EMAIL" --username "andrew" --display-name "Andrew Kieckhefer" --author-id AC
```

The password is requested without echo and stored only as an Argon2id hash.

## Authentication boundary

The database stores only an Argon2id password hash, never a password. Passkeys store a credential identifier and public key. Sessions store a token hash rather than the usable token. The application service—not browser code—must verify authentication, set the transaction-local `app.account_id`, and perform privileged writes.

This repository now contains the data layer, not a production authentication service. Email verification, passkey ceremonies, password recovery, rate limits, and organization invitations are the next service-layer implementation.
