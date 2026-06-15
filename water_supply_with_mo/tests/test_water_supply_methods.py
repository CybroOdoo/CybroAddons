# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
##############################################################################
from odoo.tests.common import TransactionCase
from odoo.tests import tagged


@tagged('post_install', '-at_install', 'water_supply_with_mo')
class TestWaterSupplyMethods(TransactionCase):

    def test_create_water_supply_method(self):
        """Test creating a water supply method and verifying automatic product creation."""
        method = self.env['water.supply.methods'].create({
            'code': 'WSM01',
            'supply_name': 'Test Supply Method',
        })
        self.assertEqual(method.code, 'WSM01')
        self.assertEqual(method.supply_name, 'Test Supply Method')
        self.assertTrue(method.created_product_id)

        product = method.created_product_id
        self.assertEqual(product.name, 'Test Supply Method')
        self.assertEqual(product.type, 'consu')
        self.assertTrue(product.is_storable)
