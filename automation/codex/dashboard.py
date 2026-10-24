#!/usr/bin/env python3
"""Read GitHub runs and sanitized artifacts; never infer publication from Success."""
import argparse
import base64
import tempfile
from cloud_ops import verify_live
import collections
import datetime as dt
import io
import json
import os
from pathlib import Path
import subprocess
import zipfile


def api(path, binary=False):
    data=subprocess.check_output(['gh','api',path], stderr=subprocess.PIPE)
    return data if binary else json.loads(data)



def reconcile_deployment(repo, kind, data):
    """Recheck a committed candidate after asynchronous Pages propagation."""
    if data.get('status') != 'FAILED_DEPLOY' or not data.get('commit') or not data.get('id'):
        return False
    with tempfile.TemporaryDirectory() as directory:
        root=Path(directory)
        def copy(path):
            blob=api(f"repos/{repo}/contents/{path}?ref={data['commit']}")
            local=root/path
            local.parent.mkdir(parents=True,exist_ok=True)
            local.write_bytes(base64.b64decode(blob['content']))
        if kind=='news':
            copy('public/data/ai-news.json')
            article=next(x for x in json.loads((root/'public/data/ai-news.json').read_text()) if x['id']==data['id'])
            copy('public'+article['image'])
        else:
            copy('lessons/'+data['id']+'.json')
        data['url']=verify_live(kind,root,data['id'])
        data['status']='PUBLISHED'
        data['reconciled_after_deployment_delay']=True
        return True


def build(repo, kind, recover=False):
    now=dt.datetime.now(dt.timezone.utc)
    workflow=f'codex-cloud-hourly-{kind}.yml'
    runs=api(f'repos/{repo}/actions/workflows/{workflow}/runs?per_page=100')['workflow_runs']
    recent=[r for r in runs if dt.datetime.fromisoformat(r['created_at'].replace('Z','+00:00')) >= now-dt.timedelta(hours=24)]
    artifacts=api(f'repos/{repo}/actions/artifacts?per_page=100')['artifacts']
    by_run={}
    for a in sorted(artifacts, key=lambda x:x['created_at'], reverse=True):
        if a['name'].startswith(kind+'-publishing-result-') and not a['expired'] and a.get('workflow_run'):
            by_run.setdefault(a['workflow_run']['id'], a)
    rows=[]
    for r in recent:
        status='UNRECORDED'
        detail='Legacy run or no sanitized result; publication unknown'
        if r['id'] in by_run:
            try:
                blob=api(f"repos/{repo}/actions/artifacts/{by_run[r['id']]['id']}/zip",True)
                with zipfile.ZipFile(io.BytesIO(blob)) as z:
                    data=json.loads(z.read('result.json'))
                try:
                    reconcile_deployment(repo, kind, data)
                except Exception:
                    pass  # Keep original failure until live bytes are verifiable.
                status=data['status'];detail=data.get('url',data.get('reason',''))
            except Exception:
                detail='Result artifact could not be read; inspect run'
        rows.append({'time':r['created_at'],'actions':r['conclusion'] or r['status'],'status':status,'detail':detail,'url':r['html_url']})
    counts=collections.Counter(r['status'] for r in rows)
    # GitHub supplies actual creation times, not the original cron slot. Report observed gaps honestly.
    times=sorted(dt.datetime.fromisoformat(r['created_at'].replace('Z','+00:00')) for r in recent if r['event']=='schedule')
    gaps=[]
    for a,b in zip(times,times[1:]+[now]):
        if b-a > dt.timedelta(minutes=90):
            gaps.append({'from':a.isoformat(),'to':b.isoformat(),'minutes':round((b-a).total_seconds()/60)})
    recovery='not requested'
    if recover and runs:
        last=dt.datetime.fromisoformat(runs[0]['created_at'].replace('Z','+00:00'))
        active=any(r['status'] != 'completed' for r in runs)
        if not active and now-last > dt.timedelta(minutes=90):
            subprocess.run(['gh','workflow','run',workflow,'--repo',repo,'--ref','main'],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            recovery='workflow_dispatch requested after >90 minute gap; completion not yet confirmed'
        else:
            recovery='no recovery needed or another run is active'
    result={'recovery':recovery,'checked_at' :now.isoformat(),'repo':repo,'runs_24h':len(rows),'statuses':dict(counts),'observed_schedule_gaps_over_90_minutes':gaps,'runs':rows}
    Path('ops-dashboard').mkdir(exist_ok=True)
    Path('ops-dashboard/dashboard.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    text=f'# {kind} 운영 대시보드\n\n최근 24시간 실행 {len(rows)}회 · 실제 게시 확인 {counts["PUBLISHED"]}회 · 발행 상태 미기록 {counts["UNRECORDED"]}회\n\n'
    text+=recovery+'\n\n'
    text+='과거 결과 미기록은 발행 0건을 의미하지 않습니다. 새 결과 파일 도입 이후부터 정확히 집계합니다.\n\n'
    text+=f'90분 초과 예약 실행 간격 {len(gaps)}건. 원래 예약 슬롯은 API에 없어 누락/지연을 확정 구분할 수 없습니다.\n\n'
    text+='| 실제 실행 UTC | Actions | 발행 상태 | 기록 |\n|---|---|---|---|\n'
    for r in rows:
        text+=f'| {r["time"]} | {r["actions"]} | {r["status"]} | [실행]({r["url"]}) |\n'
    Path('ops-dashboard/dashboard.md').write_text(text,encoding='utf-8')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as f:f.write(text)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',required=True);p.add_argument('--kind',choices=['news','lesson'],required=True)
    p.add_argument('--recover',action='store_true');a=p.parse_args();build(a.repo,a.kind,a.recover)
