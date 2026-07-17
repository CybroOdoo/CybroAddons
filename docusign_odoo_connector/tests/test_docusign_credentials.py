# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Akhil @ cybrosys,(odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
###############################################################################

from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError
from unittest.mock import patch
import base64

class TestDocusignCredentials(TransactionCase):

    def setUp(self):
        super(TestDocusignCredentials, self).setUp()
        self.DocusignCredentials = self.env['docusign.credentials']
        self.IrAttachment = self.env['ir.attachment']

        self.attachment1 = self.IrAttachment.create({
            'name': 'test_private_key.txt',
            'type': 'binary',
            'datas': base64.b64encode(b"dummy_key_1"),
        })

        self.attachment2 = self.IrAttachment.create({
            'name': 'test_private_key2.txt',
            'type': 'binary',
            'datas': base64.b64encode(b"dummy_key_2"),
        })

        self.credentials = self.DocusignCredentials.create({
            'name': 'Test Creds',
            'integrator_key': 'test-key',
            'account_id_data': 'test-account',
            'user_id_data': 'test-user',
            'private_key_ids': [(6, 0, [self.attachment1.id])]
        })

    def test_01_constraint_private_key(self):
        """Test the constraint allowing only one private key"""
        # Should raise ValidationError when adding a second key
        with self.assertRaises(ValidationError):
            self.credentials.write({
                'private_key_ids': [(6, 0, [self.attachment1.id, self.attachment2.id])]
            })

    @patch('odoo.addons.docusign_odoo_connector.models.docusign.action_login_docusign')
    def test_02_action_test_credentials_success(self, mock_login):
        """Test successful connection"""
        mock_login.return_value = 200
        
        result = self.credentials.action_test_credentials()
        
        self.assertEqual(result['type'], 'ir.actions.client')
        self.assertEqual(result['tag'], 'display_notification')
        self.assertEqual(result['params']['type'], 'success')
        self.assertEqual(result['params']['message'], 'Connection Successful !')
        
        mock_login.assert_called_once_with(
            'test-user', 'test-account', 'test-key', self.credentials.private_key_ids
        )

    @patch('odoo.addons.docusign_odoo_connector.models.docusign.action_login_docusign')
    def test_03_action_test_credentials_fail(self, mock_login):
        """Test failed connection"""
        mock_login.return_value = 400
        
        with self.assertRaises(UserError) as err:
            self.credentials.action_test_credentials()
        
        self.assertEqual(str(err.exception), "Connection Failed!")
