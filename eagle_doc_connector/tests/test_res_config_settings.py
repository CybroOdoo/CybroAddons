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
from unittest.mock import patch
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestResConfigSettings(TransactionCase):
    """Test suite for Eagle Doc res.config.settings behavior."""

    def setUp(self):
        super().setUp()
        self.company = self.env.company

    def test_01_config_parameters_saving(self):
        """Verify saving and retrieving API key and Base URL in system parameters."""
        config = self.env['res.config.settings'].create({
            'eagle_doc_api_key': 'key_test_123',
            'eagle_doc_base_url': 'https://custom-url.eagle-doc.com',
        })
        config.execute()

        get_param = self.env['ir.config_parameter'].sudo().get_param
        self.assertEqual(get_param('eagle_doc.api_key'), 'key_test_123')
        self.assertEqual(get_param('eagle_doc.base_url'), 'https://custom-url.eagle-doc.com')

    def test_02_related_company_auto_creation_flags(self):
        """Verify related company auto-creation fields updated via settings."""
        config = self.env['res.config.settings'].create({
            'is_eagle_doc_auto_create_partner': True,
            'is_eagle_doc_auto_create_product': True,
            'is_eagle_doc_auto_create_tax': True,
        })
        config.execute()

        self.assertTrue(self.company.is_eagle_doc_auto_create_partner)
        self.assertTrue(self.company.is_eagle_doc_auto_create_product)
        self.assertTrue(self.company.is_eagle_doc_auto_create_tax)

    @patch('odoo.addons.eagle_doc_connector.wizard.eagle_doc_usage_wizard.EagleDocUsageWizard._open_usage_wizard')
    def test_03_action_eagle_doc_check_usage(self, mock_open_usage):
        """Verify action_eagle_doc_check_usage calls _open_usage_wizard."""
        mock_open_usage.return_value = {
            'type': 'ir.actions.act_window',
            'res_model': 'eagle.doc.usage.wizard',
        }
        config = self.env['res.config.settings'].create({})
        action = config.action_eagle_doc_check_usage()
        self.assertEqual(action.get('res_model'), 'eagle.doc.usage.wizard')
