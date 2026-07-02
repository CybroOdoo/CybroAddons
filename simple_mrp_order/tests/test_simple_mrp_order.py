# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: ATHUL RAJ B S(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo.tests import common, TransactionCase
from odoo.exceptions import ValidationError

class TestSimpleMRPOrder(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super(TestSimpleMRPOrder, cls).setUpClass()
        
        # Create products
        cls.product_final = cls.env['product.product'].create({
            'name': 'Final Product',
            'is_storable': True,
        })
        cls.component_1 = cls.env['product.product'].create({
            'name': 'Component 1',
            'is_storable': True,
        })
        cls.component_2 = cls.env['product.product'].create({
            'name': 'Component 2',
            'is_storable': True,
        })

        # Create BOM
        cls.bom = cls.env['simple.mrp.bom'].create({
            'product_id': cls.product_final.id,
            'product_qty': 1.0,
            'uom_id': cls.product_final.uom_id.id,
            'line_ids': [
                (0, 0, {
                    'product_id': cls.component_1.id,
                    'product_qty': 2.0,
                    'uom_id': cls.component_1.uom_id.id,
                }),
                (0, 0, {
                    'product_id': cls.component_2.id,
                    'product_qty': 3.0,
                    'uom_id': cls.component_2.uom_id.id,
                })
            ]
        })

        # Get default location
        cls.warehouse = cls.env['stock.warehouse'].search([('company_id', '=', cls.env.company.id)], limit=1)
        cls.location_src = cls.warehouse.lot_stock_id

    def test_00_mrp_order_flow(self):
        """Test the full flow of a simple MRP order: draft -> confirmed -> done"""
        
        # 1. Create MRP Order
        mrp_order = self.env['mrp.order'].create({
            'product_id': self.product_final.id,
            'product_qty': 1.0,
            'bom_id': self.bom.id,
            'uom_id': self.product_final.uom_id.id,
        })
        
        # Trigger onchange to populate lines (simulating UI behavior if needed, 
        # but create() might have handled it if logic is in create)
        # In this module, create() handles stock_line_ids but not line_ids? 
        # Actually onchange_bom_id handles it.
        mrp_order.onchange_bom_id()
        
        self.assertEqual(mrp_order.state, 'draft', "MRP Order should be in draft state")
        self.assertEqual(len(mrp_order.line_ids), 2, "MRP Order should have 2 component lines")
        
        # 2. Try to confirm without stock - should raise ValidationError
        with self.assertRaises(ValidationError):
            mrp_order.action_confirm()
            
        # 3. Add stock for components
        inventory_location = self.env.ref('stock.stock_location_suppliers')
        self.env['stock.quant']._update_available_quantity(self.component_1, self.location_src, 2.0)
        self.env['stock.quant']._update_available_quantity(self.component_2, self.location_src, 3.0)
        
        # 4. Confirm MRP Order
        mrp_order.action_confirm()
        self.assertEqual(mrp_order.state, 'confirmed', "MRP Order should be confirmed")
        
        # 5. Mark as Done
        mrp_order.action_done()
        self.assertEqual(mrp_order.state, 'done', "MRP Order should be done")
        
        # 6. Check stock changes
        # Component stock should be reduced (by 2 and 3 respectively)
        # Final product stock should be increased (by 1)
        self.assertEqual(self.component_1.qty_available, 0.0)
        self.assertEqual(self.component_2.qty_available, 0.0)
        self.assertEqual(self.product_final.qty_available, 1.0)

    def test_01_mrp_order_cancel(self):
        """Test cancelling an MRP order"""
        mrp_order = self.env['mrp.order'].create({
            'product_id': self.product_final.id,
            'product_qty': 1.0,
            'bom_id': self.bom.id,
            'uom_id': self.product_final.uom_id.id,
        })
        mrp_order.action_cancel()
        self.assertEqual(mrp_order.state, 'cancel', "MRP Order should be cancelled")
