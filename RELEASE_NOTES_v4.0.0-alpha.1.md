# Prompt Trace v4.0.0 alpha 1 — portable identity data layer

- Adds one permanent person account and author ID across devices.
- Adds passkey, password-hash, session, and device-credential storage.
- Adds personal and organization workspaces under one continuity timeline.
- Adds employment memberships without transferring identity ownership to employers.
- Adds explicit consent records and workspace portability policies.
- Stores provenance metadata centrally while keeping raw text local by default.
- Supports optional encrypted content without a plaintext database column.
- Adds PostgreSQL row-level isolation for account-owned records.
- Includes a local Docker Compose development database and verification queries.
- Reserves all one- and two-character IDs for approved internal allocation; `AC` remains the grandfathered founder identity.
- Adds `[PT:USER · ORG]` organization-context attribution.
- Adds the standardized four-format Terminal Prompt Trace Curriculum Vitae exporter.
- Adds opt-in Cyber CV profiles, entry selection, ordering, annotations, and visibility controls.

This alpha is the database layer. It does not yet include the production login, recovery, synchronization, or organization-administration service.
