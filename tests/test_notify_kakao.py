import datetime as dt
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
s=importlib.util.spec_from_file_location('notify_kakao',Path(__file__).resolve().parents[1]/'scripts/notify_kakao.py')
n=importlib.util.module_from_spec(s);s.loader.exec_module(n)

class KakaoTests(unittest.TestCase):
    def lesson(self):
        return {'id':'AI-2026-10-CAT08-099','type':'update','released':'2026-09-01','title':'긴 제목'*60,'glance':{'emoji':'📘','one_liner':'핵심 기능'*60},'outcome':['결과물'*20]*3,'pricing':{'access':'freemium','summary':'무료 이용 한도 확인'*30}}
    def test_200_characters_full_url_and_past_badge(self):
        message,url=n.compose(self.lesson(),dt.date(2026,10,25))
        self.assertLessEqual(len(message),200)
        self.assertIn('📚 지난 기능·무료+유료',message)
        self.assertEqual(message.splitlines()[-1],'👉 '+url)
        self.assertTrue(url.endswith('?id=AI-2026-10-CAT08-099'))
    def test_recent_release_does_not_get_past_badge(self):
        lesson=self.lesson();lesson['released']='2026-10-11'
        self.assertNotIn('📚 지난 기능',n.compose(lesson,dt.date(2026,10,25))[0])
    def test_missing_credentials_never_calls_api(self):
        with patch.object(n,'post') as api:
            self.assertEqual(n.send('message','https://example.com',{})['status'],'NOT_CONFIGURED');api.assert_not_called()
    def test_retry_at_most_once_and_self_endpoint_only(self):
        with patch.object(n,'post',side_effect=[n.ApiError(503),{'result_code':0}]) as api:
            result=n.send('m','https://example.com',{'KAKAO_ACCESS_TOKEN':'test'})
            self.assertEqual(result['status'],'SENT');self.assertEqual(api.call_count,2)
            self.assertTrue(all(c.args[0]==n.SEND for c in api.call_args_list))
    def test_timeout_is_uncertain_not_duplicate(self):
        with patch.object(n,'post',side_effect=TimeoutError) as api:
            self.assertEqual(n.send('m','https://example.com',{'KAKAO_ACCESS_TOKEN':'secret'})['status'],'DELIVERY_UNKNOWN')
            self.assertEqual(api.call_count,1)
    def test_invalid_token_refreshes_before_single_resend(self):
        with patch.object(n,'post',side_effect=[n.ApiError(401),{'access_token':'new','refresh_token':'rotated'},{'result_code':0}]) as api:
            r=n.send('m','https://example.com',{'KAKAO_ACCESS_TOKEN':'old','KAKAO_REST_API_KEY':'key','KAKAO_REFRESH_TOKEN':'refresh','KAKAO_CLIENT_SECRET':'client'})
            self.assertEqual(r['status'],'SENT');self.assertTrue(r['refresh_token_rotation_required']);self.assertEqual(api.call_count,3)
    def test_unpublished_and_sent_results_do_not_send(self):
        with tempfile.TemporaryDirectory() as d:
            log=Path(d)/'runs.jsonl'
            for state in ['SKIPPED_NO_NEWS','REJECTED_AVAILABILITY','RATE_LIMITED','FAILED_DEPLOY','COMMITTED']:
                log.write_text(json.dumps({'status':state,'kind':'lesson'}))
                with patch.object(n,'send') as send:
                    self.assertEqual(n.notify(Path(d),log,{})['status'],'NOT_PUBLISHED');send.assert_not_called()
            log.write_text(json.dumps({'status':'PUBLISHED','kind':'lesson','notification':{'status':'SENT'}}))
            self.assertEqual(n.notify(Path(d),log,{})['status'],'ALREADY_SENT')
    def test_notify_preserves_published_status_and_hides_secrets(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'lessons').mkdir();l=self.lesson();(root/'lessons'/(l['id']+'.json')).write_text(json.dumps(l))
            log=root/'runs.jsonl';log.write_text(json.dumps({'status':'PUBLISHED','kind':'lesson','id':l['id'],'url':n.SITE+l['id']})+'\n')
            with patch.object(n,'post',side_effect=n.ApiError(403)):
                n.notify(root,log,{'KAKAO_ACCESS_TOKEN':'super-secret'})
            data=log.read_text();last=json.loads(data.splitlines()[-1]);self.assertEqual(last['status'],'PUBLISHED')
            self.assertEqual(last['notification']['status'],'FAILED');self.assertNotIn('super-secret',data)

if __name__=='__main__':unittest.main()
