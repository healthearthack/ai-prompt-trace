#!/usr/bin/env python3
"""Local manager dashboard for consented Prompt Trace latest CSV exports."""

import argparse
import csv
import json
import pathlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse


PAGE = r'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Prompt Trace Live Authors</title>
<style>
:root{color-scheme:dark;--pink:#ff2da1;--panel:#17121a;--muted:#bcaebe}body{margin:0;background:#0c090d;color:#fff;font:15px system-ui,sans-serif}main{max-width:1180px;margin:auto;padding:32px}h1{margin:0;font-size:30px}.mark{color:var(--pink)}.sub{color:var(--muted);margin:8px 0 24px}.status{display:flex;gap:10px;align-items:center;margin-bottom:16px}.dot{width:10px;height:10px;border-radius:50%;background:#3ee889;box-shadow:0 0 12px #3ee889}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:14px}.card{background:var(--panel);border:1px solid #38273a;border-radius:14px;padding:18px}.id{color:var(--pink);font:700 18px ui-monospace,monospace}.meta{color:var(--muted);font-size:13px;margin-top:7px}.latest{margin-top:14px;line-height:1.45}.empty{padding:28px;border:1px dashed #563954;border-radius:14px;color:var(--muted)}</style>
</head><body><main><h1><span class="mark">Prompt Trace</span> · Live Authors</h1><p class="sub">Authorized audit exports only. Refreshes every 3 seconds.</p><div class="status"><i class="dot"></i><span id="state">Connecting…</span></div><section id="authors" class="grid"></section></main>
<script>
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function refresh(){try{const r=await fetch('/api/authors',{cache:'no-store'}),d=await r.json();document.querySelector('#state').textContent=`${d.authors.length} live author export(s) · ${new Date().toLocaleTimeString()}`;document.querySelector('#authors').innerHTML=d.authors.length?d.authors.map(a=>`<article class="card"><div class="id">[PT:${esc(a.actor)}]</div><div class="meta">${esc(a.records)} records · last seen ${esc(a.lastSeen||'—')}</div><div class="latest"><b>Latest</b><br>${esc(a.latestTitle||'No entries')}<div class="meta">${esc(a.latestSource||'')} ${esc(a.latestTime||'')}</div></div></article>`).join(''):'<div class="empty">No latest exports found yet.</div>';}catch(e){document.querySelector('#state').textContent='Dashboard cannot read exports';}}refresh();setInterval(refresh,3000);
</script></body></html>'''


def author_status(folder: pathlib.Path) -> list[dict]:
    statuses = []
    for path in sorted(folder.glob("prompt-trace-*-latest.csv")):
        with path.open(encoding="utf-8-sig", newline="") as stream:
            rows = list(csv.DictReader(stream))
        actor = rows[-1].get("actor") if rows else path.stem.removeprefix("prompt-trace-").removesuffix("-latest")
        latest = max(rows, key=lambda row: row.get("timestampIso", ""), default={})
        statuses.append({
            "actor": actor,
            "records": len(rows),
            "lastSeen": latest.get("timestampIso"),
            "latestTitle": latest.get("entryTitle"),
            "latestSource": latest.get("source"),
            "latestTime": latest.get("timestampIso"),
        })
    return statuses


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("audit_folder")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    folder = pathlib.Path(args.audit_folder).expanduser().resolve()
    folder.mkdir(parents=True, exist_ok=True)

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            route = urlparse(self.path).path
            if route == "/api/authors":
                body = json.dumps({"authors": author_status(folder)}).encode()
                self.send_response(200); self.send_header("Content-Type", "application/json"); self.send_header("Cache-Control", "no-store"); self.end_headers(); self.wfile.write(body)
            elif route == "/":
                body = PAGE.encode(); self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.end_headers(); self.wfile.write(body)
            else:
                self.send_error(404)
        def log_message(self, format, *args):
            return

    server = ThreadingHTTPServer((args.host, args.port), Handler)
    print(f"Prompt Trace manager dashboard: http://{args.host}:{args.port}")
    print(f"Reading latest exports from: {folder}")
    server.serve_forever()


if __name__ == "__main__":
    main()
