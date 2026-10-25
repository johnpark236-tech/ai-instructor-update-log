import datetime as dt
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import unified_dashboard as ui

class UnifiedDashboardTests(unittest.TestCase):
    def snapshots(self):
        rows=[{'time':'2026-10-25T00:01:00Z','actions':'failure','status':'PUBLISHED','detail':'https://example.com/article','url':'https://github.com/example/run'},
              {'time':'2026-10-25T00:00:00Z','actions':'success','status':'SKIPPED_NO_NEWS','detail':'근거 없음 | <script>','url':'https://github.com/example/other'}]
        return [{'kind':k,'label':l,'repo':r,'runs':rows,'runs_24h':2,'statuses':{'PUBLISHED':1,'SKIPPED_NO_NEWS':1},'latest_content':{'url':'https://example.com/latest','title':'최신 자료','count':7}} for k,l,r,m in ui.PROJECTS]
    def test_kst_and_nominal_next_are_explicit(self):
        self.assertEqual(ui.kst('2026-10-25T00:01:00Z'),'10-25 09:01')
        now=dt.datetime(2026,10,25,0,6,tzinfo=dt.timezone.utc)
        self.assertEqual(ui.nominal_next(now,5),'10-25 10:05')
    def test_failure_actions_can_have_verified_publication_and_reason_is_visible(self):
        text=ui.render(self.snapshots(),dt.datetime(2026,10,25,tzinfo=dt.timezone.utc))
        self.assertIn('failure | ✅ 게시 확인',text)
        self.assertIn('| 실제 게시 확인 | 1건 | 1건 |',text)
        self.assertIn('근거 없음 &#124; &lt;script&gt;',text)
        self.assertIn('AI 뉴스 실행 내역',text)
        self.assertIn('AI 신기능 교안 실행 내역',text)
    def test_unavailable_is_not_reported_as_zero(self):
        data=self.snapshots();data[1]={'kind':'lesson','label':'AI 교안','repo':'owner/repo','unavailable':'API failure'}
        text=ui.render(data,dt.datetime(2026,10,25,tzinfo=dt.timezone.utc))
        self.assertIn('| 실제 게시 확인 | 1건 | 조회 실패',text)
        self.assertNotIn('javascript:',ui.link('javascript:alert(1)','보기'))

if __name__=='__main__':unittest.main()
