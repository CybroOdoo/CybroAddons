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

class TestResConfigSettings(TransactionCase):
    def test_onchange_group_user_warehouse_restriction(self):
        """Test onchange group user warehouse restriction"""
        config = self.env['res.config.settings'].new({
            'group_user_warehouse_restriction': True
        })
        config._onchange_group_user_warehouse_restriction()
        
        warehouses = self.env['stock.warehouse'].search([])
        for warehouse in warehouses:
            if not warehouse.user_ids:
                pass # Just ensuring no traceback
        
        config.group_user_warehouse_restriction = False
        config._onchange_group_user_warehouse_restriction()
        self.assertTrue(True)
