# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError

class TestPosAutomatedManufacturing(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.user.company_id
        
        cls.product_a = cls.env['product.product'].create({
            'name': 'Test Product A',
            'type': 'consu',
            'is_storable': True,
        })
        
        cls.component = cls.env['product.product'].create({
            'name': 'Test Component',
            'type': 'consu',
            'is_storable': True,
        })
        
        cls.pos_config = cls.env['pos.config'].create({
            'name': 'Test POS Config',
            'company_id': cls.company.id,
        })
        cls.pos_session = cls.env['pos.session'].create({
            'config_id': cls.pos_config.id,
        })

    def test_01_validation_error_no_bom(self):
        """Test that enabling 'To Create MRP Order' without a BoM raises a ValidationError"""
        with self.assertRaises(ValidationError):
            self.product_a.to_create_mrp = True

    def test_02_mrp_order_creation(self):
        """Test MRP order creation from POS order"""
        self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_a.product_tmpl_id.id,
            'product_qty': 1,
            'type': 'normal',
            'bom_line_ids': [(0, 0, {
                'product_id': self.component.id,
                'product_qty': 1,
            })]
        })
        
        self.product_a.to_create_mrp = True
        
        pos_order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'amount_total': 200,
            'amount_tax': 0,
            'amount_paid': 0,
            'amount_return': 0,
            'lines': [(0, 0, {
                'name': "POS Line",
                'product_id': self.product_a.id,
                'qty': 2,
                'price_unit': 100,
                'price_subtotal': 200,
                'price_subtotal_incl': 200,
            })]
        })
        
        pos_order.create_mrp_orders()
        
        mrp_order = self.env['mrp.production'].search([('origin', '=', pos_order.name)])
        self.assertTrue(mrp_order, "MRP Order should be created")
        self.assertEqual(mrp_order.product_id, self.product_a)
        self.assertEqual(mrp_order.product_qty, 2)
        self.assertEqual(mrp_order.state, 'confirmed', "MRP Order should be confirmed")

    def test_03_mrp_order_done(self):
        """Test MRP order created in 'Done' state from POS"""
        self.env['mrp.bom'].create({
            'product_tmpl_id': self.product_a.product_tmpl_id.id,
            'product_qty': 1,
            'type': 'normal',
            'bom_line_ids': [(0, 0, {
                'product_id': self.component.id,
                'product_qty': 1,
            })]
        })
        
        self.product_a.to_create_mrp = True
        self.product_a.create_mrp_done = True
        
        # Add stock for component
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.company.id)], limit=1)
        self.env['stock.quant']._update_available_quantity(self.component, warehouse.lot_stock_id, 10)
        
        pos_order = self.env['pos.order'].create({
            'session_id': self.pos_session.id,
            'amount_total': 100,
            'amount_tax': 0,
            'amount_paid': 0,
            'amount_return': 0,
            'lines': [(0, 0, {
                'name': "POS Line",
                'product_id': self.product_a.id,
                'qty': 1,
                'price_unit': 100,
                'price_subtotal': 100,
                'price_subtotal_incl': 100,
            })]
        })
        
        pos_order.create_mrp_orders()
        
        mrp_order = self.env['mrp.production'].search([('origin', '=', pos_order.name)], order='id desc', limit=1)
        self.assertTrue(mrp_order, "MRP Order should be created")
        self.assertEqual(mrp_order.state, 'done', "MRP Order should be in 'Done' state")
