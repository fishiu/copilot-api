"""Resume the original isolated audit, remotely compact, then wake original workers."""
import pathlib,json,subprocess,os,queue,threading,time
base=pathlib.Path(os.environ.get('CAPI_LAB_BASE',str(pathlib.Path.home()/'.local/share/capi-v2-plaintext-test')));home=pathlib.Path(os.environ.get('CODEX_LAB_HOME',str(pathlib.Path.home()/'.codex-v2-test')));state=json.loads((base/'acceptance.json').read_text());sid=state['initial']['threads'][0];q=queue.Queue();events=[];seq=0;receipt={};err=(base/'compact.stderr').open('w');p=subprocess.Popen([os.environ.get('CODEX_LAB_EXECUTABLE','codex'),'app-server','--stdio'],cwd=base/'work',env={**os.environ,'CODEX_HOME':str(home)},stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=err,text=True)
def reader():
 for l in p.stdout:
  try:q.put(json.loads(l))
  except:pass
threading.Thread(target=reader,daemon=True).start()
def rpc(method,params):
 global seq
 seq+=1;p.stdin.write(json.dumps({'id':seq,'method':method,'params':params})+'\n');p.stdin.flush();end=time.monotonic()+40
 while time.monotonic()<end:
  d=q.get(timeout=max(.1,end-time.monotonic()))
  if d.get('id')==seq:
   if 'error'in d:raise RuntimeError(d['error'])
   return d.get('result')
  events.append(d)
def done(timeout):
 end=time.monotonic()+timeout
 while time.monotonic()<end:
  d=q.get(timeout=max(.1,end-time.monotonic()));events.append(d)
  if d.get('method')=='turn/completed'and d.get('params',{}).get('threadId')==sid:return d['params']['turn']
 raise TimeoutError('turn')
try:
 rpc('initialize',{'clientInfo':{'name':'plaintext-v2-lab','version':'1.0'},'capabilities':{'experimentalApi':True}})
 rpc('thread/resume',{'threadId':sid,'modelProvider':'plaintext_lab','cwd':str(base/'work'),'approvalPolicy':'never','sandbox':'read-only','excludeTurns':True})
 rpc('thread/compact/start',{'threadId':sid});d=done(100);receipt['compact']={k:d.get(k)for k in ['status','error']};print(json.dumps(receipt),flush=True)
 if d.get('status')=='completed':
  before=len(events);rpc('turn/start',{'threadId':sid,'input':[{'type':'text','text':'After gateway restart and remote compaction, use collaboration.followup_task on both ORIGINAL children audit_a and audit_b. No spawning and no shell/file tools. Ask each to recall from its own existing context its original marker and the three successfully computed audit values, send POST_COMPACT progress to /root and give final JSON with task, marker, count, sum_cents, flagged_paid. Do not supply their markers or values. Wait for both, return JSON mapping task names to results. If a worker cannot recall, report that rather than guessing.','text_elements':[]}]});d=done(150);receipt['followup']={k:d.get(k)for k in ['status','error']};receipt['texts']=[e['params']['item'].get('text','')for e in events[before:]if e.get('method')=='item/completed'and e.get('params',{}).get('threadId')==sid and e.get('params',{}).get('item',{}).get('type')=='agentMessage']
except Exception as e:receipt['exception']=repr(e)
finally:
 p.terminate()
 try:p.wait(timeout=6)
 except:p.kill();p.wait()
 err.close();(base/'compact-events.json').write_text(json.dumps(events));(base/'compact-result.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt),flush=True)
