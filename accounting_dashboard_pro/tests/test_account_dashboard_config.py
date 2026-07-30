# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
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
###############################################################################
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
