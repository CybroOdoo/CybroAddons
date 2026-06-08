# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#    you can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    GENERAL PUBLIC LICENSE (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from odoo.tests.common import TransactionCase
from odoo import fields

class TestPosOrder(TransactionCase):

    def setUp(self):
        super(TestPosOrder, self).setUp()
        self.PosOrder = self.env['pos.order']
        self.payment_method = self.env['pos.payment.method'].create({
            'name': 'Cash',
            'company_id': self.env.company.id,
        })
        self.pos_config = self.env['pos.config'].create({
            'name': 'Test POS',
            'orderline_washing_type': True,
            'payment_method_ids': [(4, self.payment_method.id)],
        })
        # Create a session manually
        self.session = self.env['pos.session'].create({
            'user_id': self.env.uid,
            'config_id': self.pos_config.id,
        })
        self.partner = self.env['res.partner'].create({'name': 'Test Partner'})
        self.product = self.env['product.product'].create({'name': 'Test Product'})
        self.washing_type = self.env['washing.type'].create({
            'name': 'Test Wash',
            'amount': 10,
            'assigned_person_id': self.env.uid
        })

    def test_process_order_and_laundry_creation(self):
        """Test _process_order and _create_laundry_order_from_pos"""
        order_data = {
            'name': 'Order/001',
            'session_id': self.session.id,
            'partner_id': self.partner.id,
            'lines': [[0, 0, {
                'product_id': self.product.id,
                'qty': 1,
                'price_unit': 100,
                'price_subtotal': 100,
                'price_subtotal_incl': 100,
                'washing_type_id': self.washing_type.id,
            }]],
            'pos_reference': 'REF/001',
            'amount_tax': 0,
            'amount_total': 100,
            'amount_paid': 100,
            'amount_return': 0,
            'payment_ids': [[0, 0, {
                'payment_method_id': self.payment_method.id,
                'amount': 100,
                'payment_date': fields.Datetime.now(),
            }]],
        }
        # This will call _process_order which calls _create_laundry_order_from_pos
        self.PosOrder.sync_from_ui([order_data])
        pos_order = self.PosOrder.search([('pos_reference', '=', 'REF/001')], limit=1)
        self.assertTrue(pos_order)
        
        laundry_order = self.env['laundry.order'].search([('pos_order_id', '=', pos_order.id)])
        self.assertTrue(laundry_order, "Laundry order should be created")

    def test_is_laundry_order(self):
        """Test _is_laundry_order"""
        pos_order = self.PosOrder.create({
            'session_id': self.session.id,
            'amount_tax': 0,
            'amount_total': 10,
            'amount_paid': 10,
            'amount_return': 0,
            'lines': [(0, 0, {
                'product_id': self.product.id,
                'qty': 1,
                'price_unit': 10,
                'price_subtotal': 10,
                'price_subtotal_incl': 10,
                'washing_type_id': self.washing_type.id,
            })]
        })
        self.assertTrue(self.PosOrder._is_laundry_order(pos_order))

    def test_prepare_invoice_lines(self):
        """Test _prepare_invoice_lines"""
        pos_order = self.PosOrder.create({
            'session_id': self.session.id,
            'partner_id': self.partner.id,
            'amount_tax': 0,
            'amount_total': 10,
            'amount_paid': 10,
            'amount_return': 0,
            'lines': [(0, 0, {
                'product_id': self.product.id,
                'qty': 1,
                'price_unit': 10,
                'price_subtotal': 10,
                'price_subtotal_incl': 10,
                'washing_type_id': self.washing_type.id,
            })]
        })
        invoice_lines = pos_order._prepare_invoice_lines('out_invoice')
        # Check for washing type note
        has_note = any(l[2].get('display_type') == 'line_note' and l[2].get('name') == self.washing_type.name for l in invoice_lines)
        self.assertTrue(has_note)
