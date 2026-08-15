# Managed author IDs

An administrator can issue a unique 1–8-character alphanumeric ID before a device is enrolled:

```powershell
.\enterprise\issue-author.ps1 -AuthorId EMP0042 -DisplayName "Employee Forty Two" -Registry "\\server\PromptTrace\actors.json"
```

Give the employee the author ID and one-time enrollment token through an approved secure channel. The setup wizard activates that ID against the device public key and destroys the reusable token hash. The private signing key stays on the employee device.

Back up and access-control the shared registry. It is the authority for uniqueness inside that organization; Prompt Trace does not claim global uniqueness across unrelated registries.

## Manager audit exports

The raw ledger and private key remain on each employee device. With informed employee consent and an approved retention/access policy, publish a sanitized CSV to a restricted company folder:

```powershell
.\enterprise\publish-audit.ps1 -DestinationFolder "\\server\PromptTrace\audits"
```

Without `-Archive`, the command refreshes one on-demand file such as `prompt-trace-EMP0042-latest.csv`. Add `-Archive` to retain a timestamped snapshot.

For an opt-in live feed, each employee or managed device runs:

```powershell
.\enterprise\start-live-sync.ps1 -DestinationFolder "\\server\PromptTrace\audits" -IntervalSeconds 15
```

On the manager computer, start the live-author dashboard:

```powershell
python .\enterprise\live-dashboard.py "\\server\PromptTrace\audits"
```

Then open `http://127.0.0.1:8765`. It refreshes every three seconds and shows all reporting author IDs, last-seen times, counts, and latest signed activity. It binds only to the manager's own computer by default. Do not expose it to a network without company authentication, TLS, and authorization.

To create a deduplicated organization CSV:

```powershell
python .\enterprise\merge-audits.py "\\server\PromptTrace\audits" "\\server\PromptTrace\reports\all-employees.csv"
```

The export can contain employee-submitted prompts and commands. Restrict it to authorized managers, define retention, document the business purpose, and follow employment/privacy law. Do not collect private device keys.
