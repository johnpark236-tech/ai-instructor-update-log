import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

spec=importlib.util.spec_from_file_location('cloud_ops',Path(__file__).resolve().parents[1]/'cloud_ops.py')
ops=importlib.util.module_from_spec(spec);spec.loader.exec_module(ops)

class CloudOpsTests(unittest.TestCase):
    def test_live_news_requires_exact_article_and_svg(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'public/data').mkdir(parents=True);(root/'public/images').mkdir()
            a={'id':'ai-auto-test','slug':'ai-auto-test','image':'/images/ai-auto-test.svg'}
            (root/'public/data/ai-news.json').write_text(json.dumps([a]));(root/'public/images/ai-auto-test.svg').write_bytes(b'<svg/>')
            with patch.object(ops,'fetch',side_effect=[json.dumps([a]).encode(),b'<svg/>',b'<html/>']):
                self.assertIn('#/article/ai-auto-test',ops.verify_live('news',root,a['id']))
            with patch.object(ops,'fetch',return_value=b'[]'):
                with self.assertRaisesRegex(ValueError,'committed article'):ops.verify_live('news',root,a['id'])
            with patch.object(ops,'fetch',side_effect=[json.dumps([a]).encode(),b'wrong']):
                with self.assertRaisesRegex(ValueError,'SVG'):ops.verify_live('news',root,a['id'])

    def test_lesson_publication_requires_all_downloads(self):
        import io, zipfile
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'lessons').mkdir()
            lesson={'id':'AI-test'};(root/'lessons/AI-test.json').write_text(json.dumps(lesson))
            buf=io.BytesIO()
            with zipfile.ZipFile(buf,'w') as z:z.writestr('ppt/presentation.xml','<presentation/>')
            good=[json.dumps(lesson).encode(),b'{"lessons":[{"id":"AI-test"}]}',buf.getvalue(),buf.getvalue(),b'prompt text',b'<html/>']
            with patch.object(ops,'fetch',side_effect=good):
                self.assertTrue(ops.verify_live('lesson',root,'AI-test').endswith('lessons.html?id=AI-test'))
            with patch.object(ops,'fetch',side_effect=good[:2]+[b'not a pptx']):
                with self.assertRaises(zipfile.BadZipFile):ops.verify_live('lesson',root,'AI-test')

    def test_nonapproved_results_never_push(self):
        for status in ['FAILED_SEARCH','RATE_LIMITED','SKIPPED_NO_NEWS','REJECTED_FACT_CHECK']:
            with patch.object(ops,'read_result',return_value={'status':status}),patch.object(ops.subprocess,'run') as run:
                ops.deploy('news',Path('.'));run.assert_not_called()

    def test_push_failure_never_reports_published_or_credentials(self):
        with patch.object(ops,'read_result',return_value={'status':'COMMITTED','id':'x','commit':'sha'}),patch.dict(ops.os.environ,{'GITHUB_REPOSITORY':'owner/repo','GH_TOKEN':'secret-test-token'}),patch.object(ops.subprocess,'run',side_effect=RuntimeError('secret-test-token')),patch.object(ops,'save_result') as save:
            with self.assertRaises(SystemExit):ops.deploy('news',Path('.'))
            result=save.call_args.args[0]
            self.assertEqual(result['status'],'FAILED_DEPLOY');self.assertNotIn('secret-test-token',json.dumps(result))

    def test_concurrent_noncontent_main_update_rebases_once_and_verifies_new_sha(self):
        import datetime as dt
        import subprocess
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'article.json').write_bytes(b'reviewed content')
            result={'status':'COMMITTED','id':'x','commit':'old','files':['article.json']}
            run={'id':1,'head_sha':'rebased','created_at':dt.datetime.now(dt.timezone.utc).isoformat(),'status':'completed','conclusion':'success','html_url':'https://github.com/example/run'}
            responses=[subprocess.CompletedProcess([],code,b'',b'') for code in [1,0,0,0]]
            with patch.object(ops,'read_result',return_value=result),patch.dict(ops.os.environ,{'GITHUB_REPOSITORY':'owner/repo','GH_TOKEN':'test-token'}),patch.object(ops.subprocess,'run',side_effect=responses) as commands,patch.object(ops.subprocess,'check_output',return_value='rebased'),patch.object(ops,'gh',side_effect=['',json.dumps({'workflow_runs':[run]})]),patch.object(ops,'verify_live',return_value='https://example/article'),patch.object(ops,'save_result') as save:
                ops.deploy('news',root)
                self.assertEqual(save.call_args.args[0]['status'],'PUBLISHED')
                self.assertEqual(save.call_args.args[0]['commit'],'rebased')
                self.assertFalse(any('--force' in call.args[0] for call in commands.call_args_list))

    def test_report_does_not_upload_unapproved_fields(self):
        with tempfile.TemporaryDirectory() as d,patch.object(ops,'read_result',return_value={'status':'RATE_LIMITED','token':'secret','raw_cli':'secret'}):
            ops.report('lesson',Path(d));self.assertNotIn('secret',(Path(d)/'result.json').read_text())
