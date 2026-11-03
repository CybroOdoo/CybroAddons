# -*- coding: utf-8 -*-
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
import math
from dateutil import relativedelta
from odoo import Command, api, fields, models, _
from odoo.exceptions import ValidationError


class AccountMove(models.Model):
    """ Extending model Invoice model to compute the interest amount for
    overdue invoices based on the chosen payment term configurations."""

    _inherit = "account.move"

    interest_amount = fields.Monetary(string='Interest Amount', readonly=True,
                                      help='The amount of interest accrued.')
    interest_overdue_act = fields.Boolean(related="invoice_payment_term_id"
                                                  ".interest_overdue_act",
                                          help='Flag indicating whether overdue interest is active.')
    interest_calculated_period = fields.Char(string="Interest calculated date",
                                             help='The date when interest was calculated.')
    interest_type = fields.Selection(related="invoice_payment_term_id"
                                             ".interest_type",
                                     help='The type of interest applied.')
    interest_percentage = fields.Float(related="invoice_payment_term_id"
                                               ".interest_percentage",
                                       help='The percentage rate of interest applied.')

    def get_period_time(self, today_date):
        """ Compute period duration based on Interest duration type. """
        self.ensure_one()
        r_obj = relativedelta. \
            relativedelta(today_date, self.invoice_date_due)
        if self.invoice_payment_term_id.interest_type == 'monthly':
            period = (r_obj.years * 12) + r_obj.months
            if r_obj and r_obj.days > 0:
                period = period + 1
        elif self.invoice_payment_term_id.interest_type == 'weekly':
            period = math.ceil(
                (today_date - self.invoice_date_due).days / 7)
        else:
            period = (today_date - self.invoice_date_due).days
        return period

    def _compute_interest(self, raise_error=True):
        """Helper method to compute overdue interest for the invoice records."""
        today_date = fields.Date.today()
        for rec in self:
            if (rec.invoice_date_due
                    and rec.invoice_date_due < today_date
                    and rec.state == 'draft'
                    and rec.move_type == 'out_invoice'
                    and rec.interest_overdue_act
                    and rec.invoice_payment_term_id.interest_percentage > 0):
                period = rec.get_period_time(today_date)
                interest_type = rec.invoice_payment_term_id.interest_type
                if interest_type == 'monthly':
                    suffix = "-m"
                    msg = _('Your payment term is monthly, and you can update it only once in a month.')
                elif interest_type == 'weekly':
                    suffix = "-w"
                    msg = _('Your payment term is weekly, and you can update it only once in a week.')
                else:
                    suffix = "-d"
                    msg = _('Your payment term is daily, and you can update it only once in a day.')

                if rec.interest_calculated_period == str(period) + suffix:
                    if raise_error:
                        raise ValidationError(msg)
                    continue

                rec.interest_calculated_period = str(period) + suffix
                interest_line = rec.invoice_line_ids.filtered(
                    lambda l: l.name == 'Interest Amount for Overdue'
                )
                if interest_line:
                    rec.invoice_line_ids = [Command.delete(interest_line[0].id)]
                rec.interest_amount = (
                    rec.amount_total
                    * rec.invoice_payment_term_id.interest_percentage
                    * period / 100
                )
                vals = {
                    'name': 'Interest Amount for Overdue',
                    'price_unit': rec.interest_amount,
                    'quantity': 1,
                }
                if rec.invoice_payment_term_id.interest_account_id:
                    vals['account_id'] = (
                        rec.invoice_payment_term_id.interest_account_id.id
                    )
                if rec.interest_amount > 0:
                    rec.invoice_line_ids = [Command.create(vals)]
            elif rec.interest_amount > 0:
                rec.action_interest_reset()

    def action_interest_compute(self):
        """ Action for computing Interest amount based on the chosen payment
        term configurations"""
        self._compute_interest(raise_error=True)

    def _get_interest_check(self):
        """ Method for Interest computation via scheduled action """
        records = self.sudo().search([('state', '=', 'draft')])
        records._compute_interest(raise_error=False)

    def action_interest_reset(self):
        """Method for resetting the interest lines and Interest amount in
        Invoice"""
        for rec in self:
            rec.interest_amount = 0
            interest_line = rec.invoice_line_ids.filtered(
                lambda l: l.name == 'Interest Amount for Overdue')
            if interest_line:
                rec.invoice_line_ids = [Command.delete(interest_line[0].id)]
            rec.interest_calculated_period = False

    @api.onchange('invoice_payment_term_id', 'invoice_line_ids',
                  'invoice_date_due')
    def _onchange_invoice_payment_term_id(self):
        """Method for removing interest from Invoice when user changes dependent
            values of interest."""
        for rec in self:
            if rec.move_type == 'out_invoice':
                rec.interest_amount = 0
                interest_line = rec.invoice_line_ids.filtered(
                    lambda l: l.name == 'Interest Amount for Overdue')
                if interest_line:
                    rec.invoice_line_ids = [Command.delete(interest_line[0].id)]
                rec.interest_calculated_period = False
