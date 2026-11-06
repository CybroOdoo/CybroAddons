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
from datetime import timedelta

from odoo import api, fields, models

PARAM = 'sale_invoice_due_date_reminder.'


class SaleOrder(models.Model):
    """Due date of the sale orders and its reminder to the customer."""
    _inherit = 'sale.order'

    due_date_order = fields.Date(
        string="Due Date", copy=False,
        help="The customer is reminded of the order before this date")
    due_reminder_date = fields.Date(
        copy=False, readonly=True,
        help="Due date of the order the customer was last reminded of")

    def _needs_due_reminder(self):
        """Return whether the order is not fully invoiced or paid yet."""
        self.ensure_one()
        if self.invoice_status in ('to invoice', 'upselling'):
            return True
        if self.invoice_status == 'no':
            invoices = self.invoice_ids.filtered(lambda move: move.state == 'posted')
            return not invoices or any(
                invoice.payment_state not in ('paid', 'in_payment', 'reversed')
                for invoice in invoices)
        return False

    @api.model
    def action_send_mail_sale_order(self):
        """Remind the customers of the orders due within the set number of
        days, once per due date (scheduled action)."""
        params = self.env['ir.config_parameter'].sudo()
        if not params.get_bool(PARAM + 'reminder_sale'):
            return
        today = fields.Date.context_today(self)
        days = params.get_int(PARAM + 'set_date_sales')
        orders = self.search([
            ('state', '!=', 'cancel'),
            ('due_date_order', '>=', today),
            ('due_date_order', '<=', today + timedelta(days=days)),
        ]).filtered(lambda order: order.due_reminder_date != order.due_date_order
                    and order._needs_due_reminder())
        template = self.env.ref(
            'sale_invoice_due_date_reminder.sale_order_due_mail_template')
        for order in orders:
            # The email is logged in the chatter of the order
            template.send_mail(order.id)
            order.due_reminder_date = order.due_date_order
