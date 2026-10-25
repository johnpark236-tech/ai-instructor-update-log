#!/usr/bin/env python3
"""Read-only combined GitHub Actions Summary for news and lessons."""
import base64
import datetime as dt
import html
import json
import os
from pathlib import Path
import dashboard

PROJECTS = [('news', 'AI 뉴스', 'johnpark236-tech/mannal_news', 5),
            ('lesson', 'AI 신기능 교안', 'johnpark236-tech/ai-instructor-update-log', 35)]
KST = dt.timezone(dt.timedelta(hours=9))
LABELS = {'PUBLISHED':'✅ 게시 확인', 'COMMITTED':'🟡 커밋 완료·배포 대기',
          'PUSHED':'🟡 업로드 완료·배포 대기', 'RATE_LIMITED':'⏸ 구독 한도 대기',
          'SKIPPED_NO_NEWS':'ℹ 신규 자료 없음', 'SKIPPED_DUPLICATE':'ℹ 중복으로 생략',
          'REJECTED_AVAILABILITY':'🚫 이용 조건 근거 부족', 'REJECTED_FACT_CHECK':'🚫 사실 검수 반려',
          'REJECTED_SCHEMA':'🚫 형식 검사 반려', 'FAILED_SEARCH':'❌ 출처 조사 실패',
          'FAILED_GENERATION':'❌ 작성 실패', 'FAILED_DEPLOY':'❌ 배포 확인 실패',
          'AUTH_FAILED':'❌ 인증 오류', 'UNKNOWN_ERROR':'❓ 미분류 오류',
          'UNRECORDED':'❓ 결과 미기록', 'RUNNING':'🔄 실행 중'}


def clean(value, limit=400):
    return html.escape(str(value or '')[:limit]).replace('|','&#124;').replace('\n',' ')


def kst(value):
    if not value:
        return '확인 필요'
    try:
        return dt.datetime.fromisoformat(value.replace('Z','+00:00')).astimezone(KST).strftime('%m-%d %H:%M')
    except (ValueError, TypeError):
        return clean(value)


def link(url, label):
    if not isinstance(url,str) or not url.startswith('https://'):
        return clean(label)
    return '['+clean(label)+']('+url.replace(' ','%20').replace(')','%29')+')'


def nominal_next(now, minute):
    target=now.astimezone(KST).replace(minute=minute,second=0,microsecond=0)
    if target<=now.astimezone(KST):
        target+=dt.timedelta(hours=1)
    return target.strftime('%m-%d %H:%M')


def latest_content(repo, kind):
    path='public/data/ai-news.json' if kind=='news' else 'lessons.json'
    blob=dashboard.api(f'repos/{repo}/contents/{path}?ref=main')
    data=json.loads(base64.b64decode(blob['content']))
    records=data if kind=='news' else data['lessons']
    if not records:
        return None
    x=records[0]
    url=('https://mannalkorean.com/#/article/'+x['id'] if kind=='news' else
         'https://johnpark236-tech.github.io/ai-instructor-update-log/lessons.html?id='+x['id'])
    return {'title':x['title'],'id':x['id'],'url':url,'time':x.get('publishedAt',x.get('created_at')),'count':len(records)}


