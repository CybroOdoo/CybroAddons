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
#############################################################################
from odoo import fields
from odoo.tests import TransactionCase, tagged
from odoo.tools.misc import format_amount


@tagged('post_install', '-at_install')
class TestTextileReport(TransactionCase):
    """Test the textile customer and vendor report."""

    @classmethod
    def setUpClass(cls):
        """Create textile and other orders for a customer and a vendor."""
        super().setUpClass()
        cls.partner = cls.env['res.partner'].create({'name': 'Weaver'})
        cls.product = cls.env['product.product'].create({
            'name': 'Cotton Fabric', 'is_textile_product': True})
        order_line = {'product_id': cls.product.id, 'product_qty': 1,
                      'product_uom_qty': 1, 'price_unit': 100}
        cls.sale_orders = cls.env['sale.order'].create([{
            'partner_id': cls.partner.id,
            'is_textile_sale_order': textile,
            'date_order': date,
            'order_line': [fields.Command.create({
                key: order_line[key]
                for key in ('product_id', 'product_uom_qty', 'price_unit')})],
        } for textile, date in [(True, '2026-01-10'), (True, '2026-03-10'),
                                (False, '2026-01-15')]])
        cls.purchase_orders = cls.env['purchase.order'].create([{
            'partner_id': cls.partner.id,
            'is_textile_purchase_order': True,
            'date_order': '2026-02-10',
            'state': state,
        } for state in ('draft', 'to approve')])

    def _report_data(self, **values):
        """Run the wizard and return the data sent to the report."""
        # Skip the document layout configurator shown before the first print
        wizard = self.env['textile.report'].with_context(
            discard_logo_check=True).create(values)
        return wizard.action_customer_vendor_report()['data']

    def test_01_customer_report(self):
        """Only the textile sale orders of the customer are listed, with
        their status label and amount in currency."""
        data = self._report_data(type='customer', customer_id=self.partner.id)
        self.assertEqual([line['sale'] for line in data['customer_details']],
                         self.sale_orders[:2].mapped('name'))
        self.assertEqual(data['customer_details'][0]['status'], 'Quotation')
        order = self.sale_orders[0]
        self.assertEqual(data['customer_details'][0]['amount'],
                         format_amount(self.env, order.amount_total,
                                       order.currency_id))
        self.assertIn(order.currency_id.symbol,
                      data['customer_details'][0]['amount'])
        self.assertFalse(data['vendor_details'])

    def test_02_period(self):
        """The period filters the orders, also with only one date set."""
        data = self._report_data(type='customer', customer_id=self.partner.id,
                                 date_begin='2026-02-01')
        self.assertEqual([line['sale'] for line in data['customer_details']],
                         [self.sale_orders[1].name])
        data = self._report_data(type='customer', customer_id=self.partner.id,
                                 date_end='2026-01-10')
        self.assertEqual([line['sale'] for line in data['customer_details']],
                         [self.sale_orders[0].name])

    def test_05_period_in_user_timezone(self):
        """The period uses the days of the user: 20:00 UTC on 31 October is
        already 1 November in Kolkata."""
        self.env.user.tz = 'Asia/Kolkata'
        order = self.sale_orders[0]
        order.date_order = '2026-10-31 20:00:00'
        for day, expected in (('2026-10-31', []), ('2026-11-01', [order.name])):
            data = self._report_data(type='customer',
                                     customer_id=self.partner.id,
                                     date_begin=day, date_end=day)
            self.assertEqual(
                [line['sale'] for line in data['customer_details']], expected)
        self.assertIn('11/01/2026', data['customer_details'][0]['create_date'])

    def test_03_vendor_report(self):
        """Vendor reports list textile purchase orders in any state,
        including those waiting for approval."""
        data = self._report_data(type='vendor', vendor_id=self.partner.id)
        self.assertEqual(sorted(line['status']
                                for line in data['vendor_details']),
                         ['RFQ', 'To Approve'])
        self.assertFalse(data['customer_details'])

    def test_04_report_renders(self):
        """The PDF report renders from the wizard data."""
        data = self._report_data(type='vendor', vendor_id=self.partner.id)
        html = self.env['ir.actions.report']._render_qweb_html(
            'textile_management.report_textile_report', None, data=data)[0]
        self.assertIn(b'To Approve', html)
        self.assertIn(b'Weaver', html)
