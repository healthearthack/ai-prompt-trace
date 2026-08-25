import csv, datetime as dt, json, os, pathlib, platform, shutil, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
CLI = ROOT / 'prompt_trace.py'
RESULTS = pathlib.Path(__file__).resolve().parent / 'results'
RESULTS.mkdir(parents=True, exist_ok=True)
CATEGORIES={'recording_integrity':25,'duplicate_tag_prevention':15,'credential_redaction':15,'signature_verification':20,'csv_export_integrity':15,'tamper_detection':10}

def call(home,*args,input_text=None):
    env={**os.environ,'PROMPT_TRACE_HOME':str(home)}
    return subprocess.run([sys.executable,str(CLI),*args],env=env,input=input_text,text=True,capture_output=True)

def init(home): return call(home,'init','--actor','AC','--consent')
def events(home):
    p=pathlib.Path(home)/'prompt-ledger.jsonl'
    if not p.exists(): return []
    return [json.loads(x) for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
def R(cat,cid,ok,detail): return {'category':cat,'case_id':cid,'passed':bool(ok),'detail':detail}

def recording():
    out=[]; sources=['ai-composer','browser:chatgpt.com','browser:claude.ai','browser:gemini.google.com','browser:copilot.microsoft.com','powershell','bash','zsh','terminal','mcp']
    for i in range(25):
        with tempfile.TemporaryDirectory() as f:
            h=pathlib.Path(f)/'d'; ir=init(h); text=f'Benchmark recording scenario {i+1:02d}'; src=sources[i%len(sources)]
            rr=call(h,'record','--text',text,'--source',src) if ir.returncode==0 else ir; es=events(h)
            ok=ir.returncode==0 and rr.returncode==0 and len(es)==1 and es[0].get('actor')=='AC' and es[0].get('entryText')==text and es[0].get('entryTitle')==f'[PT:AC] {text}' and bool(es[0].get('signature'))
            out.append(R('recording_integrity',f'REC-{i+1:02d}',ok,'signed record preserved' if ok else (rr.stderr.strip() or 'record mismatch')))
    return out

def duplicate():
    out=[]
    for i in range(15):
        with tempfile.TemporaryDirectory() as f:
            h=pathlib.Path(f)/'d'; ir=init(h); text=f'[PT:AC] Existing attributed prompt {i+1:02d}'
            rr=call(h,'record','--text',text,'--source','browser:chatgpt.com') if ir.returncode==0 else ir; es=events(h); title=es[0].get('entryTitle','') if es else ''
            ok=ir.returncode==0 and rr.returncode==0 and title==text and '[PT:AC] [PT:AC]' not in title
            out.append(R('duplicate_tag_prevention',f'DUP-{i+1:02d}',ok,'duplicate prevented' if ok else (rr.stderr.strip() or title)))
    return out

def redact():
    vals=[('--password hunter2','hunter2'),('--password=hunter3','hunter3'),('--api-key sk-abcdefghijklmnop','sk-abcdefghijklmnop'),('--api-key=sk-qrstuvwxyzabcdef','sk-qrstuvwxyzabcdef'),('Authorization: Bearer secret-token','secret-token'),('--token token-value-12345','token-value-12345'),('--token=token-value-67890','token-value-67890'),('--pin 4815','4815'),('password: summer2026','summer2026'),('api_key: abcdefghijklmnop','abcdefghijklmnop'),('Bearer eyJhbGciOiJIUzI1NiJ9.payload.signature','eyJhbGciOiJIUzI1NiJ9.payload.signature'),('authorization=Basic dXNlcjpwYXNz','dXNlcjpwYXNz'),('--password alpha --token beta-token','alpha'),('--api-key sk-1234567890abcdef --pin 9922','sk-1234567890abcdef'),('Authorization: Bearer final-secret --password omega','final-secret')]
    out=[]
    for i,(text,forbidden) in enumerate(vals,1):
        with tempfile.TemporaryDirectory() as f:
            h=pathlib.Path(f)/'d'; ir=init(h); rr=call(h,'record','--source','powershell',input_text=text) if ir.returncode==0 else ir
            p=h/'prompt-ledger.jsonl'; body=p.read_text(encoding='utf-8') if p.exists() else ''; es=events(h); e=es[0] if es else {}
            ok=ir.returncode==0 and rr.returncode==0 and forbidden not in body and e.get('redactionApplied') is True and int(e.get('redactionCount',0))>=1
            out.append(R('credential_redaction',f'RED-{i:02d}',ok,'secret redacted before storage' if ok else (rr.stderr.strip() or 'redaction mismatch')))
    return out

def verify():
    out=[]
    for i in range(20):
        with tempfile.TemporaryDirectory() as f:
            h=pathlib.Path(f)/'d'; ir=init(h); good=ir.returncode==0
            if good:
                for j in range(1+(i%4)): good = good and call(h,'record','--text',f'Verification {i+1:02d}-{j+1}','--source','test').returncode==0
            vr=call(h,'verify') if good else ir; ok=good and vr.returncode==0
            out.append(R('signature_verification',f'VER-{i+1:02d}',ok,'ledger verified' if ok else vr.stderr.strip()))
    return out

def export_csv():
    out=[]
    for i in range(15):
        with tempfile.TemporaryDirectory() as f:
            root=pathlib.Path(f); h=root/'d'; ir=init(h); text=f'CSV export scenario {i+1:02d}'
            rr=call(h,'record','--text',text,'--source','test') if ir.returncode==0 else ir; p=root/'activity.csv'; er=call(h,'export-csv',str(p)) if rr.returncode==0 else rr
            rows=[]
            if p.exists():
                with p.open(encoding='utf-8-sig',newline='') as s: rows=list(csv.DictReader(s))
            ok=ir.returncode==0 and rr.returncode==0 and er.returncode==0 and len(rows)==1 and rows[0].get('actor')=='AC' and rows[0].get('entryText')==text and rows[0].get('entryTitle')==f'[PT:AC] {text}'
            out.append(R('csv_export_integrity',f'CSV-{i+1:02d}',ok,'CSV preserved actor/text/title' if ok else (er.stderr.strip() or 'CSV mismatch')))
    return out

def tamper():
    out=[]; fields=['entryText','entryTitle','actor','source','recordId','timestamp','organization','codeSignatureId','signature','redactionCount']
    for i,field in enumerate(fields,1):
        with tempfile.TemporaryDirectory() as f:
            h=pathlib.Path(f)/'d'; ir=init(h); rr=call(h,'record','--text',f'Tamper case {i:02d}','--source','test') if ir.returncode==0 else ir; es=events(h); p=h/'prompt-ledger.jsonl'
            if rr.returncode!=0 or not es: out.append(R('tamper_detection',f'TAMP-{i:02d}',False,rr.stderr.strip() or 'no event')); continue
            e=es[0]; e[field]=999 if field=='redactionCount' else ('AAAA' if field=='signature' else f'TAMPERED-{field}'); p.write_text(json.dumps(e)+'\n',encoding='utf-8'); vr=call(h,'verify'); ok=vr.returncode!=0
            out.append(R('tamper_detection',f'TAMP-{i:02d}',ok,f'{field} tamper detected' if ok else 'tamper accepted'))
    return out

def git_sha():
    try:return subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
    except Exception:return None

def main():
    if not CLI.exists(): raise SystemExit(f'PromptHub CLI not found: {CLI}')
    if not shutil.which('ssh-keygen'): raise SystemExit('OpenSSH ssh-keygen is required.')
    results=[]
    for fn in [recording,duplicate,redact,verify,export_csv,tamper]:
        cur=fn(); results+=cur; print(f"{cur[0]['category']}: {sum(x['passed'] for x in cur)}/{len(cur)}")
    assert len(results)==100
    summary={}
    for cat,total in CATEGORIES.items():
        items=[x for x in results if x['category']==cat]; passed=sum(x['passed'] for x in items); summary[cat]={'planned':total,'executed':len(items),'passed':passed,'score_percent':round(100*passed/len(items),2)}
    passed=sum(x['passed'] for x in results); score=round(float(passed),2)
    report={'benchmark':'PromptHub Provenance Benchmark','benchmark_version':'1.0','status':'EXECUTED','executed_at_utc':dt.datetime.now(dt.timezone.utc).isoformat(),'prompthub_commit_sha':git_sha(),'environment':{'os':platform.platform(),'python_version':platform.python_version()},'total_scenarios':100,'overall_passed':passed,'overall_failed':100-passed,'overall_score_percent':score,'categories':summary,'scenarios':results}
    jp=RESULTS/'prompthub-v1.0.json'; jp.write_text(json.dumps(report,indent=2),encoding='utf-8')
    labels={'recording_integrity':'Recording integrity','duplicate_tag_prevention':'Duplicate-tag prevention','credential_redaction':'Credential redaction','signature_verification':'Signature verification','csv_export_integrity':'CSV export integrity','tamper_detection':'Tamper detection'}
    lines=['# PromptHub Provenance Benchmark v1.0','',f'**Measured result: {passed}/100 scenarios passed ({score:.1f}%).**','',f"- Executed (UTC): `{report['executed_at_utc']}`",f"- PromptHub commit SHA: `{report['prompthub_commit_sha']}`",f"- Operating system: `{report['environment']['os']}`",f"- Python: `{report['environment']['python_version']}`",'','## Category results','','| Category | Passed | Total | Score |','|---|---:|---:|---:|']
    for k in CATEGORIES:
        s=summary[k]; lines.append(f"| {labels[k]} | {s['passed']} | {s['executed']} | {s['score_percent']:.1f}% |")
    lines += ['','## Scope','','Overall score = passed controlled scenarios / 100.','','This benchmark measures the tested PromptHub CLI provenance behaviors above. It does not represent browser compatibility, legal compliance, security certification, or production-load performance.','','## Scenario results','']
    for x in results: lines.append(f"- **{'PASS' if x['passed'] else 'FAIL'}** `{x['case_id']}` — {x['detail']}")
    (RESULTS/'prompthub-v1.0.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    print(f'\nOVERALL: {passed}/100 = {score:.1f}%')
    print(f'JSON: {jp}')
    print(f'Markdown: {RESULTS / "prompthub-v1.0.md"}')
    return 0 if passed==100 else 1
if __name__=='__main__': raise SystemExit(main())
