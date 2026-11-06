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


class AccountMove(models.Model):
    """Reminder of the due date of the customer invoices."""
    _inherit = 'account.move'

    due_reminder_date = fields.Date(
        copy=False, readonly=True,
        help="Due date of the invoice the customer was last reminded of")

    @api.model
    def action_send_mail_invoice(self):
        """Remind the customers of the unpaid invoices due within the set
        number of days, once per due date (scheduled action)."""
        params = self.env['ir.config_parameter'].sudo()
        if not params.get_bool(PARAM + 'reminder_invoicing'):
            return
        today = fields.Date.context_today(self)
        days = params.get_int(PARAM + 'set_date_invoicing')
        invoices = self.search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'not in', ('paid', 'in_payment', 'reversed')),
            ('invoice_date_due', '>=', today),
            ('invoice_date_due', '<=', today + timedelta(days=days)),
        ]).filtered(lambda move: move.due_reminder_date != move.invoice_date_due)
        template = self.env.ref(
            'sale_invoice_due_date_reminder.invoice_due_mail_template')
        for invoice in invoices:
            # The email is logged in the chatter of the invoice
            template.send_mail(invoice.id)
            invoice.due_reminder_date = invoice.invoice_date_due
