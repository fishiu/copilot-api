"""Synthetic native-Codex acceptance against the private CAPI instance."""
import csv, json, os, pathlib, random, subprocess, time, uuid, sys
BASE=pathlib.Path.home()/'.local/share/capi-v2-plaintext-test'
HOME=pathlib.Path.home()/'.codex-v2-test'
WORK=BASE/'work'
HOME.mkdir(mode=0o700,exist_ok=True);WORK.mkdir(mode=0o700,exist_ok=True)
if (BASE/'acceptance.json').exists():raise SystemExit('Existing results: inspect before repeating')
catalog=json.loads((pathlib.Path.home()/'.codex/copilot-models.json').read_text())
for m in catalog['models']:m['multi_agent_version']='v2'
(HOME/'catalog.json').write_text(json.dumps(catalog))
(HOME/'config.toml').write_text(f'''model="gpt-6.1-sol"
model_provider="plaintext_lab"
model_reasoning_effort="medium"
model_catalog_json="{HOME/'catalog.json'}"
approval_policy="never"
sandbox_mode="read-only"
web_search="disabled"
[features]
multi_agent=true
defer_mailbox_preemption=true
output_token_replay=false
memories=false
[features.multi_agent_v2]
enabled=true
expose_spawn_agent_model_overrides=true
max_concurrent_threads_per_session=4
[model_providers.plaintext_lab]
name="OpenAI"
base_url="http://127.0.0.1:60444"
wire_api="responses"
supports_websockets=false
request_max_retries=0
stream_max_retries=0
stream_idle_timeout_ms=90000
capabilities={{ remote_compaction="v2" }}
[model_providers.plaintext_lab.auth]
command="/bin/bash"
args=["/Users/leverest/repos/dotconfig/shared/capi/get-gateway-key.sh","{BASE/'data'}"]
timeout_ms=5000
refresh_interval_ms=300000
''')
rng=random.Random(938123);expect={};secret={}
for task in ['audit_a','audit_b']:
 marker='TASK_'+uuid.uuid4().hex;secret[task]=marker;rows=[]
 for i in range(1200):rows.append({'id':i,'status':rng.choice(['paid','pending','cancelled']),'cents':rng.randint(100,99999),'flag':rng.choice([0,0,0,1])})
 with (WORK/(task+'.csv')).open('w')as f:
  w=csv.DictWriter(f,fieldnames=['id','status','cents','flag']);w.writeheader();w.writerows(rows)
 valid=[r for r in rows if r['status']=='paid' and not r['flag']];expect[task]={'count':len(valid),'sum_cents':sum(r['cents']for r in valid),'flagged_paid':sum(r['status']=='paid' and bool(r['flag'])for r in rows)}
state={'expected':expect,'markers':secret,'home':str(HOME),'work':str(WORK)}
def invoke(label,prompt,sid=None):
 cmd=['/Users/leverest/.local/bin/codex','exec']
 if sid:cmd+=['resume']
 cmd+=['--json','--skip-git-repo-check']
 if sid:cmd+=[sid]
 cmd+=[prompt]
 out=BASE/(label+'.jsonl');err=BASE/(label+'.stderr');t=time.monotonic()
 with out.open('w')as so,err.open('w')as se:
  p=subprocess.Popen(cmd,cwd=WORK,env={**os.environ,'CODEX_HOME':str(HOME)},stdout=so,stderr=se,stdin=subprocess.DEVNULL)
  try:rc=p.wait(timeout=330)
  except subprocess.TimeoutExpired:p.terminate();p.wait(timeout=10);rc='timeout'
 ds=[]
 for l in out.read_text().splitlines():
  try:ds.append(json.loads(l))
  except:pass
 receipt={'exit':rc,'seconds':round(time.monotonic()-t,2),'threads':[d['thread_id']for d in ds if d.get('type')=='thread.started'],'errors':[d for d in ds if d.get('type')in ['error','turn.failed']],'assistant_texts':[d['item'].get('text','')for d in ds if d.get('type')=='item.completed'and d.get('item',{}).get('type')=='agent_message']}
 print(json.dumps({label:receipt}),flush=True);return receipt
prompts=[]
for task,model in [('audit_a','gpt-6-astra'),('audit_b','gpt-6.1-sol')]:
 child=f'''Synthetic CSV audit. Remember your task marker {secret[task]} in your own context. First send collaboration.send_message to /root: START_{task}. Read {WORK/(task+'.csv')} using python3 -c inline code only, with no heredocs or output redirection. Compute exactly the number and sum of cents of rows status=paid AND flag=0; also count rows status=paid AND flag=1. Send an explicit RESULT_{task} progress message containing your marker and all three computed numbers. Then give final JSON with task, marker, count, sum_cents, flagged_paid. Do not spawn children. Do not modify files or use network/MCP. On error stop and report actual failure.'''
 prompts.append(f'Spawn task_name={task}, model={model}, reasoning_effort=medium, fork_turns=none, with this message: {child}')
prompt='''This is an isolated multi-agent acceptance test using synthetic CSV data. Create exactly TWO children before waiting, one for each task below. Use actual V2 tools, including functions.exec if tools require it. You must not read the CSVs or compute their answers yourself. Children may use shell/Python tools to read only the specified files. After creating both, wait for their explicit progress messages and final results. Do not create replacements or retry on failure. Return a JSON object mapping task names to their returned result objects. No file modifications, network or MCP.\n'''+ '\n'.join(prompts)
state['initial']=invoke('initial',prompt)
(BASE/'acceptance.json').write_text(json.dumps(state,indent=2))
if state['initial']['exit'] != 0 or state['initial']['errors'] or not state['initial']['threads']:raise SystemExit(1)
sid=state['initial']['threads'][0]
state['resume']=invoke('restart-followup', '''You are a new process resuming the prior synthetic audit. Use collaboration.followup_task on BOTH original children audit_a and audit_b; do not spawn any new child. Ask each to recall from its own prior context its task marker and the three audit numbers, send one explicit RECALL message to /root, and return final JSON with task, marker, count, sum_cents, flagged_paid. Do not supply their markers or results in your followup, and no shell/file/network tools are needed. Wait for both original children and output a JSON object mapping tasks to their results. On failure report it and stop.''',sid)
(BASE/'acceptance.json').write_text(json.dumps(state,indent=2))
