#!/usr/bin/env python3
"""Notify only the authenticated user's own Kakao chat after verified publication."""
import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import socket
import urllib.error
import urllib.parse
import urllib.request

SITE='https://johnpark236-tech.github.io/ai-instructor-update-log/lessons.html?id='
SEND='https://kapi.kakao.com/v2/api/talk/memo/default/send'
TOKEN='https://kauth.kakao.com/oauth/token'

class ApiError(Exception):
    def __init__(self,status):self.status=status


def compact(value):
    if isinstance(value,list):value=' + '.join(str(x) for x in value)
    return re.sub(r'\s+',' ',str(value or '')).strip()


def compose(lesson, today=None):
    lesson_id=lesson['id']
    if not re.fullmatch(r'AI-\d{4}-\d{2}-CAT\d{2}-\d{3}',lesson_id):raise ValueError('Invalid lesson ID')
    today=today or dt.datetime.now(dt.timezone(dt.timedelta(hours=9))).date()
    kind='신규 AI' if lesson.get('type')=='new' else '기존 AI'
    try:
        if (today-dt.date.fromisoformat(lesson['released'][:10])).days>14:kind='📚 지난 기능'
    except (KeyError,ValueError,TypeError):pass
    pricing=lesson.get('pricing',{})
    cost={'free':'무료','freemium':'무료+유료','paid':'유료'}.get(pricing.get('access'),'요금 확인 필요')
    glance=lesson.get('glance',{})
    parts=[compact(glance.get('one_liner') or lesson.get('title')),compact(lesson.get('outcome')),compact(pricing.get('summary'))]
    parts=[x[:n] for x,n in zip(parts,[50,35,35])]
    url=SITE+lesson_id
    def text():
        return f'📘[{kind}·{cost}] {compact(glance.get("emoji"))[:4]} {parts[0]}\n🎁 {parts[1]}\n💳 {parts[2]}\n👉 {url}'
    while len(text())>200:
        # Preserve the final URL and headings; shorten explanatory fields only.
        index=next((i for i in [0,1,2] if len(parts[i])>4),None)
        if index is None:raise ValueError('Message cannot fit without truncating URL')
        parts[index]=parts[index][:-1]
    return text(),url


def post(url, fields, token=None):
    headers={'Content-Type':'application/x-www-form-urlencoded;charset=utf-8'}
    if token:headers['Authorization']='Bearer '+token
    request=urllib.request.Request(url,data=urllib.parse.urlencode(fields).encode(),headers=headers,method='POST')
    try:
        with urllib.request.urlopen(request,timeout=35) as response:return json.load(response)
    except urllib.error.HTTPError as exc:
        # Never include response bodies, headers or credentials in logs.
        raise ApiError(exc.code) from None


def refresh(env):
    if not env.get('KAKAO_REST_API_KEY') or not env.get('KAKAO_REFRESH_TOKEN'):raise ApiError(401)
    fields={'grant_type':'refresh_token','client_id':env['KAKAO_REST_API_KEY'],'refresh_token':env['KAKAO_REFRESH_TOKEN']}
    if env.get('KAKAO_CLIENT_SECRET'):fields['client_secret']=env['KAKAO_CLIENT_SECRET']
    result=post(TOKEN,fields)
    if not result.get('access_token'):raise ApiError(401)
    return result['access_token'],bool(result.get('refresh_token'))


def send(message,url,env):
    token=env.get('KAKAO_ACCESS_TOKEN','')
    renewable=bool(env.get('KAKAO_REST_API_KEY') and env.get('KAKAO_REFRESH_TOKEN'))
    if not token and not renewable:return {'status':'NOT_CONFIGURED','channel':'kakao','attempts':0}
    rotated=False
    try:
        if not token:token,rotated=refresh(env)
        template={'object_type':'text','text':message,'link':{'web_url':url,'mobile_web_url':url},'button_title':'교안 보기'}
        for attempt in range(1,3):
            try:
                response=post(SEND,{'template_object':json.dumps(template,ensure_ascii=False)},token)
                if response.get('result_code')!=0:return {'status':'FAILED','channel':'kakao','attempts':attempt,'reason':'Kakao returned a nonzero result'}
                return {'status':'SENT','channel':'kakao','attempts':attempt,'refresh_token_rotation_required':rotated}
            except ApiError as exc:
                if attempt==1 and exc.status==401 and renewable:
                    token,rotated=refresh(env)
                    continue
                if attempt==1 and (exc.status>=500 or exc.status==429):continue
                return {'status':'FAILED','channel':'kakao','attempts':attempt,'http_status':exc.status}
    except ApiError as exc:
        return {'status':'AUTH_FAILED','channel':'kakao','http_status':exc.status,'attempts':0}
    except (urllib.error.URLError,TimeoutError,socket.timeout):
        # A timeout after POST may already have delivered; do not blindly duplicate.
        return {'status':'DELIVERY_UNKNOWN','channel':'kakao','reason':'Network result uncertain; no automatic resend'}
    return {'status':'FAILED','channel':'kakao'}


def notify(repo,log,env=None):
    env=os.environ if env is None else env
    if not log.exists():return {'status':'NOT_PUBLISHED','channel':'kakao'}
    result=json.loads(log.read_text(encoding='utf-8').splitlines()[-1])
    if result.get('status')!='PUBLISHED' or result.get('kind')!='lesson':return {'status':'NOT_PUBLISHED','channel':'kakao'}
    if result.get('notification',{}).get('status')=='SENT':return {'status':'ALREADY_SENT','channel':'kakao'}
    lesson=json.loads((repo/'lessons'/(result['id']+'.json')).read_text(encoding='utf-8-sig'))
    message,url=compose(lesson)
    if result.get('url')!=url:raise ValueError('Verified publication URL mismatch')
    outcome=send(message,url,env)
    result['notification']=outcome
    with log.open('a',encoding='utf-8') as f:f.write(json.dumps(result,ensure_ascii=False)+'\n')
    return outcome


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--repo',type=Path,default=Path('.'));p.add_argument('--log',type=Path,required=True)
    args=p.parse_args()
    try:result=notify(args.repo,args.log.expanduser())
    except Exception as exc:result={'status':'FAILED','channel':'kakao','reason':type(exc).__name__}
    print('Kakao notification: '+json.dumps(result,ensure_ascii=False))
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        with open(os.environ['GITHUB_STEP_SUMMARY'],'a',encoding='utf-8') as f:f.write('\n## 카카오톡 알림\n\n'+result['status']+'\n\nNOT_CONFIGURED는 GitHub Secrets 설정이 필요한 상태입니다.\n')
