# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#     Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class AccountPaymentTermLine(models.Model):
    """Inherits the AccountPaymentTermLine class for adding fields"""
    _inherit = "account.payment.term.line"

    value = fields.Selection([
        ('balance', 'Balance'),
        ('percent', 'Percent'),
        ('fixed', 'Fixed Amount'),
        ('instalment', 'Instalment')
    ], string='Type', required=True, default='Percent',
        help="Select here the kind of valuation related to this payment term line.")
    period_type = fields.Selection([
        ('daily', 'Day(s)'),
        ('weekly', 'Week(s)'),
        ('monthly', 'Month(s)'),
        ('yearly', 'Year(s)'),
    ], string='Period Type', default='monthly',help="Select the instalment type")
    period_count = fields.Integer('Number of instalments', default=1, help="Number of instalment")


class AccountPaymentTerm(models.Model):
    """Inherits the AccountPaymentTerm class for adding fields and  methods"""
    _inherit = "account.payment.term"

    @api.constrains('line_ids')
    def _check_lines(self):
        """Checking the validations of payment term lines"""
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
    def _compute_terms(self, date_ref, currency, company, tax_amount, tax_amount_currency, sign, untaxed_amount, untaxed_amount_currency, cash_rounding=None):
        """Get the distribution of this payment term.
        :param date_ref: The move date to take into account
        :param currency: the move's currency
        :param company: the company issuing the move
        :param tax_amount: the signed tax amount for the move
        :param tax_amount_currency: the signed tax amount for the move in the move's currency
        :param untaxed_amount: the signed untaxed amount for the move
        :param untaxed_amount_currency: the signed untaxed amount for the move in the move's currency
        :param sign: the sign of the move
        :param cash_rounding: the cash rounding that should be applied (or None).
            We assume that the input total in move currency (tax_amount_currency + untaxed_amount_currency) is already cash rounded.
            The cash rounding does not change the totals: Consider the sum of all the computed payment term amounts in move / company currency.
            It is the same as the input total in move / company currency.
        :return (list<tuple<datetime.date,tuple<float,float>>>): the amount in the company's currency and
            the document's currency, respectively for each required payment date
        """
        self.ensure_one()
        company_currency = company.currency_id
        tax_amount_left = tax_amount
        tax_amount_currency_left = tax_amount_currency
        untaxed_amount_left = untaxed_amount
        untaxed_amount_currency_left = untaxed_amount_currency
        total_amount = tax_amount + untaxed_amount
        total_amount_currency = tax_amount_currency + untaxed_amount_currency
        foreign_rounding_amount = 0
        company_rounding_amount = 0
        result = []

        for line in self.line_ids.sorted(lambda line: line.value == 'balance'):
            term_vals = {
                'date': line._get_due_date(date_ref),
                'has_discount': line.discount_percentage,
                'discount_date': None,
                'discount_amount_currency': 0.0,
                'discount_balance': 0.0,
                'discount_percentage': line.discount_percentage,
            }

            if line.value == 'fixed':
                term_vals['company_amount'] = sign * company_currency.round(line.value_amount)
                term_vals['foreign_amount'] = sign * currency.round(line.value_amount)
                company_proportion = tax_amount/untaxed_amount if untaxed_amount else 1
                foreign_proportion = tax_amount_currency/untaxed_amount_currency if untaxed_amount_currency else 1
                line_tax_amount = company_currency.round(line.value_amount * company_proportion) * sign
                line_tax_amount_currency = currency.round(line.value_amount * foreign_proportion) * sign
                line_untaxed_amount = term_vals['company_amount'] - line_tax_amount
                line_untaxed_amount_currency = term_vals['foreign_amount'] - line_tax_amount_currency
                result.append(term_vals)
            elif line.value == 'percent':
                term_vals['company_amount'] = company_currency.round(total_amount * (line.value_amount / 100.0))
                term_vals['foreign_amount'] = currency.round(total_amount_currency * (line.value_amount / 100.0))
                line_tax_amount = company_currency.round(tax_amount * (line.value_amount / 100.0))
                line_tax_amount_currency = currency.round(tax_amount_currency * (line.value_amount / 100.0))
                line_untaxed_amount = term_vals['company_amount'] - line_tax_amount
                line_untaxed_amount_currency = term_vals['foreign_amount'] - line_tax_amount_currency
                result.append(term_vals)
            else:
                line_tax_amount = line_tax_amount_currency = line_untaxed_amount = line_untaxed_amount_currency = 0.0

            # The following values do not account for any potential cash rounding
            tax_amount_left -= line_tax_amount
            tax_amount_currency_left -= line_tax_amount_currency
            untaxed_amount_left -= line_untaxed_amount
            untaxed_amount_currency_left -= line_untaxed_amount_currency

            if cash_rounding and line.value in ['fixed', 'percent']:
                cash_rounding_difference_currency = cash_rounding.compute_difference(currency, term_vals['foreign_amount'])
                if not currency.is_zero(cash_rounding_difference_currency):
                    rate = abs(term_vals['foreign_amount'] / term_vals['company_amount']) if term_vals['company_amount'] else 1.0

                    foreign_rounding_amount += cash_rounding_difference_currency
                    term_vals['foreign_amount'] += cash_rounding_difference_currency

                    company_amount = company_currency.round(term_vals['foreign_amount'] / rate)
                    cash_rounding_difference = company_amount - term_vals['company_amount']
                    if not currency.is_zero(cash_rounding_difference):
                        company_rounding_amount += cash_rounding_difference
                        term_vals['company_amount'] = company_amount

            if line.value == 'balance':
                # The `*_amount_left` variables do not account for cash rounding.
                # Here we remove the total amount added by the cash rounding from the amount left.
                # This way the totals in company and move currency remain unchanged (compared to the input).
                # We assume the foreign total (`tax_amount_currency + untaxed_amount_currency`) is cash rounded.
                # The following right side is the same as subtracting all the (cash rounded) foreign payment term amounts from the foreign total.
                # Thus it is the remaining foreign amount and also cash rounded.
                term_vals['foreign_amount'] = tax_amount_currency_left + untaxed_amount_currency_left - foreign_rounding_amount
                term_vals['company_amount'] = tax_amount_left + untaxed_amount_left - company_rounding_amount

                line_untaxed_amount = untaxed_amount_left
                line_untaxed_amount_currency = untaxed_amount_currency_left
                result.append(term_vals)
            if line.value == 'instalment':
                total_instalment_count = line.period_count

                for count in range(total_instalment_count):
                    # Calculate the due date for each installment
                    if line.period_type == 'daily':
                        line_date = line._get_due_date(date_ref) + relativedelta(days=count)
                    elif line.period_type == 'weekly':
                        line_date = line._get_due_date(date_ref) + relativedelta(weeks=count)
                    elif line.period_type == 'monthly':
                        line_date = line._get_due_date(date_ref) + relativedelta(months=count)
                    elif line.period_type == 'yearly':
                        line_date = line._get_due_date(date_ref) + relativedelta(years=count)
                    else:
                        line_date = line._get_due_date(date_ref)

                    term_vals['date'] = line_date
                    term_vals['company_amount'] = sign * company_currency.round(total_amount / total_instalment_count)
                    term_vals['foreign_amount'] = sign * currency.round(total_amount_currency / total_instalment_count)
                    result.append(term_vals.copy())


            if line.discount_percentage:
                if company.early_pay_discount_computation in ('excluded', 'mixed'):
                    term_vals['discount_balance'] = company_currency.round(term_vals['company_amount'] - line_untaxed_amount * line.discount_percentage / 100.0)
                    term_vals['discount_amount_currency'] = currency.round(term_vals['foreign_amount'] - line_untaxed_amount_currency * line.discount_percentage / 100.0)
                else:
                    term_vals['discount_balance'] = company_currency.round(term_vals['company_amount'] * (1 - (line.discount_percentage / 100.0)))
                    term_vals['discount_amount_currency'] = currency.round(term_vals['foreign_amount'] * (1 - (line.discount_percentage / 100.0)))
                term_vals['discount_date'] = date_ref + relativedelta(days=line.discount_days)

            if cash_rounding and line.discount_percentage:
                cash_rounding_difference_currency = cash_rounding.compute_difference(currency, term_vals['discount_amount_currency'])
                if not currency.is_zero(cash_rounding_difference_currency):
                    rate = abs(term_vals['discount_amount_currency'] / term_vals['discount_balance']) if term_vals['discount_balance'] else 1.0
                    term_vals['discount_amount_currency'] += cash_rounding_difference_currency
                    term_vals['discount_balance'] = company_currency.round(term_vals['discount_amount_currency'] / rate)

                result.append(term_vals)
            amount = sum(entry['company_amount'] for entry in result)
            amount_currency = sum(val['foreign_amount'] for val in result)
            dist = company_currency.round(amount-total_amount)
            value = currency.round(amount_currency - total_amount_currency)
            if dist and value :
                result[0]['company_amount'] -= dist
                result[0]['foreign_amount'] -= value
        return result
