from odoo.tests import HttpCase, tagged


@tagged('post_install', '-at_install')
class TestBasePwa(HttpCase):

    def test_manifest(self):
        response = self.url_open('/manifest/webmanifest')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['display'], 'standalone')
        self.assertFalse(data['icons'][0]['src'].startswith('/home'))
        self.assertNotIn('cybrosys', data['start_url'])