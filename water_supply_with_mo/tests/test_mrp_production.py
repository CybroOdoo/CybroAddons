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
class TestMrpProduction(TransactionCase):

    def test_mrp_production_creation_with_context(self):
        """Test creating an mrp.production record with default_manufacturing_order_id in context."""
        product = self.env['product.product'].create({
            'name': 'Test Water Product',
            'type': 'consu',
        })
        
        bom = self.env['mrp.bom'].create({
            'product_id': product.id,
            'product_tmpl_id': product.product_tmpl_id.id,
            'product_qty': 1.0,
            'type': 'normal',
        })

        creation_order = self.env['manufacturing.order.creation'].create({
            'product_id': product.id,
            'quantity': 10,
        })

        # Create manufacturing order with the context key
        production = self.env['mrp.production'].with_context(
            default_manufacturing_order_id=creation_order.id
        ).create({
            'product_id': product.id,
            'bom_id': bom.id,
            'product_qty': 10,
        })

        # Verify that creation_order was updated correctly by the overridden create method
        self.assertEqual(creation_order.mrp_id, production)
        self.assertEqual(creation_order.bom_id, bom)
        self.assertFalse(creation_order.is_mo)
