# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from unittest.mock import patch
from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError


@tagged('post_install', '-at_install')
class TestWhatsappAuthenticate(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.config_manager = cls.env['configuration.manager'].create({
            'instance': 'instance_123',
            'token': 'token_abc',
            'state': 'draft',
        })

    def test_01_check_active_connected(self):
        """Test scanning connected whatsapp succeeds and verifies config manager."""
        mock_response_data = {
            'is_connected': True
        }
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response_data

            wizard = self.env['whatsapp.authenticate'].create({
                'qrcode': b'dummyqrcode',
                'configuration_manager_id': self.config_manager.id,
            })
            # Creating record triggers _check_active constrains method
            self.assertEqual(self.config_manager.state, 'verified')

    def test_02_check_active_not_connected_fails(self):
        """Test scanning when not connected displays connection check warnings."""
        mock_response_data = {
            'is_connected': False
        }
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response_data

            self.config_manager.state = 'draft'
            # Note: since state is not verified and is_connected is false, it returns a notification but wait!
            # Let's see _check_active method:
            # if 'is_connected' in req.json().keys():
            #     if req.json()['is_connected']:
            #         self.configuration_manager_id.state = "verified"
            # else:
            #     raise ValidationError("Please scan...")
            # if self.configuration_manager_id.state != 'verified':
            #     return { ... }
            # Under standard Odoo, constrains methods that return dictionary/notifications do not fail/rollback unless raised,
            # but we can verify the state remains unverified.
            wizard = self.env['whatsapp.authenticate'].create({
                'qrcode': b'dummyqrcode',
                'configuration_manager_id': self.config_manager.id,
            })
            self.assertNotEqual(self.config_manager.state, 'verified')

    def test_03_check_active_no_is_connected_key_fails(self):
        """Test scanning raises ValidationError when is_connected key is missing in response."""
        mock_response_data = {}
        with patch('requests.get') as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = mock_response_data

            self.config_manager.state = 'draft'
            with self.assertRaises(ValidationError) as ctx:
                self.env['whatsapp.authenticate'].create({
                    'qrcode': b'dummyqrcode',
                    'configuration_manager_id': self.config_manager.id,
                })
            self.assertIn("Please scan and connect your whatsapp web", str(ctx.exception))
