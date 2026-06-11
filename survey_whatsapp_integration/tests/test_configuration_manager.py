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
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestConfigurationManager(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.configuration = cls.env['configuration.manager'].sudo().create({
            'instance': 'instance-1',
            'token': 'token-1',
        })

    def test_action_authenticate_returns_qr_wizard(self):
        response = MagicMock()
        response.status_code = 200
        response.text = 'ok'
        response.json.return_value = {'qr': 'data:image/png;base64,QUJD'}

        with patch('requests.get', return_value=response):
            result = self.configuration.action_authenticate()

        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'whatsapp.authenticate')
        self.assertEqual(result['context']['default_qrcode'], 'QUJD')

    def test_action_authenticate_returns_connected_notification(self):
        response = MagicMock()
        response.status_code = 200
        response.text = 'ok'
        response.json.return_value = {'is_connected': True}

        with patch('requests.get', return_value=response):
            result = self.configuration.action_authenticate()

        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')
        self.assertEqual(result['params']['type'], 'success')

    def test_action_authenticate_invalid_status_raises(self):
        response = MagicMock()
        response.status_code = 400
        response.text = 'bad request'
        response.json.return_value = {}

        with patch('requests.get', return_value=response):
            with self.assertRaises(Exception):
                self.configuration.action_authenticate()

    def test_display_notification_returns_action(self):
        result = self.configuration.display_notification('success', 'Connected')
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')
        self.assertEqual(result['params']['message'], 'Connected')

    def test_open_authenticate_wizard_returns_action(self):
        result = self.configuration.open_authenticate_wizard('QRCODE')
        self.assertEqual(result['type'], 'ir.actions.act_window')
        self.assertEqual(result['res_model'], 'whatsapp.authenticate')
        self.assertEqual(result['context']['default_qrcode'], 'QRCODE')
