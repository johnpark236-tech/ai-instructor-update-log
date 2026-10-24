#!/usr/bin/env python3
"""Trusted post-generation operations. Never upload CLI transcripts or credentials."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import urllib.request
import zipfile
import io

LOG = Path.home() / '.mannal-codex-hourly' / 'runs.jsonl'


def gh(*args):
    return subprocess.check_output(['gh', *args], text=True, stderr=subprocess.PIPE).strip()


def read_result():
    if LOG.exists():
        return json.loads(LOG.read_text(encoding='utf-8').splitlines()[-1])
    return {'status': 'UNKNOWN_ERROR', 'reason': 'No publisher result; inspect setup/authentication steps'}


def save_result(result):
    LOG.parent.mkdir(parents=True, exist_ok=True)
    with LOG.open('a', encoding='utf-8') as f:
        f.write(json.dumps(result, ensure_ascii=False) + '\n')


def fetch(path):
    request = urllib.request.Request(path, headers={'Cache-Control': 'no-cache', 'User-Agent': 'mannal-deployment-verifier'})
    with urllib.request.urlopen(request, timeout=25) as response:
        return response.read()


def verify_live(kind, repo, content_id):
    base = 'https://mannalkorean.com/' if kind == 'news' else 'https://johnpark236-tech.github.io/ai-instructor-update-log/'
    stamp = '?verify=' + str(time.time_ns())
    if kind == 'news':
        expected = next(x for x in json.loads((repo/'public/data/ai-news.json').read_text()) if x['id'] == content_id)
        remote = json.loads(fetch(base+'data/ai-news.json'+stamp))
        if not any(x == expected for x in remote):
            raise ValueError('Live news JSON does not contain the committed article')
        image_path = expected['image'].lstrip('/')
        if fetch(base+image_path+stamp) != (repo/'public'/image_path).read_bytes():
            raise ValueError('Live SVG differs from committed SVG')
        fetch(base+stamp)
        return base+'#/article/'+expected['slug']
    expected = json.loads((repo/'lessons'/f'{content_id}.json').read_text())
    if json.loads(fetch(base+f'lessons/{content_id}.json'+stamp)) != expected:
        raise ValueError('Live lesson JSON differs from commit')
    if not any(x['id'] == content_id for x in json.loads(fetch(base+'lessons.json'+stamp))['lessons']):
        raise ValueError('Live index missing lesson')
    for mode in ['learner', 'instructor']:
        data = fetch(base+f'downloads/{content_id}-{mode}.pptx'+stamp)
        with zipfile.ZipFile(io.BytesIO(data)) as z:
            if 'ppt/presentation.xml' not in z.namelist() or z.testzip():
                raise ValueError('Invalid published PPTX')
    if not fetch(base+f'downloads/{content_id}-prompts.txt'+stamp).decode('utf-8-sig').strip():
        raise ValueError('Empty prompt download')
    fetch(base+'lessons.html'+stamp)
    return base+'lessons.html?id='+content_id


def deploy(kind, repo):
    result = read_result()
    if result['status'] != 'COMMITTED':
        print('No approved commit; deployment skipped: '+result['status'])
        return
    full_repo = os.environ['GITHUB_REPOSITORY']
    workflow = 'deploy.yml' if kind == 'news' else 'pages.yml'
    try:
        # Token is present only in this trusted step, after Codex has exited.
        import base64
        auth = base64.b64encode(('x-access-token:'+os.environ['GH_TOKEN']).encode()).decode()
        def push():
            return subprocess.run(['git', '-c', 'http.https://github.com/.extraheader=AUTHORIZATION: basic '+auth,
                                   'push', 'origin', 'HEAD:main'], cwd=repo,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        pushed = push()
        if pushed.returncode:
            # Concurrent documentation/workflow updates may move main during Codex research.
            # Rebase once, preserve every reviewed content byte, never force-push.
            snapshots = {p: (repo/p).read_bytes() for p in result.get('files', [])}
            if not snapshots:
                raise RuntimeError('No validated content paths for safe retry')
            subprocess.run(['git','fetch','origin','main'],cwd=repo,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            rebased = subprocess.run(['git','rebase','origin/main'],cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
            if rebased.returncode:
                subprocess.run(['git','rebase','--abort'],cwd=repo,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
                raise RuntimeError('Concurrent content conflict; retry next scheduled run')
            if any((repo/p).read_bytes() != data for p,data in snapshots.items()):
                raise RuntimeError('Reviewed content bytes changed during rebase')
            result['commit'] = subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
            if push().returncode:
                raise RuntimeError('Push retry failed')
        result['status'] = 'PUSHED'
        save_result(result)
        requested = dt.datetime.now(dt.timezone.utc)
        gh('workflow', 'run', workflow, '--repo', full_repo, '--ref', 'main')
        deadline = time.monotonic()+900
        while time.monotonic() < deadline:
            runs = json.loads(gh('api', f'repos/{full_repo}/actions/workflows/{workflow}/runs?event=workflow_dispatch&per_page=20'))['workflow_runs']
            matches = [x for x in runs if x['head_sha'] == result['commit'] and
                       dt.datetime.fromisoformat(x['created_at'].replace('Z','+00:00')) >= requested-dt.timedelta(seconds=5)]
            if matches:
                run = max(matches, key=lambda x: x['id'])
                result['deployment_run_url'] = run['html_url']
                if run['status'] == 'completed':
                    if run['conclusion'] != 'success':
                        raise RuntimeError('Pages workflow failed: '+str(run['conclusion']))
                    # A successful workflow alone is insufficient. Check live bytes and downloads.
                    last = None
                    for _ in range(30):
                        try:
                            result['url'] = verify_live(kind, repo, result['id'])
                            result.update(status='PUBLISHED', verified_at=dt.datetime.now(dt.timezone.utc).isoformat())
                            save_result(result)
                            return
                        except Exception as exc:
                            last = exc
                            time.sleep(10)
                    raise RuntimeError('Live verification failed: '+type(last).__name__)
            time.sleep(15)
        raise RuntimeError('Timed out waiting for matching Pages deployment')
    except Exception as exc:
        # Do not emit subprocess argv (contains the transient authentication header).
        result.update(status='FAILED_DEPLOY', reason=type(exc).__name__+': deployment or live verification failed')
        save_result(result)
        raise SystemExit('Deployment failed; inspect deployment run. Credentials suppressed.')


def report(kind, output):
    result = read_result()
    # Explicit allowlist: never include raw CLI output or files from CODEX_HOME.
    keys = ['status','reason','error','kind','time','ended_at','attempts','id','commit','url','run_url','deployment_run_url','verified_at','next_action','sources']
    result = {k: result[k] for k in keys if k in result}
    result['kind'] = kind
    output.mkdir(parents=True, exist_ok=True)
    (output/'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    text = '# 자동 발행 운영 결과\n\n'
    text += '| 항목 | 값 |\n|---|---|\n'
    for k,v in result.items():
        clean = str(v).replace('|','/').replace('\n',' ')
        text += f'| {k} | {clean} |\n'
    text += '\nPUBLISHED는 배포 워크플로 성공과 실제 데이터·이미지/다운로드 검증을 통과한 상태입니다. 화면 조작 검증은 별도입니다.\n'
    text += '\n조회·다운로드 통계: 별도 daily-analytics 실행을 확인하세요. 미설정 수치를 0으로 해석하지 마세요.\n'
    (output/'report.md').write_text(text, encoding='utf-8')
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8') as f:
            f.write(text)
    print(result['status'])


if __name__ == '__main__':
    p=argparse.ArgumentParser()
    p.add_argument('action', choices=['deploy','report'])
    p.add_argument('--kind', required=True, choices=['news','lesson'])
    p.add_argument('--repo', type=Path, default=Path('.'))
    p.add_argument('--output', type=Path, default=Path('ops-report'))
    a=p.parse_args()
    deploy(a.kind, a.repo.resolve()) if a.action == 'deploy' else report(a.kind, a.output)
