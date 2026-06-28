# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions(odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################
from odoo.tests import tagged, TransactionCase

@tagged('post_install', '-at_install', 'pos_reference_for_payment')
class TestPosPaymentReference(TransactionCase):

    def setUp(self):
        super(TestPosPaymentReference, self).setUp()
        
        # Setup Company
        self.company = self.env.company
        
        # Setup Product
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'list_price': 100.0,
            'taxes_id': False,
        })
        
        # Setup POS Payment Method
        self.payment_method = self.env['pos.payment.method'].search([
            ('company_id', '=', self.company.id),
            ('journal_id.type', 'in', ['cash', 'bank'])
        ], limit=1)
        
        if not self.payment_method:
            self.cash_journal = self.env['account.journal'].create({
                'name': 'Test Unique Cash',
                'type': 'cash',
                'code': 'TUCH',
                'company_id': self.company.id,
            })
            self.payment_method = self.env['pos.payment.method'].create({
                'name': 'Test Unique Cash Method',
                'journal_id': self.cash_journal.id,
                'company_id': self.company.id,
            })
        
        # Setup POS Config
        self.pos_config = self.env['pos.config'].create({
            'name': 'Test Main Config',
            'payment_method_ids': [(4, self.payment_method.id)],
            'is_add_pos_payment_reference': True,
        })
        
        # Open Session
        self.pos_config.open_ui()
        self.pos_session = self.pos_config.current_session_id

    def test_pos_payment_reference_creation(self):
        """Test that user_payment_reference from UI passes to backend payment records"""
        
        # Create a mock dictionary payload as if sent from the POS UI
        mock_order = {
            'data': {
                'amount_paid': 100.0,
                'amount_return': 0.0,
                'amount_tax': 0.0,
                'amount_total': 100.0,
                'date_order': '2026-05-12 10:00:00',
                'fiscal_position_id': False,
                'lines': [[0, 0, {
                    'discount': 0,
                    'pack_lot_ids': [],
                    'price_unit': 100.0,
                    'product_id': self.product.id,
                    'price_subtotal': 100.0,
                    'price_subtotal_incl': 100.0,
                    'qty': 1,
                    'tax_ids': [(6, 0, [])]
                }]],
                'name': 'Order 00001-001-0001',
                'partner_id': False,
                'session_id': self.pos_session.id,
                'sequence_number': 1,
                'payment_ids': [[0, 0, {
                    'amount': 100.0,
                    'name': '2026-05-12 10:00:00',
                    'payment_method_id': self.payment_method.id,
                    'user_payment_reference': 'TEST_REF_9999',
                }]],
                'uuid': '00001-001-0001',
                'user_id': self.env.user.id,
            },
            'to_invoice': False,
        }

        # Process the mocked UI order payload using Odoo 19 sync_from_ui
        order_sync_results = self.env['pos.order'].sync_from_ui([mock_order['data']])
        created_order_id = order_sync_results['pos.order'][0]['id']
        pos_order = self.env['pos.order'].browse(created_order_id)
        self.assertTrue(pos_order.exists(), "Order should exist in the database")

        # Verify the payment reference was saved properly
        payment_lines = pos_order.payment_ids
        self.assertTrue(payment_lines, "Order should have payment lines")
        for payment in payment_lines:
            self.assertEqual(
                payment.user_payment_reference,
                'TEST_REF_9999',
                "The custom user_payment_reference was not passed through successfully."
            )
