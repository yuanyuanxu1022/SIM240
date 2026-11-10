"""Extract only D2/D3 build-related historical tool calls; never execute them."""
import hashlib
import json
import re
from pathlib import Path

OUT=Path(__file__).resolve().parent
sessions=[]
hits=[]
case=re.compile(r'd2_groove_error_map|d3_oblique_groove_tensor_check',re.I)
build=re.compile(r'\bmake\b|\bmpic\+\+|\bg\+\+|sha256sum|CXXFLAGS|\.cpp',re.I)
for day in ['14','15','16','17','18','19']:
    for p in sorted(Path('/home/dell/.codex/sessions/2026/10',day).glob('*.jsonl')):
        ids={}
        count=0
        for line_no,line in enumerate(p.open(),1):
            try: obj=json.loads(line)
            except json.JSONDecodeError: continue
            payload=obj.get('payload',{})
            typ=payload.get('type','')
            cid=payload.get('call_id')
            if typ in ['function_call','custom_tool_call']:
                content=payload.get('arguments',payload.get('input',''))
                if isinstance(content,dict): content=json.dumps(content,ensure_ascii=False)
                if not case.search(content) or not build.search(content): continue
                # Exclude calls solely reading reports/manuscripts, not build/source artefacts.
                if not any(s in content for s in ['src/','build/','Makefile','sha256sum','make -','make"','make\'']): continue
                ids[cid]=len(hits)
                hits.append({'session':str(p),'line':line_no,'timestamp':obj.get('timestamp'),
                    'call_id':cid,'tool':payload.get('name'),'recorded_tool_input':content,
                    'classification':'historical tool input; not executed by this audit'})
                count+=1
            elif typ in ['function_call_output','custom_tool_call_output'] and cid in ids:
                hits[ids[cid]]['output_line']=line_no
                hits[ids[cid]]['recorded_tool_output']=payload.get('output')
        if count:
            sessions.append({'path':str(p),'targeted_tool_calls':count,
                 'bytes_observed':p.stat().st_size,
                 'sha256_observed':hashlib.sha256(p.read_bytes()).hexdigest()})
(OUT/'evidence/historical_tool_excerpts.json').write_text(json.dumps(hits,ensure_ascii=False,indent=2)+'\n')
(OUT/'evidence/history_search_scope.json').write_text(json.dumps({'date_directories':['2026-10-'+d for d in ['14','15','16','17','18','19']],
    'sessions_with_targeted_calls':sessions,'targeted_call_count':len(hits),
    'limits':'Only D2/D3 tool call inputs and directly paired outputs; no narrative treated as proof. Session files may be append-only/live; hashes are observed snapshots.'},ensure_ascii=False,indent=2)+'\n')
for h in hits:
    s=h['recorded_tool_input']
    # Only print the local relevant snippets, not unrelated conversation material.
    candidate_lines=[x for x in s.splitlines() if case.search(x) or re.search(r'\bmpic\+\+|\bg\+\+|\bmake\s+-',x)]
    print(Path(h['session']).name,h['line'],h['timestamp'],str(candidate_lines)[:650])
print('targeted calls',len(hits),'sessions',len(sessions))
