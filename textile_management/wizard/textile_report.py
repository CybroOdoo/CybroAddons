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
from datetime import UTC, datetime, time

from odoo import api, fields, models
from odoo.tools.misc import format_amount, format_date


class TextileReport(models.TransientModel):
    """Wizard printing the textile orders of a customer or a vendor."""
    _name = 'textile.report'
    _description = 'Textile Report'

    type = fields.Selection(
        [('customer', 'Customer'), ('vendor', 'Vendor')],
        default='customer', help="Type of Textile Report")
    customer_id = fields.Many2one(
        'res.partner', help="Customer whose textile orders are printed")
    vendor_id = fields.Many2one(
        'res.partner', help="Vendor whose textile orders are printed")
    date_begin = fields.Date(string='From Date', help="First day of the period")
    date_end = fields.Date(string='To Date', help="Last day of the period")
    textile_customer_ids = fields.Many2many(
        'res.partner', compute='_compute_textile_partners')
    textile_vendor_ids = fields.Many2many(
        'res.partner', compute='_compute_textile_partners')

    @api.depends('type')
    def _compute_textile_partners(self):
        """Partners having textile sale or purchase orders, to choose from,
        among the orders the user can read."""
        customers = vendors = self.env['res.partner']
        if self.env['sale.order'].has_access('read'):
            customers = self.env['sale.order'].search(
                [('is_textile_sale_order', '=', True)]).partner_id
        if self.env['purchase.order'].has_access('read'):
            vendors = self.env['purchase.order'].search(
                [('is_textile_purchase_order', '=', True)]).partner_id
        for report in self:
            report.textile_customer_ids = customers
            report.textile_vendor_ids = vendors

    def _day_start(self, date):
        """Start of ``date`` in the timezone of the user, in UTC as the order
        dates are stored, so the period matches the dates the report shows."""
        start = datetime.combine(date, time.min, self.env.tz)
        return start.astimezone(UTC).replace(tzinfo=None)

    def _get_order_lines(self, orders, name_key):
        """Report lines of ``orders``, with the status label and the amount
        in the currency of each order."""
        states = dict(orders._fields['state']._description_selection(self.env))
        return [{
            name_key: order.name,
            'create_date': format_date(self.env, order.date_order),
            'amount': format_amount(self.env, order.amount_total,
                                    order.currency_id),
            'status': states.get(order.state, order.state),
        } for order in orders]

    def action_customer_vendor_report(self):
        """Print the textile orders of the customer or vendor, optionally
        within the period."""
        self.ensure_one()
        domain = []
        if self.date_begin:
            domain.append(('date_order', '>=',
                           self._day_start(self.date_begin)))
        if self.date_end:
            domain.append(('date_order', '<', self._day_start(
                fields.Date.add(self.date_end, days=1))))
        customer_details, vendor_details = [], []
        if self.type == 'customer' and self.customer_id:
            orders = self.env['sale.order'].search(domain + [
                ('partner_id', '=', self.customer_id.id),
                ('is_textile_sale_order', '=', True),
            ], order='date_order')
            customer_details = self._get_order_lines(orders, 'sale')
        elif self.type == 'vendor' and self.vendor_id:
            orders = self.env['purchase.order'].search(domain + [
                ('partner_id', '=', self.vendor_id.id),
                ('is_textile_purchase_order', '=', True),
            ], order='date_order')
            vendor_details = self._get_order_lines(orders, 'purchase')
        data = {
            'type': self.type,
            'customer': self.customer_id.name,
            'vendor': self.vendor_id.name,
            'date_begin': format_date(self.env, self.date_begin)
            if self.date_begin else False,
            'date_end': format_date(self.env, self.date_end)
            if self.date_end else False,
            'customer_details': customer_details,
            'vendor_details': vendor_details,
        }
        return self.env.ref(
            'textile_management.action_textile_report').report_action(
            None, data=data)
