# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
#    OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
#    THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
##############################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged

@tagged('post_install', '-at_install')
class TestAccountDashboardConfig(TransactionCase):
    """Tests for Account Dashboard Configuration."""

    @classmethod
    def setUpClass(cls):
        """Set up test environment and user."""
        super().setUpClass()
        cls.env = cls.env(context=dict(cls.env.context, tracking_disable=True))
        
        # Create a test user with manager access
        cls.user_manager = cls.env['res.users'].create({
            'name': 'Test Dashboard Manager',
            'login': 'test_config_manager',
            'groups_id': [(6, 0, [cls.env.ref('base.group_user').id, cls.env.ref('account.group_account_manager').id])],
        })

    def test_01_dashboard_config(self):
        """Test the creation and constraint of dashboard config."""
        config_model = self.env['account.dashboard.config']
        
        # Test get_or_create_config
        config_data = config_model.with_user(self.user_manager).get_or_create_config()
        self.assertTrue(config_data.get('id'), "Config should be created and return an ID")
        
        config = config_model.browse(config_data['id'])
        self.assertEqual(config.user_id.id, self.user_manager.id)
        
        # Test save config
        config.with_user(self.user_manager).save_config({'default_period': 'this_year'})
        self.assertEqual(config.default_period, 'this_year')
