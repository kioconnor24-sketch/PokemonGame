"""Bulk source cells, closed boundaries and exact pinned donor repairs."""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[3]
HERE=ROOT/'Pokemon Game/Averon_Codex_Handoff/design/sinnoh/remaining-donor'
spec=importlib.util.spec_from_file_location('remaining_stage',HERE/'stage_remaining.py')
stage=importlib.util.module_from_spec(spec);spec.loader.exec_module(stage)


def sha(raw):return hashlib.sha256(raw).hexdigest()
def words(raw):return [v[0] for v in struct.iter_unpack('<H',raw)]


class RemainingSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.selection=json.loads((HERE/'selection.json').read_text())
        cls.receipt=json.loads((HERE/'source-receipt.json').read_text())
        cls.headers={m['name']:json.loads((HERE/'staged'/m['name']/'map.json').read_text()) for m in cls.selection['maps']}

    def test_all_91_selected_maps_have_real_outputs_and_identity_roundtrips(self):
        self.assertEqual(91,len(self.selection['maps']))
        self.assertEqual({m['name'] for m in self.selection['maps']},set(self.receipt['maps']))
        for m in self.selection['maps']:
            name=m['name'];r=self.receipt['identity_roundtrips'][name]
            self.assertEqual(m['source_sha256'],r['source_sha256'])
            self.assertEqual(r['source_sha256'],r['output_sha256'])
            self.assertEqual(m['map_blob'],self.receipt['maps'][name]['source_blob'])
            for filename in ('map.bin','border.bin','map.json','attributes.json','collision.png'):
                self.assertTrue((HERE/'staged'/name/filename).is_file())

    def test_exact_source_reconstructed_and_every_closure_only_changes_collision(self):
        for m in self.selection['maps']:
            name=m['name'];raw=(HERE/'staged'/name/'map.bin').read_bytes();values=words(raw)
            self.assertEqual(m['dimensions'][0]*m['dimensions'][1],len(values))
            self.assertEqual(sha(raw),self.receipt['maps'][name]['staged_sha256'])
            # Fixed-point closures may revisit a cell; unwind in reverse order.
            for change in reversed(self.receipt['closure_changes'][name]):
                index=change['y']*m['dimensions'][0]+change['x']
                self.assertEqual(change['after'],values[index])
                self.assertEqual(0,(change['before']^change['after'])&~0xC00)
                self.assertNotEqual(0,change['after']&0xC00)
                values[index]=change['before']
            original=struct.pack('<%dH'%len(values),*values)
            self.assertEqual(m['source_sha256'],sha(original),name)

    def test_every_used_map_and_border_attribute_is_defined(self):
        for m in self.selection['maps']:
            folder=HERE/'staged'/m['name'];attrs=json.loads((folder/'attributes.json').read_text())['used_source_attribute_words']
            for value in words((folder/'map.bin').read_bytes()+(folder/'border.bin').read_bytes()):
                self.assertIn(str(value&1023),attrs,m['name'])
                self.assertTrue(0<=attrs[str(value&1023)]<=65535)

    def test_only_16_broken_borders_are_substituted_under_original_hash_guards(self):
        repairs=self.selection['border_repairs'];self.assertEqual(16,len(repairs))
        self.assertEqual(repairs,self.receipt['border_substitutions'])
        for name,repair in repairs.items():
            self.assertEqual([1]*4,words((HERE/'staged'/name/'border.bin').read_bytes()))
            raw=struct.pack('<4H',*repair['before_words']);replacement=struct.pack('<4H',*repair['after_words'])
            self.assertEqual(replacement,stage.base.repair_border(raw,repair,replacement))
            with self.assertRaises(ValueError):stage.base.repair_border(b'bad',repair,replacement)
            self.assertEqual(0,sum((a^b)&0xFC00 for a,b in zip(words(raw),words(replacement))))
        self.assertEqual(1,len(self.receipt['neutral_header_corrections']))

    def test_duplicate_return_repair_is_exact_nonmutating_and_fails_if_source_changes(self):
        original={'Route221':{'connections':copy.deepcopy(stage.DUPLICATED_ROUTE221)}}
        saved=copy.deepcopy(original);fixed=stage.corrected_headers(original)
        self.assertEqual(saved,original)
        self.assertEqual(stage.DUPLICATED_ROUTE221[:1],fixed['Route221']['connections'])
        for candidate in ([],stage.DUPLICATED_ROUTE221[:1],[dict(stage.DUPLICATED_ROUTE221[0],offset=5)]*2):
            with self.assertRaises(ValueError):stage.corrected_headers({'Route221':{'connections':candidate}})

    def test_warps_are_in_bounds_and_source_order_is_compacted_without_external_events(self):
        ids={h['id']:name for name,h in self.headers.items()}
        for name,h in self.headers.items():
            for kind in ('object_events','coord_events','bg_events'):self.assertEqual([],h[kind])
            self.assertEqual('MAPSEC_PENDING_OWNER',h['region_map_section'])
            self.assertEqual('REGION_SINNOH',h['region'])
            self.assertNotIn('scripts',h)
            translation=self.receipt['warp_index_translation'][name]
            self.assertEqual(list(range(len(h['warp_events']))),list(translation.values()))
            width,height=self.receipt['maps'][name]['dimensions']
            for event in h['warp_events']:
                self.assertTrue(0<=event['x']<width and 0<=event['y']<height)
                self.assertIn(event['dest_map'],ids)
                self.assertTrue(0<=int(event['dest_warp_id'])<len(self.headers[ids[event['dest_map']]]['warp_events']))

    def test_final_seams_have_unique_directions_reciprocal_offsets_and_no_dangling_open_cells(self):
        ids={h['id']:name for name,h in self.headers.items()};opp={'up':'down','down':'up','left':'right','right':'left'}
        for name,h in self.headers.items():
            connections=h['connections'];self.assertEqual(len(connections),len({c['direction'] for c in connections}))
            w,ht=self.receipt['maps'][name]['dimensions'];raw=words((HERE/'staged'/name/'map.bin').read_bytes())
            anchors={(e['x'],e['y']) for e in h['warp_events']}
            for direction in opp:
                connection=next((c for c in connections if c['direction']==direction),None)
                points=([(x,0 if direction=='up' else ht-1) for x in range(w)] if direction in ('up','down') else [(0 if direction=='left' else w-1,y) for y in range(ht)])
                if connection:
                    target=ids[connection['map']];th=self.headers[target]
                    self.assertEqual(1,len([c for c in th['connections'] if c['map']==h['id'] and c['direction']==opp[direction] and c['offset']==-connection['offset']]))
                    tw,tall=self.receipt['maps'][target]['dimensions'];other=words((HERE/'staged'/target/'map.bin').read_bytes())
                for x,y in points:
                    if (x,y) in anchors or raw[y*w+x]&0xC00:continue
                    self.assertIsNotNone(connection,(name,x,y))
                    tx,ty=stage.base.destination((x,y),direction,connection['offset'],tw,tall)
                    self.assertTrue(0<=tx<tw and 0<=ty<tall)
                    self.assertEqual(0,other[ty*tw+tx]&0xC00)

    def test_bad_selection_refused_before_output_creation(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'out'
            for kind in ('revision','empty','duplicate'):
                candidate=copy.deepcopy(self.selection)
                if kind=='revision':candidate['donor_revision']='0'*40
                if kind=='empty':candidate['maps']=[]
                if kind=='duplicate':candidate['maps'].append(candidate['maps'][0])
                with self.assertRaises(ValueError):stage.build(Path(temp)/'no-donor',out,candidate)
                self.assertFalse(out.exists())


if __name__=='__main__':unittest.main()
