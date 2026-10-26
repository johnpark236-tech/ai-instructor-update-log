"""v2.4 입력 계약과 기존 필드 보존 검증."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('lesson_index', ROOT/'scripts/build_lessons_index.py')
index = importlib.util.module_from_spec(spec)
spec.loader.exec_module(index)


class GlanceV24Tests(unittest.TestCase):
    def setUp(self):
        self.path = ROOT/'lessons/AI-2026-10-CAT04-019.json'
        self.lesson = json.loads(self.path.read_text())

    def errors(self, key, value):
        d = copy.deepcopy(self.lesson)
        if value is None:
            d['glance'].pop(key, None)
        else:
            d['glance'][key] = value
        return index.check_lesson(self.path, d)

    def test_required_and_lengths(self):
        for key, size in [('what',45),('for_whom',30)]:
            self.assertTrue(self.errors(key,None))
            self.assertTrue(self.errors(key,'가'*(size+1)))
            self.assertFalse(self.errors(key,'가'*size))

    def test_benefits_shape_and_copy_rejection(self):
        b = self.lesson['glance']['benefits']
        for value in [[],b[:2],b+b[:1],[None]*3]:
            self.assertTrue(self.errors('benefits',value))
        for key, value in [('title','가'*13),('text','가'*31),('icon','😀😀'),('icon','x')]:
            changed=copy.deepcopy(b);changed[0][key]=value
            self.assertTrue(self.errors('benefits',changed))
        changed=copy.deepcopy(b)
        for benefit, card in zip(changed,self.lesson['glance']['cards']):
            benefit['title']=card['title']
        self.assertTrue(any('복사' in e for e in self.errors('benefits',changed)))

    def test_style_applies_to_new_fields(self):
        for key in ['what','for_whom']:
            d=copy.deepcopy(self.lesson);d['glance'][key]='설명합니다'
            hits=[]
            index.style_terse.walk(d,(),lambda s,p:(hits.append(p) if index.style_terse.remains(s) else None) or s)
            self.assertIn(('glance',key),hits)

    def test_all_lessons_and_index_contract(self):
        files=list((ROOT/'lessons').glob('*.json'))
        data=json.loads((ROOT/'lessons.json').read_text())
        self.assertEqual(data['count'],len(files))
        for p in files:
            d=json.loads(p.read_text());self.assertFalse(index.check_lesson(p,d),p.name)
        self.assertTrue(all('what' in row for row in data['lessons']))


if __name__=='__main__':unittest.main()
