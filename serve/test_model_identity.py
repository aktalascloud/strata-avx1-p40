import json
from pathlib import Path
import re
import unittest
import urllib.parse
import urllib.request

from serve.frontend import ChatTemplate
from serve.model_identity import public_model_id, configured_model_id
from serve.server import ByteTokenizer, MockEngine, Service, serve


class MachineIds(unittest.TestCase):
    def test_existing_ids_unchanged(self):
        for value in ['swift-1.5-iq3-s', 'Qwen3.8', 'org/model:Q4_K_M']:
            self.assertEqual(public_model_id(value), value)

    def test_friendly_names_are_not_protocol_ids(self):
        self.assertEqual(public_model_id('SC117 Swift1.5 IQ3_S — Q2 baseline'), 'SC117-Swift1.5-IQ3_S-Q2-baseline')
        self.assertEqual(public_model_id('  model name  '), 'model-name')
        self.assertRegex(public_model_id('Модель'), r'^model-[0-9a-f]{12}$')
        self.assertEqual(public_model_id('Модель'), public_model_id('Модель'))

    def test_explicit_id_is_validated(self):
        for value in ['bad id', ' id', '', [], 4]:
            with self.assertRaises(ValueError):
                configured_model_id({'api_model_id': value}, 'fallback')
        self.assertEqual(configured_model_id({'api_model_id': 'safe-id', 'model_name': 'Friendly Name'}, 'x'), 'safe-id')

    def test_aliases_are_safe_and_exact_legacy_labels_work(self):
        tok = ByteTokenizer()
        svc = Service(MockEngine(tok, 'ok'), tok, ChatTemplate(Path(__file__).with_name('chat_template.jinja')),
                      model_name='Friendly Model')
        svc.set_aliases(['Alias One', 'alias-two', 'Alias One'])
        self.assertEqual(svc.model_names(), ['Friendly-Model', 'Alias-One', 'alias-two'])
        self.assertEqual(svc.model_for({'model': 'Alias One'}), 'Alias-One')
        self.assertEqual(svc.model_for({'model': 'Friendly Model'}), 'Friendly-Model')
        self.assertEqual(svc.model_for({'model': ['bad']}), 'Friendly-Model')
        svc.set_aliases([])
        self.assertIsNone(svc.resolve_model_name('Alias One'))


class HttpContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        tok = ByteTokenizer()
        cls.svc = Service(MockEngine(tok, 'ok'), tok, ChatTemplate(Path(__file__).with_name('chat_template.jinja')),
                          model_name='SC117 Swift1.5 IQ3_S — Q2 baseline')
        cls.svc.set_aliases(['Legacy Alias'])
        cls.httpd = serve(cls.svc, host='127.0.0.1', port=0)
        cls.base = 'http://127.0.0.1:' + str(cls.httpd.server_address[1])

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown(); cls.httpd.server_close()

    def get(self, path):
        with urllib.request.urlopen(self.base + path, timeout=10) as response:
            return json.load(response)

    def test_all_discovery_ids_pass_no_whitespace_client_validation(self):
        for path in ['/v1/models', '/models']:
            data = self.get(path)['data']
            for model in data:
                self.assertIsNone(re.search(r'\s', model['id']))
                self.assertTrue(model['display_name'])
                for alias in model.get('aliases', []):
                    self.assertIsNone(re.search(r'\s', alias))
        self.assertEqual(data[0]['display_name'], 'SC117 Swift1.5 IQ3_S — Q2 baseline')

    def test_chat_reply_uses_the_advertised_id(self):
        identity = self.get('/v1/models')['data'][0]['id']
        for asked in [identity, 'SC117 Swift1.5 IQ3_S — Q2 baseline', 'Legacy Alias']:
            payload = {'model': asked, 'messages': [{'role': 'user', 'content': 'hi'}],
                       'max_tokens': 8, 'stream': False}
            req = urllib.request.Request(self.base + '/v1/chat/completions', data=json.dumps(payload).encode(),
                                         headers={'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.load(response)
            self.assertIsNone(re.search(r'\s', result['model']))
            self.assertTrue(result['choices'])

    def test_legacy_display_name_props_still_resolves(self):
        props = self.get('/props?model=' + urllib.parse.quote('SC117 Swift1.5 IQ3_S — Q2 baseline'))
        self.assertIsNone(re.search(r'\s', props['model_alias']))
        self.assertEqual(props['display_name'], 'SC117 Swift1.5 IQ3_S — Q2 baseline')


if __name__ == '__main__':
    unittest.main()
