import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from cog_core import nexus_addons as a

class AddonTests(unittest.TestCase):
    def test_private_never_recommends_cloud(self):
        self.assertEqual(a.recommendation('private',False)['route'],'blocked')
        self.assertEqual(a.recommendation('restricted',True)['route'],'local-only')
        self.assertEqual(a.recommendation('public',False,True)['route'],'blocked')
        self.assertEqual(a.recommendation('public',False)['route'],'hermes-configured-provider')
        self.assertFalse(a.recommendation('private',True)['automatic_switch'])

    def test_aegis_redaction(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'events.json'
            p.write_text(json.dumps({'events':[{'type':'network-connection','severity':'high','token':'secret'}, {'type':'secret-custom-kind','severity':'private-value'},None]}))
            result=a.summarize_aegis(p)
            self.assertEqual(result['types'],{'network-connection':1,'other':1})
            self.assertEqual(result['invalid'],1)
            self.assertNotIn('secret',json.dumps(result))

    def test_ha_read_only_and_validation(self):
        class Stub:
            def open(self,request,timeout):
                self.req=request
                return io.BytesIO(b'{"entity_id":"light.office","state":"on","attributes":{"secret":"not returned"}}')
        stub=Stub()
        result=a.home_state('http://127.0.0.1:8123','light.office','test-token',opener=stub)
        self.assertEqual(stub.req.get_method(),'GET')
        self.assertEqual(result,{'entity_id':'light.office','state':'on','read_only':True})
        for url in ['http://evil.example:8123','http://127.0.0.1:8123@evil.example:80','http://127.0.0.1:8123/path']:
            with self.assertRaises(ValueError):a.home_state(url,'light.office','token',opener=stub)
        with self.assertRaises(ValueError):a.home_state('http://127.0.0.1:8123','light.office/../','token',opener=stub)

    def test_no_unapproved_launch(self):
        with patch.object(a.subprocess,'Popen') as proc:
            for app,confirmation in [('notepad','no'),('powershell','LAUNCH powershell')]:
                with self.assertRaises(ValueError):a.windows_launch(app,confirmation)
            proc.assert_not_called()

    def test_voice_missing_model_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'audio.wav';p.write_bytes(b'test')
            with self.assertRaises((ValueError,OSError)):a.local_transcribe(p,Path(d)/'missing')

if __name__=='__main__':unittest.main()
