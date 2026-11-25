# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo.tests import tagged, TransactionCase


@tagged('post_install', '-at_install', 'pos_reference_for_payment')
class TestPosPaymentReference(TransactionCase):

    def setUp(self):
        super(TestPosPaymentReference, self).setUp()

        self.company = self.env.company

        # Setup Product
        self.product = self.env['product.product'].create({
            'name': 'Test Product',
            'type': 'consu',
            'list_price': 100.0,
            'taxes_id': False,
        })

        # Setup POS Payment Method
        # In Odoo, cash payment methods cannot be assigned to multiple POS configs.
        # We search for or create a bank payment method to avoid this constraint.
        self.payment_method = self.env['pos.payment.method'].search([
            ('company_id', '=', self.company.id),
            ('type', '=', 'bank'),
        ], limit=1)

        if not self.payment_method:
            bank_journal = self.env['account.journal'].search([
                ('company_id', '=', self.company.id),
                ('type', '=', 'bank'),
            ], limit=1)
            if not bank_journal:
                bank_journal = self.env['account.journal'].create({
                    'name': 'Test Bank Journal',
                    'type': 'bank',
                    'code': 'TBNK',
                    'company_id': self.company.id,
                })
            self.payment_method = self.env['pos.payment.method'].create({
                'name': 'Test Bank Payment Method',
                'journal_id': bank_journal.id,
                'type': 'bank',
                'company_id': self.company.id,
            })

        # Setup POS Config
        self.pos_config = self.env['pos.config'].create({
            'name': 'Test POS Reference Config',
            'payment_method_ids': [(4, self.payment_method.id)],
            'is_add_pos_payment_reference': True,
        })

        # Setup and Open POS Session
        self.pos_session = self.env['pos.session'].create({
            'user_id': self.env.uid,
            'config_id': self.pos_config.id,
        })
        self.pos_session.state = 'opened'

    def test_pos_payment_reference_creation(self):
        """Test that user_payment_reference from UI passes to backend payment records"""
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

        order_sync_results = self.env['pos.order'].sync_from_ui([mock_order['data']])
        created_order_id = order_sync_results['pos.order'][0]['id']
        pos_order = self.env['pos.order'].browse(created_order_id)
        self.assertTrue(pos_order.exists(), "Order should exist in the database")

        payment_lines = pos_order.payment_ids
        self.assertTrue(payment_lines, "Order should have payment lines")
        for payment in payment_lines:
            self.assertEqual(
                payment.user_payment_reference,
                'TEST_REF_9999',
                "The custom user_payment_reference was not passed through successfully."
            )

    def test_pos_payment_reference_multiple_payments(self):
        """Test that user_payment_reference is applied across all payment lines on the order"""
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
                    'price_unit': 100.0,
                    'product_id': self.product.id,
                    'price_subtotal': 100.0,
                    'price_subtotal_incl': 100.0,
                    'qty': 1,
                    'tax_ids': [(6, 0, [])]
                }]],
                'name': 'Order 00001-001-0002',
                'partner_id': False,
                'session_id': self.pos_session.id,
                'sequence_number': 2,
                'payment_ids': [
                    [0, 0, {
                        'amount': 60.0,
                        'name': '2026-05-12 10:00:00',
                        'payment_method_id': self.payment_method.id,
                        'user_payment_reference': 'SPLIT_REF_123',
                    }],
                    [0, 0, {
                        'amount': 40.0,
                        'name': '2026-05-12 10:01:00',
                        'payment_method_id': self.payment_method.id,
                    }]
                ],
                'uuid': '00001-001-0002',
                'user_id': self.env.user.id,
            },
            'to_invoice': False,
        }

        order_sync_results = self.env['pos.order'].sync_from_ui([mock_order['data']])
        created_order_id = order_sync_results['pos.order'][0]['id']
        pos_order = self.env['pos.order'].browse(created_order_id)
        self.assertTrue(pos_order.exists())

        payment_lines = pos_order.payment_ids
        self.assertEqual(len(payment_lines), 2, "Order should have two payment lines")
        for payment in payment_lines:
            self.assertEqual(
                payment.user_payment_reference,
                'SPLIT_REF_123',
                "All payment lines should receive the payment reference."
            )

    def test_pos_payment_reference_empty(self):
        """Test order creation when no payment reference is provided"""
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
                    'price_unit': 100.0,
                    'product_id': self.product.id,
                    'price_subtotal': 100.0,
                    'price_subtotal_incl': 100.0,
                    'qty': 1,
                    'tax_ids': [(6, 0, [])]
                }]],
                'name': 'Order 00001-001-0003',
                'partner_id': False,
                'session_id': self.pos_session.id,
                'sequence_number': 3,
                'payment_ids': [[0, 0, {
                    'amount': 100.0,
                    'name': '2026-05-12 10:00:00',
                    'payment_method_id': self.payment_method.id,
                }]],
                'uuid': '00001-001-0003',
                'user_id': self.env.user.id,
            },
            'to_invoice': False,
        }

        order_sync_results = self.env['pos.order'].sync_from_ui([mock_order['data']])
        created_order_id = order_sync_results['pos.order'][0]['id']
        pos_order = self.env['pos.order'].browse(created_order_id)
        self.assertTrue(pos_order.exists())

        payment = pos_order.payment_ids[0]
        self.assertFalse(
            payment.user_payment_reference,
            "Payment reference should be false/empty when not provided."
        )

    def test_pos_data_loading(self):
        """Test that custom fields are included in PoS data loading"""
        config_data = self.env['pos.config']._load_pos_data_read(self.pos_config, self.pos_config)
        self.assertTrue(config_data, "pos.config should return loaded data")
        self.assertIn('is_add_pos_payment_reference', config_data[0])

    def test_res_config_settings_toggle(self):
        """Test toggling the setting via res.config.settings updates pos.config"""
        settings = self.env['res.config.settings'].create({
            'pos_config_id': self.pos_config.id,
            'is_add_pos_payment_reference': False,
        })
        settings.execute()
        self.assertFalse(self.pos_config.is_add_pos_payment_reference)

        settings.is_add_pos_payment_reference = True
        settings.execute()
        self.assertTrue(self.pos_config.is_add_pos_payment_reference)
