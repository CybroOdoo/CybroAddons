#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#############################################################################
from odoo import Command
from odoo.tests import Form, tagged

from odoo.addons.sale.tests.common import TestSaleCommon


@tagged('post_install', '-at_install')
class TestSaleDiscountTotal(TestSaleCommon):
    """Global discount, discount approval and reports of
    sale_discount_total."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.env.user.group_ids = [Command.link(
            cls.env.ref('sale.group_discount_per_so_line').id)]
        cls.company.write({
            'so_double_validation': 'one_step',
            'so_double_validation_limit': 0.0,
        })

    def _create_order(self, discount_type='percent', discount_rate=0.0,
                      lines=((2, 100.0),)):
        """Create a sale order without taxes and apply its global
        discount."""
        order = self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'discount_type': discount_type,
            'discount_rate': discount_rate,
            'order_line': [Command.create({
                'product_id': self.product_a.id,
                'product_uom_qty': qty,
                'price_unit': price,
                'tax_ids': [Command.clear()],
            }) for qty, price in lines],
        })
        order.button_dummy()
        return order

    def _enable_approval(self, limit):
        """Enable the discount approval with the given limit."""
        self.company.write({
            'so_double_validation': 'two_step',
            'so_double_validation_limit': limit,
        })

    # Sale order discount

    def test_sale_order_percent_discount(self):
        """A percentage discount is applied on every line."""
        order = self._create_order('percent', 10.0, lines=((2, 100.0), (1, 50.0)))
        self.assertEqual(order.order_line.mapped('discount'), [10.0, 10.0])
        self.assertAlmostEqual(order.amount_discount, 25.0)
        self.assertAlmostEqual(order.amount_untaxed, 225.0)
        self.assertAlmostEqual(order.amount_total, 225.0)

    def test_sale_order_amount_discount(self):
        """A fixed amount discount is spread over the lines."""
        order = self._create_order('amount', 50.0, lines=((2, 100.0), (1, 50.0)))
        self.assertAlmostEqual(order.order_line[0].discount, 20.0)
        self.assertAlmostEqual(order.amount_discount, 50.0)
        self.assertAlmostEqual(order.amount_untaxed, 200.0)

    def test_sale_order_amount_discount_zero_total(self):
        """A fixed amount discount on a zero total gives no discount."""
        order = self._create_order('amount', 50.0, lines=((1, 0.0),))
        self.assertEqual(order.order_line.discount, 0.0)
        self.assertEqual(order.amount_discount, 0.0)

    def test_sale_order_discount_onchange(self):
        """Changing the discount in the form updates the lines."""
        order = self._create_order()
        with Form(order) as order_form:
            order_form.discount_type = 'percent'
            order_form.discount_rate = 15.0
        self.assertAlmostEqual(order.order_line.discount, 15.0)
        self.assertAlmostEqual(order.amount_discount, 30.0)

    def test_sale_order_discount_with_taxes(self):
        """Taxes are computed on the discounted amount."""
        order = self._create_order('percent', 10.0)
        order.order_line.tax_ids = self.tax_sale_a
        expected_tax = 180.0 * self.tax_sale_a.amount / 100
        self.assertAlmostEqual(order.amount_untaxed, 180.0)
        self.assertAlmostEqual(order.amount_tax, expected_tax)
        self.assertAlmostEqual(order.amount_total, 180.0 + expected_tax)

    # Discount approval

    def test_confirm_without_approval(self):
        """Orders are confirmed directly when the approval is disabled."""
        order = self._create_order('percent', 50.0)
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    def test_confirm_below_limit(self):
        """Orders below the discount limit are confirmed directly."""
        self._enable_approval(20.0)
        order = self._create_order('percent', 10.0)
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    def test_confirm_above_limit_and_approve(self):
        """Orders above the limit wait for approval, then get confirmed."""
        self._enable_approval(5.0)
        order = self._create_order('percent', 10.0)
        order.action_confirm()
        self.assertEqual(order.state, 'waiting')
        order.action_approve()
        self.assertEqual(order.state, 'sale')

    def test_confirm_several_orders(self):
        """Each order is checked against the limit on its own."""
        self._enable_approval(5.0)
        high = self._create_order('percent', 10.0)
        low = self._create_order('percent', 2.0)
        (high | low).action_confirm()
        self.assertEqual(high.state, 'waiting')
        self.assertEqual(low.state, 'sale')

    def test_confirm_order_without_lines(self):
        """An order without lines does not need approval."""
        self._enable_approval(5.0)
        order = self.env['sale.order'].create({'partner_id': self.partner_a.id})
        order.action_confirm()
        self.assertEqual(order.state, 'sale')

    def test_waiting_state_order(self):
        """'Waiting Approval' comes before 'Sales Order'."""
        states = [key for key, _label in
                  self.env['sale.order']._fields['state'].selection]
        self.assertLess(states.index('waiting'), states.index('sale'))

    def test_confirmation_error_messages(self):
        """Confirmed orders and lines without product are refused."""
        order = self._create_order('percent', 10.0)
        order.action_confirm()
        self.assertTrue(order._confirmation_error_message())
        order = self._create_order()
        self.assertFalse(order._confirmation_error_message())
        order.order_line.product_id = False
        self.assertTrue(order._confirmation_error_message())

    # Invoice discount

    def test_invoice_from_sale_order(self):
        """The discount of the sale order is passed on to the invoice."""
        order = self._create_order('amount', 50.0)
        order.action_confirm()
        invoice = order._create_invoices()
        self.assertEqual(invoice.discount_type, 'amount')
        self.assertEqual(invoice.discount_rate, 50.0)
        self.assertAlmostEqual(invoice.amount_discount, 50.0)
        self.assertAlmostEqual(invoice.amount_untaxed, 150.0)
        invoice.action_post()
        self.assertEqual(invoice.state, 'posted')
        self.assertAlmostEqual(invoice.amount_residual, invoice.amount_total)

    def _create_invoice(self, discount_type, discount_rate, lines):
        """Create a customer invoice without taxes and apply its global
        discount."""
        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.partner_a.id,
            'discount_type': discount_type,
            'discount_rate': discount_rate,
            'invoice_line_ids': [Command.create({
                'product_id': self.product_a.id,
                'quantity': qty,
                'price_unit': price,
                'tax_ids': [Command.clear()],
            }) for qty, price in lines],
        })
        invoice.button_dummy()
        return invoice

    def test_invoice_percent_discount(self):
        """A percentage discount is applied on every invoice line."""
        invoice = self._create_invoice('percent', 10.0, ((2, 100.0), (1, 50.0)))
        self.assertEqual(invoice.invoice_line_ids.mapped('discount'), [10.0, 10.0])
        self.assertAlmostEqual(invoice.amount_discount, 25.0)
        self.assertAlmostEqual(invoice.amount_total, 225.0)

    def test_invoice_amount_discount(self):
        """A fixed amount discount is spread over the invoice lines."""
        invoice = self._create_invoice('amount', 30.0, ((3, 100.0),))
        self.assertAlmostEqual(invoice.invoice_line_ids.discount, 10.0)
        self.assertAlmostEqual(invoice.amount_discount, 30.0)
        self.assertAlmostEqual(invoice.amount_total, 270.0)

    def test_invoice_amount_discount_zero_total(self):
        """A fixed amount discount on a zero total gives no discount."""
        invoice = self._create_invoice('amount', 30.0, ((1, 0.0),))
        self.assertEqual(invoice.invoice_line_ids.discount, 0.0)

    def test_invoice_discount_onchange(self):
        """Changing the discount in the invoice form updates the lines."""
        invoice = self._create_invoice('percent', 0.0, ((1, 200.0),))
        with Form(invoice) as invoice_form:
            invoice_form.discount_rate = 25.0
        self.assertAlmostEqual(invoice.invoice_line_ids.discount, 25.0)
        self.assertAlmostEqual(invoice.amount_total, 150.0)

    # Settings, margin and reports

    def test_settings(self):
        """The approval setting is read from and saved on the company."""
        settings = self.env['res.config.settings'].create({
            'so_order_approval': True,
            'so_double_validation_limit': 12.0,
        })
        settings.execute()
        self.assertEqual(self.company.so_double_validation, 'two_step')
        self.assertEqual(self.company.so_double_validation_limit, 12.0)
        self.assertTrue(self.env['res.config.settings'].create({}).so_order_approval)
        self.env['res.config.settings'].create({'so_order_approval': False}).execute()
        self.assertEqual(self.company.so_double_validation, 'one_step')

    def test_margin(self):
        """The margin is only shown when the Sales Margin app is installed."""
        order = self._create_order('percent', 10.0)
        expected = order.margin if 'margin' in order._fields else 0.0
        self.assertEqual(order.margin_test, expected)

    def test_reports(self):
        """The discount is shown in the analysis and the PDF reports."""
        order = self._create_order('percent', 10.0)
        order.action_confirm()
        invoice = order._create_invoices()
        invoice.action_post()
        self.env.flush_all()
        report_lines = self.env['account.invoice.report'].search_read(
            [('move_id', '=', invoice.id)], ['discount'])
        self.assertAlmostEqual(report_lines[0]['discount'], 10.0)
        report = self.env['ir.actions.report']
        order_html = str(report._render_qweb_html(
            'sale.report_saleorder', order.ids)[0])
        invoice_html = str(report._render_qweb_html(
            'account.report_invoice', invoice.ids)[0])
        self.assertIn('Discount', order_html)
        self.assertIn('Discount', invoice_html)
