# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2019-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Tintuk Tomin(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError



class AccountPaymentTermLine(models.Model):
    _inherit = "account.payment.term.line"

    value = fields.Selection([
        ('balance', 'Balance'),
        ('percent', 'Percent'),
        ('fixed', 'Fixed Amount'),
        ('instalment', 'Instalment')
    ], string='Type', required=True, default='balance',
        help="Select here the kind of valuation related to this payment term line.")
    period_type = fields.Selection([
        ('daily', 'Day(s)'),
        ('weekly', 'Week(s)'),
        ('monthly', 'Month(s)'),
        ('yearly', 'Year(s)'),
    ], string='Period Type', default='monthly')
    period_count = fields.Integer('Number of instalments', default=1)


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    @api.constrains('line_ids')
    @api.one
    def _check_lines(self):
        payment_term_lines = self.line_ids.sorted()
        if payment_term_lines and payment_term_lines[-1].value not in ['balance', 'instalment']:
            raise ValidationError(_('A Payment Term should have its last line of type Balance/Instalment.'))
        lines = self.line_ids.filtered(lambda r: r.value == 'balance') or []
        if len(lines) > 1:
            raise ValidationError(_('A Payment Term should have only one line of type Balance.'))
        lines = self.line_ids.filtered(lambda r: r.value == 'instalment') or []
        if len(lines) > 1:
            raise ValidationError(_('A Payment Term should have only one line of type Instalment.'))
        lines = self.line_ids.filtered(lambda r: r.value in ['balance', 'instalment']) or []
        if len(lines) > 1:
            raise ValidationError(_('A Payment Term should have only one of type Balance and Instalment.'))
        lines = self.line_ids.filtered(lambda r: r.value == 'instalment') or []
        for line in lines:
            if line.period_count == 0:
                raise ValidationError(_('A Payment Term of type Instalment should have number of instalments more than 0.'))

    @api.one
    def compute(self, value, date_ref=False):
        date_ref = date_ref or fields.Date.today()
        amount = value
        sign = value < 0 and -1 or 1
        result = []
        if self.env.context.get('currency_id'):
            currency = self.env['res.currency'].browse(self.env.context['currency_id'])
        else:
            currency = self.env.user.company_id.currency_id
        # prec = currency.decimal_places
        for line in self.line_ids:
            if line.value == 'fixed':
                amt = sign * currency.round(line.value_amount)
            elif line.value == 'percent':
                amt = currency.round(value * (line.value_amount / 100.0))
            elif line.value in ['balance', 'instalment']:
                amt = currency.round(amount)
            if line.value != 'instalment' and amt:
                next_date = fields.Date.from_string(date_ref)
                if line.option == 'day_after_invoice_date':
                    next_date += relativedelta(days=line.days)
                elif line.option == 'fix_day_following_month':
                    next_first_date = next_date + relativedelta(day=1, months=1)  # Getting 1st of next month
                    next_date = next_first_date + relativedelta(days=line.days - 1)
                elif line.option == 'last_day_following_month':
                    next_date += relativedelta(day=31, months=1)  # Getting last day of next month
                elif line.option == 'last_day_current_month':
                    next_date += relativedelta(day=31, months=0)  # Getting last day of next month
                result.append((fields.Date.to_string(next_date), amt))
                amount -= amt
            elif line.value == 'instalment' and amt:
                count = line.period_count
                instalment_amount = amt/count
                while count > 0:
                    next_date = fields.Date.from_string(date_ref)
                    if line.period_type == 'daily':
                        next_date += relativedelta(days=count)
                    elif line.period_type == 'weekly':
                        next_date += relativedelta(weeks=count)
                    elif line.period_type == 'monthly':
                        next_date += relativedelta(months=count)
                    else:
                        next_date += relativedelta(years=count)
                    result.append((fields.Date.to_string(next_date), instalment_amount))
                    count -= 1
                amount -= amt
        amount = sum(amt for _, amt in result)
        dist = currency.round(value - amount)
        if dist:
            last_date = result and result[-1][0] or fields.Date.today()
            result.append((last_date, dist))
        return result
