# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from unittest.mock import MagicMock, patch
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestConfigurationManager(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.pos_config = cls.env.ref('point_of_sale.pos_config_main', raise_if_not_found=False)
        if not cls.pos_config:
            cls.pos_config = cls.env['pos.config'].search([], limit=1)
        cls.configuration = cls.env['configuration.manager'].sudo().create({
            'instance': 'instance-1',
            'token': 'token-1',
            'config_id': cls.pos_config.id,
        })

    def test_action_authenticate_returns_auth_wizard(self):
        def mock_request(*args, **kwargs):
            response = MagicMock()
            response.status_code = 200
            response.text = '{"status": {"accountStatus": {"substatus": "normal"}}}'
            response.json.return_value = {
                'status': {'accountStatus': {'substatus': 'normal'}}
            }
            return response

        with patch('requests.request', side_effect=mock_request), \
             patch.object(type(self.configuration), 'get_qr_code', return_value='{"qrCode": "QRDATA"}'), \
             patch.object(type(self.configuration), 'open_authenticate_wizard', return_value={'action': 'wizard'}):
            result = self.configuration.action_authenticate()

        self.assertEqual(result, {'action': 'wizard'})

    def test_action_authenticate_returns_connected_notification(self):
        def mock_request(*args, **kwargs):
            response = MagicMock()
            response.status_code = 200
            response.text = '{"status": {"accountStatus": {"substatus": "connected"}}}'
            response.json.return_value = {
                'status': {'accountStatus': {'substatus': 'connected'}}
            }
            return response

        with patch('requests.request', side_effect=mock_request):
            result = self.configuration.action_authenticate()

        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')
        self.assertEqual(result['params']['type'], 'success')

    def test_action_authenticate_invalid_status_raises(self):
        def mock_request(*args, **kwargs):
            response = MagicMock()
            response.status_code = 400
            response.text = 'bad request'
            return response

        with patch('requests.request', side_effect=mock_request):
            with self.assertRaises(ValidationError):
                self.configuration.action_authenticate()

    def test_get_qr_code_returns_text(self):
        response = MagicMock()
        response.status_code = 200
        response.text = '{"qrCode": "QRDATA"}'

        with patch('requests.get', return_value=response):
            result = self.configuration.get_qr_code()

        self.assertEqual(result, '{"qrCode": "QRDATA"}')

    def test_display_notification_returns_action(self):
        result = self.configuration.display_notification('success', 'Connected')
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')
        self.assertEqual(result['params']['message'], 'Connected')
        self.assertEqual(result['params']['type'], 'success')

    def test_open_authenticate_wizard_builds_action(self):
        result = self.configuration.open_authenticate_wizard('{"qrCode": "HELLO"}')
        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'whatsapp.authenticate')
        self.assertEqual(result['target'], 'new')
        self.assertIn('default_qrcode', result['context'])
