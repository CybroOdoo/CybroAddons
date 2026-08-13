# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Swaraj R (odoo@cybrosys.com)
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
from odoo.exceptions import UserError, ValidationError
from psycopg2 import IntegrityError
from odoo.tools import mute_logger

@tagged('post_install', '-at_install')
class TestPurchaseOrderLine(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({
            'name': 'POL Test Vendor',
            'default_discount': 10.0,
        })
        cls.product = cls.env['product.product'].create({
            'name': 'POL Test Product',
            'type': 'consu',
            'barcode': '1234567890',
        })
        cls.po = cls.env['purchase.order'].create({
            'partner_id': cls.partner.id,
        })

    def test_purchase_order_line_discount_and_onchanges(self):
        """Test PO line barcode scan, discount compute, and locked state restrictions."""
        line = self.env['purchase.order.line'].new({
            'order_id': self.po.id,
        })
        
        # Test barcode scanning onchange
        line.barcode_scan = '1234567890'
        line._onchange_barcode_scan()
        self.assertEqual(line.product_id, self.product)
        
        # Test order_id validation onchange
        self.po.state = 'purchase'
        with self.assertRaises(UserError):
            line._onchange_order_id()
        self.po.state = 'draft'
        
        # Create line to test compute methods
        po_line = self.env['purchase.order.line'].create({
            'order_id': self.po.id,
            'product_id': self.product.id,
            'product_qty': 1,
            'price_unit': 100.0,
            'discount': 10.0,
        })
        self.assertEqual(po_line._get_discounted_price(), 90.0)
        
        # Test invoice line preparation
        invoice_line_vals = po_line._prepare_account_move_line()
        self.assertEqual(invoice_line_vals.get('discount'), 10.0)
        
        # Test default discount computation (when no seller matches)
        po_line._compute_price_unit_and_date_planned_and_name()
        self.assertEqual(po_line.discount, 10.0)

    def test_purchase_order_line_actions_and_dashboard(self):
        """Test action window actions and dashboard category metrics."""
        po_line = self.env['purchase.order.line'].create({
            'order_id': self.po.id,
            'product_id': self.product.id,
            'product_qty': 1,
            'price_unit': 100.0,
        })
        
        action_catalog = po_line.add_catalog_control()
        self.assertEqual(action_catalog['res_model'], 'product.product')
        
        action_po = po_line.action_purchase_order()
        self.assertEqual(action_po['res_id'], self.po.id)
        
        # Test category queries
        categ_analysis = self.env['purchase.order.line'].product_categ_analysis()
        self.assertIn('values', categ_analysis)
        
        categ_data = self.env['purchase.order.line'].product_categ_data(self.product.categ_id.id)
        self.assertIn('count', categ_data)

    def test_discount_sql_constraint(self):
        """Test SQL check constraint on discount field."""
        with mute_logger('odoo.sql_db'):
            try:
                with self.env.cr.savepoint():
                    self.env['purchase.order.line'].create({
                        'order_id': self.po.id,
                        'product_id': self.product.id,
                        'product_qty': 1,
                        'price_unit': 100.0,
                        'discount': 150.0,
                    })
            except (ValidationError, IntegrityError):
                pass
            else:
                self.fail("ValidationError or IntegrityError not raised for discount > 100")
