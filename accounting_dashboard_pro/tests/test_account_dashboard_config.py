# -*- coding: utf-8 -*-
######################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author:  Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the Software
#    or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#    DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
#    ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
#    DEALINGS IN THE SOFTWARE.
#
########################################################################################
import psycopg2
from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAccountDashboardConfig(TransactionCase):
    """
    Test suite for the account.dashboard.config model.
    Validates the creation, retrieval, and modification of dashboard configurations.
    """

    @classmethod
    def setUpClass(cls):
        """
        Set up common test data and environment for the test suite.
        Initializes the model references, user, and company.
        """
        super().setUpClass()
        cls.config_model = cls.env['account.dashboard.config']
        cls.user = cls.env.user
        cls.company = cls.env.company

    def test_get_or_create_config_new(self):
        """Test if config is created when it does not exist."""
        # Ensure no config exists for current user
        existing_config = self.config_model.search([('user_id', '=', self.user.id)])
        existing_config.unlink()

        config_data = self.config_model.get_or_create_config()
        self.assertTrue(config_data.get('id'), "Config should have an ID.")
        self.assertEqual(config_data.get('theme'), 'dark', "Default theme should be 'dark'.")
        self.assertEqual(config_data.get('default_period'), 'this_month', "Default period should be 'this_month'.")

    def test_get_or_create_config_existing(self):
        """Test if existing config is returned."""
        # Ensure config exists for current user
        existing_config = self.config_model.search([('user_id', '=', self.user.id)])
        if not existing_config:
            self.config_model.create({'user_id': self.user.id, 'theme': 'light'})
        else:
            existing_config.write({'theme': 'light'})

        config_data = self.config_model.get_or_create_config()
        self.assertEqual(config_data.get('theme'), 'light', "Should return existing config theme.")

    def test_save_config(self):
        """Test saving configuration updates correctly."""
        # Ensure config exists
        self.config_model.get_or_create_config()
        
        config = self.config_model.search([('user_id', '=', self.user.id)], limit=1)
        self.assertEqual(config.theme, 'dark' if config.theme == 'dark' else 'light') # might be anything from previous

        vals = {
            'theme': 'light',
            'amount_format': 'K',
            'company_ids': [self.company.id],
        }
        config.save_config(vals)

        # Re-fetch config to check
        config.invalidate_recordset()
        self.assertEqual(config.theme, 'light', "Theme should be updated to light.")
        self.assertEqual(config.amount_format, 'K', "Amount format should be updated to K.")
        self.assertIn(self.company.id, config.company_ids.ids, "Company ID should be updated.")

    def test_user_uniq_constraint(self):
        """Test that user_id must be unique."""
        
        # Create first config
        self.config_model.search([('user_id', '=', self.user.id)]).unlink()
        self.config_model.create({'user_id': self.user.id})

        # Creating a second one should raise an error
        with self.assertRaises(psycopg2.IntegrityError):
            with self.env.cr.savepoint():
                self.config_model.create({'user_id': self.user.id})