def render(snapshots, now):
    text='# 📰 AI 뉴스 · 📘 AI 교안 자동 작성 현황\n\n'
    text+='갱신: **'+now.astimezone(KST).strftime('%Y-%m-%d %H:%M KST')+'** · 20분 간격 갱신 · Run workflow로 수동 갱신\n\n'
    text+='**실제 발행과 Actions 결과를 따로 표시합니다.** 녹색 Success도 신규 발행 0건일 수 있습니다.\n\n'
    text+='| 항목 | AI 뉴스 | AI 신기능 교안 |\n|---|---|---|\n'
    def metric(s, key):
        if s.get('unavailable'):
            return '조회 실패·아래 사유 확인'
        rows=s.get('runs',[]);counts=s.get('statuses',{})
        recent=rows[0] if rows else {}
        if key=='schedule':return '매시 '+('05' if s['kind']=='news' else '35')+'분'
        if key=='next':return nominal_next(now,5 if s['kind']=='news' else 35)+' 예정'
        if key=='last':return kst(recent.get('time'))
        if key=='state':return LABELS.get(recent.get('status'),clean(recent.get('status','기록 없음')))
        if key=='runs':return str(s.get('runs_24h',0))+'회'
        if key=='published':return str(counts.get('PUBLISHED',0))+'건'
        if key=='skipped':return str(sum(v for k,v in counts.items() if k.startswith('SKIPPED')))+'회'
        if key=='rejected':return str(sum(v for k,v in counts.items() if k.startswith('REJECTED')))+'회'
        if key=='failed':return str(sum(v for k,v in counts.items() if k.startswith('FAILED') or k in ('AUTH_FAILED','UNKNOWN_ERROR')))+'회'
        if key=='quota':return str(counts.get('RATE_LIMITED',0))+'회'
        if key=='unknown':return str(counts.get('UNRECORDED',0))+'회'
        if key=='gaps':return str(len(s.get('observed_schedule_gaps_over_90_minutes',[])))+'구간'
        if key=='verified':
            x=next((r for r in rows if r['status']=='PUBLISHED'),None)
            return link(x.get('content_url',x.get('detail')),kst(x['time'])+' 실행에서 확인') if x else '24시간 내 확인 기록 없음'
        if key=='latest':
            x=s.get('latest_content');return link(x['url'],x['title']) if x else '조회 불가'
        if key=='total':
            x=s.get('latest_content');return str(x['count'])+'개' if x else '조회 불가'
    for label,key in [('정기 실행','schedule'),('다음 정기 예약','next'),('최근 실행 KST','last'),('최근 발행 상태','state'),('최근 24시간 실행','runs'),('실제 게시 확인','published'),('생략','skipped'),('검수 반려','rejected'),('작성·배포·인증 실패','failed'),('구독 한도 대기','quota'),('발행 결과 미기록','unknown'),('90분 초과 예약 실행 간격','gaps'),('최근 게시 확인','verified'),('최신 등록 콘텐츠','latest'),('전체 콘텐츠','total')]:
        text+='| '+label+' | '+' | '.join(metric(s,key) for s in snapshots)+' |\n'
    text+='\n최신 등록 콘텐츠는 저장소 기준이며, 별도 작성자가 추가했을 수 있습니다. 자동 발행 수는 발행 결과 기록으로 집계합니다. 조회 실패·미기록을 0건으로 해석하지 마세요.\n\n'
    text+='다음 예약은 설정상 예정이며 GitHub 지연이 가능합니다. 90분 초과 간격은 관측값으로, 누락·지연을 확정 구분하지 않습니다. 한도 부족·근거 부족 시 게시를 생략합니다.\n\n'
    for s in snapshots:
        text+='## '+s['label']+' 실행 내역\n\n'
        repo=s['repo'];text+=link('https://github.com/'+repo+'/actions/workflows/codex-cloud-hourly-'+s['kind']+'.yml','발행 실행 전체 기록')+' · '+link('https://github.com/'+repo+'/actions/workflows/publishing-dashboard.yml','개별 운영 대시보드')+'\n\n'
        if s.get('unavailable'):
            text+='⚠ '+clean(s['unavailable'])+'\n\n';continue
        text+='| 실행 KST | Actions | 발행 상태 | 원인·결과 | 실행 기록 |\n|---|---|---|---|---|\n'
        for r in s.get('runs',[])[:24]:
            text+='| '+kst(r['time'])+' | '+clean(r['actions'])+' | '+LABELS.get(r['status'],clean(r['status']))+' | '+clean(r.get('detail'))+' | '+link(r['url'],'열기')+' |\n'
        text+='\n'
    text+='방문자·다운로드 통계는 별도 연결이 필요한 지표입니다. 이 화면은 자동 작성·검수·배포 현황을 표시합니다.\n'
    return text


def main():
    summary=os.environ.pop('GITHUB_STEP_SUMMARY',None)
    snapshots=[]
    try:
        for kind,label,repo,minute in PROJECTS:
            try:
                data=dashboard.build(repo,kind,recover=False)
                if data is None:
                    data=json.loads(Path('ops-dashboard/dashboard.json').read_text())
                data.update(kind=kind,label=label,repo=repo)
                try:data['latest_content']=latest_content(repo,kind)
                except Exception:data['latest_content']=None
            except Exception as exc:
                data={'kind':kind,'label':label,'repo':repo,'unavailable':type(exc).__name__+' — GitHub 조회 권한·네트워크와 개별 대시보드를 확인하세요.'}
            snapshots.append(data)
    finally:
        if summary:os.environ['GITHUB_STEP_SUMMARY']=summary
    now=dt.datetime.now(dt.timezone.utc)
    text=render(snapshots,now)
    out=Path('ops-dashboard');out.mkdir(exist_ok=True)
    (out/'unified.md').write_text(text,encoding='utf-8')
    (out/'unified.json').write_text(json.dumps({'checked_at':now.isoformat(),'projects':snapshots},ensure_ascii=False,indent=2),encoding='utf-8')
    if summary:
        with open(summary,'a',encoding='utf-8') as f:f.write(text)
    print('Unified dashboard saved. Project reads: '+str(sum(not x.get('unavailable') for x in snapshots))+'/2')
    if any(x.get('unavailable') for x in snapshots):
        raise SystemExit('Dashboard has an unavailable project; see Summary')

if __name__=='__main__':main()
