# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Anjali V P(odoo@cybrosys.com)
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
from odoo.tests import TransactionCase

class TestStockWarehouse(TransactionCase):
    def setUp(self):
        super(TestStockWarehouse, self).setUp()
        self.warehouse = self.env['stock.warehouse'].search([], limit=1)

    def test_onchange_restrict_location(self):
        """Test the restrict_location onchange logic"""
        if self.warehouse:
            self.warehouse.restrict_location = True
            self.warehouse._onchange_restrict_location()
            self.warehouse.restrict_location = False
            self.warehouse._onchange_restrict_location()
            self.assertTrue(True)

    def test_action_open_users_view(self):
        """Test the action to open users view"""
        if self.warehouse:
            action = self.warehouse.action_open_users_view()
            self.assertEqual(action.get('type'), 'ir.actions.act_window')
            self.assertEqual(action.get('res_model'), 'res.users')
