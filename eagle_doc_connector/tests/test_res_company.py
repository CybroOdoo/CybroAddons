# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NON INFRINGEMENT. IN NO EVENT SHALL
#    THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,ARISING
#    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
###############################################################################
from unittest.mock import patch, MagicMock
from odoo.tests import tagged
from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


@tagged('post_install', '-at_install')
class TestResCompany(TransactionCase):
    """Test suite for ResCompany Eagle Doc sub-business linkage and synchronization."""

    def setUp(self):
        super().setUp()
        self.company = self.env['res.company'].create({
            'name': 'Test Eagle Company',
            'email': 'test@eaglecompany.com',
            'phone': '+123456789',
            'eagle_sub_business_industry': 'IT',
            'eagle_sub_business_account_type': 'SKR04',
        })
        self.env['ir.config_parameter'].sudo().set_param('eagle_doc.api_key', 'test_key')

    def test_01_profile_sync_flag_on_write(self):
        """Verify is_eagle_doc_profile_synced is cleared when relevant fields change."""
        self.company.eagle_sub_business_id = 'sub_bus_123'
        self.company.is_eagle_doc_profile_synced = True

        self.company.write({'street': '123 Main St'})
        self.assertFalse(self.company.is_eagle_doc_profile_synced)

    @patch('odoo.addons.eagle_doc_connector.models.res_company.EagleDocAPI.create_sub_business')
    def test_02_action_eagle_create_sub_business(self, mock_create):
        """Verify successful sub-business creation for company."""
        mock_create.return_value = {'id': 'sub_bus_new_101'}

        self.company.action_eagle_create_sub_business()
        self.assertEqual(self.company.eagle_sub_business_id, 'sub_bus_new_101')
        self.assertTrue(self.company.is_eagle_doc_profile_synced)

    def test_03_action_eagle_create_sub_business_already_linked(self):
        """Verify UserError is raised if company is already linked."""
        self.company.eagle_sub_business_id = 'sub_bus_existing'
        with self.assertRaises(UserError):
            self.company.action_eagle_create_sub_business()

    @patch('odoo.addons.eagle_doc_connector.models.res_company.EagleDocAPI.update_sub_business')
    def test_04_action_eagle_update_sub_business(self, mock_update):
        """Verify sub-business profile update."""
        self.company.eagle_sub_business_id = 'sub_bus_123'
        self.company.is_eagle_doc_profile_synced = False

        res = self.company.action_eagle_update_sub_business()
        mock_update.assert_called_once()
        self.assertTrue(self.company.is_eagle_doc_profile_synced)
        self.assertEqual(res.get('type'), 'ir.actions.client')

    def test_05_action_eagle_update_sub_business_unlinked(self):
        """Verify UserError if updating unlinked company."""
        self.company.eagle_sub_business_id = False
        with self.assertRaises(UserError):
            self.company.action_eagle_update_sub_business()

    @patch('odoo.addons.eagle_doc_connector.models.res_company.EagleDocAPI.delete_sub_business')
    def test_06_action_eagle_delete_sub_business(self, mock_delete):
        """Verify deleting sub-business clears local reference."""
        mock_delete.return_value = True
        self.company.eagle_sub_business_id = 'sub_bus_123'

        self.company.action_eagle_delete_sub_business()
        self.assertFalse(self.company.eagle_sub_business_id)

    @patch('odoo.addons.eagle_doc_connector.models.res_company.EagleDocAPI.batch_create_sub_businesses')
    def test_07_action_eagle_batch_create_sub_businesses(self, mock_batch):
        """Verify batch creation of sub-businesses for multiple unlinked companies."""
        company2 = self.env['res.company'].create({'name': 'Second Test Company'})
        mock_batch.return_value = {
            'results': [
                {
                    'externalRef': f'odoo-company-{self.company.id}',
                    'outcome': 'CREATED',
                    'subBusinessId': 'sub_batch_1',
                },
                {
                    'externalRef': f'odoo-company-{company2.id}',
                    'outcome': 'CREATED',
                    'subBusinessId': 'sub_batch_2',
                },
            ]
        }

        companies = self.company | company2
        res = companies.action_eagle_batch_create_sub_businesses()

        self.assertEqual(self.company.eagle_sub_business_id, 'sub_batch_1')
        self.assertEqual(company2.eagle_sub_business_id, 'sub_batch_2')
        self.assertEqual(res.get('type'), 'ir.actions.client')
