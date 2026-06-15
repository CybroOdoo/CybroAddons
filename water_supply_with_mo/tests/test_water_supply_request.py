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
from odoo import fields


@tagged('post_install', '-at_install', 'water_supply_with_mo')
class TestWaterSupplyRequest(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Water Customer',
            'email': 'customer@example.com',
            'phone': '1234567890',
            'street': '123 Water Street',
        })
        cls.place = cls.env['water.usage.places'].create({
            'code': 'UP01',
            'usage_place_name': 'Test Usage Place',
        })
        cls.category = cls.env['water.usage.categories'].create({
            'code': 'UC01',
            'usage_category_name': 'Test Usage Category',
        })
        cls.method = cls.env['water.supply.methods'].create({
            'code': 'WSM01',
            'supply_name': 'Test Supply Method',
        })
        # The creation of 'water.supply.methods' automatically creates a product
        cls.product = cls.method.created_product_id
        
        # Create a BOM for the product so the onchange can find it
        cls.bom = cls.env['mrp.bom'].create({
            'product_id': cls.product.id,
            'product_tmpl_id': cls.product.product_tmpl_id.id,
            'product_qty': 5.0,
            'type': 'normal',
        })

    def test_water_supply_request_creation_and_sequence(self):
        """Test basic creation, sequence generation, and related fields."""
        request = self.env['water.supply.request'].create({
            'partner_id': self.partner.id,
            'pickup_date': '2026-06-20',
            'usage_place_id': self.place.id,
            'usage_categories_ids': [self.category.id],
            'supply_method_ids': [self.method.id],
        })
        # Check sequence generation
        self.assertNotEqual(request.reference_no, 'New')
        
        # Check related partner fields
        self.assertEqual(request.customer_email, 'customer@example.com')
        self.assertEqual(request.customer_phone, '1234567890')
        self.assertEqual(request.customer_address, '123 Water Street')
        self.assertEqual(request.state, 'draft')
        self.assertFalse(request.is_closed)

    def test_onchange_supply_method_ids(self):
        """Test that _onchange_supply_method_ids populates create_mo_ids."""
        request = self.env['water.supply.request'].new({
            'partner_id': self.partner.id,
            'pickup_date': '2026-06-20',
            'usage_place_id': self.place.id,
            'usage_categories_ids': [self.category.id],
            'supply_method_ids': [self.method.id],
        })
        # Trigger the onchange
        request._onchange_supply_method_ids()
        
        # Validate that create_mo_ids has correct values
        self.assertTrue(request.create_mo_ids)
        mo_creation = request.create_mo_ids[0]
        self.assertEqual(mo_creation.product_id, self.product)
        self.assertEqual(mo_creation.quantity, self.bom.product_qty)
        self.assertEqual(mo_creation.uom_id, self.product.uom_id)
        self.assertEqual(mo_creation.bom_id, self.bom)

    def test_action_apply_and_supply(self):
        """Test action_apply (stock moves, state change) and action_supply."""
        # Create a request
        request = self.env['water.supply.request'].create({
            'partner_id': self.partner.id,
            'pickup_date': '2026-06-20',
            'usage_place_id': self.place.id,
            'usage_categories_ids': [self.category.id],
            'supply_method_ids': [self.method.id],
        })

        # Create a mock manufacturing order creation line linked to the request
        mo_creation = self.env['manufacturing.order.creation'].create({
            'product_id': self.product.id,
            'quantity': 10,
            'supply_request_id': request.id,
        })
        
        # Create a mock mrp.production record and link it to the mo_creation
        production = self.env['mrp.production'].create({
            'product_id': self.product.id,
            'bom_id': self.bom.id,
            'product_qty': 10,
        })
        mo_creation.write({'mrp_id': production.id})

        # Trigger action_apply
        request.action_apply()

        # Check state changed to 'created'
        self.assertEqual(request.state, 'created')

        # Check stock moves created
        moves = self.env['stock.move'].search([('supply_id', '=', request.id)])
        self.assertEqual(len(moves), 1)
        self.assertEqual(moves.product_id, self.product)
        self.assertEqual(moves.product_uom_qty, 10.0)
        self.assertEqual(moves.state, 'done')
        
        # Check that manufacturing order was linked to the request
        self.assertEqual(production.supply_id, request)

        # Verify computed fields
        request._compute_mo_count()
        request._compute_stock_move_count()
        self.assertEqual(request.mo_count, 1)
        self.assertEqual(request.stock_move_count, 1)

        # Test action helper window actions
        stock_move_action = request.action_stock_move()
        self.assertEqual(stock_move_action.get('res_model'), 'stock.move')
        self.assertEqual(stock_move_action.get('domain'), [('supply_id', '=', request.id)])

        mrp_action = request.action_mrp_production()
        self.assertEqual(mrp_action.get('res_model'), 'mrp.production')
        self.assertEqual(mrp_action.get('domain'), [('supply_id', '=', request.id)])

        # Trigger action_supply
        request.action_supply()
        self.assertEqual(request.state, 'supplied')
        self.assertTrue(request.is_closed)
