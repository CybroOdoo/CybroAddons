# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP(odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import math
from dateutil import relativedelta
from odoo import api, fields, models, _
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

    def action_interest_compute(self):
        """ Action for computing Interest amount based on the chosen payment
        term configurations"""
        today_date = fields.Date.today()
        for rec in self:
            if rec.invoice_date_due \
                    and rec.invoice_date_due < fields.Date.today() \
                    and rec.state == 'draft' \
                    and rec.move_type == 'out_invoice' \
                    and rec.interest_overdue_act \
                    and rec.invoice_payment_term_id.interest_percentage > 0:
                period = rec.get_period_time(today_date)
                if rec.invoice_payment_term_id.interest_type == 'monthly':
                    if rec.interest_calculated_period \
                            and rec.interest_calculated_period == str(period) \
                            + "-m":
                        raise ValidationError(_('Your payment term is '
                                                'monthly, and you can update '
                                                'it only once in a month.'))
                    rec.interest_calculated_period = str(period) + "-m"
                elif rec.invoice_payment_term_id.interest_type == 'weekly':
                    if rec.interest_calculated_period \
                            and rec.interest_calculated_period == str(period) \
                            + "-w":
                        raise ValidationError(_('Your payment term is weekly, '
                                                'and you can update it only '
                                                'once in a week.'))
                    rec.interest_calculated_period = str(period) + "-w"
                else:
                    if rec.interest_calculated_period \
                            and rec.interest_calculated_period == str(period) \
                            + "-d":
                        raise ValidationError(_('Your payment term is daily, '
                                                'and you can update it only '
                                                'once in a day.'))
                    rec.interest_calculated_period = str(period) + "-d"
                interest_line = rec.invoice_line_ids.search(
                    [('name', '=', 'Interest Amount for Overdue'),
                     ('move_id', '=', rec.id)],
                    limit=1)
                if interest_line:
                    rec.invoice_line_ids = ([(2, interest_line.id, 0)])
                rec.interest_amount = rec.amount_total * rec \
                    .invoice_payment_term_id.interest_percentage * period / 100
                vals = {'name': 'Interest Amount for Overdue',
                        'price_unit': rec.interest_amount,
                        'quantity': 1,
                        }
                if rec.invoice_payment_term_id.interest_account_id:
                    vals.update({
                        'account_id': rec.invoice_payment_term_id
                        .interest_account_id.id})
                if rec.interest_amount > 0:
                    rec.invoice_line_ids = ([(0, 0, vals)])
            elif rec.interest_amount > 0:
                rec.action_interest_reset()

    def _get_interest_check(self):
        """ Method for Interest computation via scheduled action """

        today_date = fields.Date.today()
        for rec in self.sudo().search([('state', '=', 'draft')]):
            if rec.invoice_date_due and rec.invoice_date_due < today_date \
                    and rec.state == 'draft' \
                    and rec.move_type == 'out_invoice' \
                    and rec.interest_overdue_act \
                    and rec.invoice_payment_term_id.interest_percentage > 0:
                period = rec.get_period_time(today_date)
                if rec.invoice_payment_term_id.interest_type == 'monthly':
                    if rec.interest_calculated_period \
                            and rec.interest_calculated_period == str(period) \
                            + "-m":
                        continue
                    rec.interest_calculated_period = str(period) + "-m"
                elif rec.invoice_payment_term_id.interest_type == 'weekly':
                    if rec.interest_calculated_period \
                            and rec.interest_calculated_period == str(period) \
                            + "-w":
                        continue
                    rec.interest_calculated_period = str(period) + "-w"
                else:
                    if rec.interest_calculated_period \
                            and rec.interest_calculated_period == str(period) \
                            + "-d":
                        continue
                    rec.interest_calculated_period = str(period) + "-d"
                interest_line = rec.invoice_line_ids.search(
                    [('name', '=', 'Interest Amount for Overdue'),
                     ('move_id', '=', rec.id)], limit=1)
                if interest_line:
                    rec.invoice_line_ids = ([(2, interest_line.id, 0)])
                rec.interest_amount = rec.amount_total * rec \
                    .invoice_payment_term_id.interest_percentage * period / 100
                vals = {'name': 'Interest Amount for Overdue',
                        'price_unit': rec.interest_amount,
                        'quantity': 1,
                        }
                if rec.invoice_payment_term_id.interest_account_id:
                    vals.update({
                        'account_id': rec.invoice_payment_term_id.
                        interest_account_id.id})
                if rec.interest_amount > 0:
                    rec.invoice_line_ids = ([(0, 0, vals)])
            elif rec.interest_amount > 0:
                rec.action_interest_reset()

    def action_interest_reset(self):
        """Method for resetting the interest lines and Interest amount in
        Invoice"""
        self.interest_amount = 0
        interest_line = self.invoice_line_ids.search(
            [('name', '=', 'Interest Amount for Overdue'),
             ('move_id', '=', self.id)], limit=1)
        if interest_line:
            self.invoice_line_ids = ([(2, interest_line.id, 0)])
        self.interest_calculated_period = False

    @api.onchange('invoice_payment_term_id', 'invoice_line_ids',
                  'invoice_date_due')
    def _onchange_invoice_payment_term_id(self):
        """Method for removing interest from Invoice when user changes dependent
            values of interest."""
        for rec in self:
            if rec.move_type == 'out_invoice':
                rec.interest_amount = 0
                interest_line = rec.invoice_line_ids.search(
                    [('name', '=', 'Interest Amount for Overdue')], limit=1)
                if interest_line:
                    rec.invoice_line_ids = ([(2, interest_line.id, 0)])
                rec.interest_calculated_period = False
            return
