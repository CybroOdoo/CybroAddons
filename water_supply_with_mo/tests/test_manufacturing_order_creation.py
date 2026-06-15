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
class TestManufacturingOrderCreation(TransactionCase):

    def test_action_creating_mo(self):
        """Test the action_creating_mo method returns correct window action and context."""
        product = self.env['product.product'].create({
            'name': 'Test Water Product',
            'type': 'consu',
        })
        
        # Create a water usage place
        place = self.env['water.usage.places'].create({
            'code': 'UP1',
            'usage_place_name': 'Place 1',
        })
        
        # Create water usage category
        category = self.env['water.usage.categories'].create({
            'code': 'UC1',
            'usage_category_name': 'Category 1',
        })

        # Create water supply method
        method = self.env['water.supply.methods'].create({
            'code': 'M1',
            'supply_name': 'Method 1',
        })
        
        partner = self.env['res.partner'].create({
            'name': 'Test Customer',
        })
        
        request = self.env['water.supply.request'].create({
            'partner_id': partner.id,
            'pickup_date': '2026-06-20',
            'usage_place_id': place.id,
            'usage_categories_ids': [category.id],
            'supply_method_ids': [method.id],
        })

        creation_order = self.env['manufacturing.order.creation'].create({
            'product_id': product.id,
            'quantity': 10,
            'supply_request_id': request.id,
        })

        action = creation_order.action_creating_mo()
        self.assertEqual(action.get('type'), 'ir.actions.act_window')
        self.assertEqual(action.get('res_model'), 'mrp.production')
        self.assertEqual(action.get('view_mode'), 'form')
        
        context = action.get('context', {})
        self.assertEqual(context.get('default_product_id'), product.id)
        self.assertEqual(context.get('default_product_qty'), 10)
        self.assertEqual(context.get('default_supply_id'), request.id)
        self.assertEqual(context.get('default_manufacturing_order_id'), creation_order.id)
