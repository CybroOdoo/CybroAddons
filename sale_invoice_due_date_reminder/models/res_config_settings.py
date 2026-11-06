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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    """Settings of the due date reminders of the sale orders and invoices."""
    _inherit = 'res.config.settings'

    reminder_sales = fields.Boolean(
        string='Reminder for Sales',
        help="Email the customers of the sale orders that are not fully "
             "invoiced or paid before the due date of the order.",
        config_parameter='sale_invoice_due_date_reminder.reminder_sale')
    set_date_sales = fields.Integer(
        string='Days Before Order Due Date',
        help="Number of days before the due date of the sale order the "
             "reminder is sent.",
        config_parameter='sale_invoice_due_date_reminder.set_date_sales')
    reminder_invoicing = fields.Boolean(
        string='Reminder for Invoicing',
        help="Email the customers of the unpaid customer invoices before "
             "their due date.",
        config_parameter='sale_invoice_due_date_reminder.reminder_invoicing')
    set_date_invoicing = fields.Integer(
        string='Days Before Invoice Due Date',
        help="Number of days before the due date of the invoice the reminder "
             "is sent.",
        config_parameter='sale_invoice_due_date_reminder.set_date_invoicing')

    @api.constrains('set_date_sales', 'set_date_invoicing')
    def _check_reminder_days(self):
        """The reminders are sent before the due date."""
        if any(settings.set_date_sales < 0 or settings.set_date_invoicing < 0
               for settings in self):
            raise ValidationError(self.env._(
                "The number of days before the due date cannot be negative."))
