"""Regression checks for backup hourly execution, independent of credentials."""
import ast
import datetime as dt
import pathlib
import unittest

source=(pathlib.Path(__file__).resolve().parents[1]/'dashboard.py').read_text(encoding='utf-8')
tree=ast.parse(source)
function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='recovery_due')
namespace={'dt':dt}
exec(compile(ast.Module(body=[function],type_ignores=[]),'<recovery guard>','exec'),namespace)
due=namespace['recovery_due']

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.now=dt.datetime(2026,10,25,1,0,tzinfo=dt.timezone.utc)
    def run_at(self,minutes,status='completed'):
        return {'created_at':(self.now-dt.timedelta(minutes=minutes)).isoformat(),'status':status}
    def test_hour_boundary_and_no_repeated_calls_within_hour(self):
        self.assertFalse(due([self.run_at(59)],self.now))
        self.assertTrue(due([self.run_at(60)],self.now))
        self.assertTrue(due([self.run_at(120)],self.now))
    def test_active_or_queued_job_blocks_backup(self):
        for state in ['in_progress','queued','waiting','pending']:
            self.assertFalse(due([self.run_at(180,state)],self.now))
    def test_latest_actual_run_controls_recovery_even_if_input_unsorted(self):
        self.assertFalse(due([self.run_at(180),self.run_at(5)],self.now))
    def test_missing_history_does_not_dispatch_blindly(self):
        self.assertFalse(due([],self.now))

if __name__=='__main__':
    unittest.main()
