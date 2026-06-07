# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Aleena K (odoo@cybrosys.com)
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
################################################################################
import json
from unittest.mock import patch, Mock
from odoo.tests import tagged
from odoo.tests.common import HttpCase


@tagged('post_install', '-at_install')
class TestOdooPipedriveConnector(HttpCase):
    """
    HttpCase tests for Pipedrive webhook controllers.
    Setup data for tests that involve pre-existing records (update, delete)
    is placed in setUpClass so it is committed by the framework and visible
    to the HTTP controller's separate DB transaction.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Data for test_update_contact_webhook
        cls.update_partner = cls.env['res.partner'].create({
            'name': 'Old Partner',
            'pipedrive_reference': '3002',
        })
        cls.env['pipedrive.record'].create({
            'pipedrive_reference': '3002',
            'record_type': 'partner',
            'odoo_ref': cls.update_partner.id,
        })
        cls.delete_partner = cls.env['res.partner'].create({
            'name': 'Delete Partner',
            'pipedrive_reference': '3003',
        })
        cls.env['pipedrive.record'].create({
            'pipedrive_reference': '3003',
            'record_type': 'partner',
            'odoo_ref': cls.delete_partner.id,
        })

    def test_add_contact_webhook(self):
        """Test add contact webhook creates a new partner."""
        payload = {
            'data': {
                'id': '3001',
                'name': 'Webhook Partner',
                'phones': [{'value': '9876543210'}],
                'emails': [{'value': 'webhook@test.com'}],
            }
        }
        self.url_open(
            '/add_pipedrive_contact',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        partner = self.env['res.partner'].search([
            ('pipedrive_reference', '=', '3001')
        ], limit=1)
        self.assertTrue(partner)

    def test_update_contact_webhook(self):
        """Test update contact webhook updates an existing partner's name."""
        payload = {
            'data': {
                'id': '3002',
                'name': 'Updated Partner',
                'phones': [{'value': '9999999999'}],
                'emails': [{'value': 'updated@test.com'}],
            }
        }
        mock_response = Mock()
        mock_response.json.return_value = {'success': True}

        with patch('requests.put', return_value=mock_response):
            self.url_open(
                '/update_pipedrive_contact',
                data=json.dumps(payload),
                headers={'Content-Type': 'application/json'}
            )
        self.update_partner.invalidate_recordset()
        self.assertEqual(self.update_partner.name, 'Updated Partner')

    def test_delete_contact_webhook(self):
        """
        Test delete contact webhook archives an existing partner.
        """
        payload = {
            'meta': {
                'entity_id': '3003'
            },
            'data': {
                'id': '3003'
            }
        }

        self.url_open(
            '/delete_pipedrive_contact',
            data=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        self.delete_partner.invalidate_recordset()
        deleted_partner = self.env['res.partner'].with_context(
            active_test=False
        ).search([
            ('pipedrive_reference', '=', '3003')
        ], limit=1)
        self.assertTrue(deleted_partner)
        self.assertFalse(deleted_partner.active)
