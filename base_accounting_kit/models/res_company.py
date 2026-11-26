# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from datetime import datetime, timedelta
import calendar
import logging
from odoo import fields, models, api
from odoo.exceptions import RedirectWarning

_logger = logging.getLogger(__name__)


class ResCompany(models.Model):
    """Model for inheriting res_company."""
    _inherit = "res.company"

    kit_auto_reconcile_import = fields.Boolean(
        string='Reconcile Imported Statements Automatically',
        help="After a bank statement import, reconcile the new transactions "
             "that have a single sure match (partner and amount, or the "
             "entry number in the label, or an automatic reconcile model).")
    kit_retained_earnings_account_id = fields.Many2one(
        'account.account', string='Retained Earnings Account',
        help="Equity account receiving the result of a closed fiscal year "
             "(last one used in Year-end Closing).")
    fx_reval_journal_id = fields.Many2one(
        'account.journal', string='FX Revaluation Journal',
        domain="[('type', '=', 'general'), ('company_id', '=', id)]",
        help="Journal used for foreign-currency revaluation entries.")
    fx_reval_gain_account_id = fields.Many2one(
        'account.account', string='Unrealized FX Gain Account',
        help="Account crediting the unrealized foreign-exchange gains.")
    fx_reval_loss_account_id = fields.Many2one(
        'account.account', string='Unrealized FX Loss Account',
        help="Account debiting the unrealized foreign-exchange losses.")

    @api.model_create_multi
    def create(self, vals_list):
        """Ensure fiscal year day does not exceed the maximum valid day for the selected month during record creation."""
        for vals in vals_list:
            if 'fiscalyear_last_month' in vals and 'fiscalyear_last_day' in vals:
                month = vals.get('fiscalyear_last_month')
                day = vals.get('fiscalyear_last_day')
                if month and day:
                    opening_date = vals.get('account_opening_date')
                    if opening_date:
                        year = fields.Date.to_date(opening_date).year
                    else:
                        year = datetime.now().year
                    max_day = calendar.monthrange(year, int(month))[1]
                    if int(day) > max_day:
                        vals['fiscalyear_last_day'] = max_day
        return super().create(vals_list)

    def write(self, vals):
        """Auto-correct fiscal year day to a valid value when month or day is updated to prevent invalid calendar dates."""
        if 'fiscalyear_last_month' in vals or 'fiscalyear_last_day' in vals:
            month = vals.get('fiscalyear_last_month')
            day = vals.get('fiscalyear_last_day')
            if month:
                if self.account_opening_date:
                    year = self.account_opening_date.year
                else:
                    year = datetime.now().year
                max_day = calendar.monthrange(year, int(month))[1]
                if not day:
                    if any(company.fiscalyear_last_day > max_day for company in self):
                        vals['fiscalyear_last_day'] = max_day
                elif int(day) > max_day:
                    vals['fiscalyear_last_day'] = max_day

        return super().write(vals)

    def compute_fiscalyear_dates(self, current_date):
        """Fiscal year of a date: the kit Fiscal Year record covering it
        (P2.3-b), else the company setting, trimmed so it does not overlap
        a record."""
        res = super().compute_fiscalyear_dates(current_date)
        current = fields.Date.to_date(current_date)
        if not current:
            return res
        years = self.env['kit.fiscal.year'].sudo().search([
            ('company_id', '=', self.root_id.id),
            ('date_from', '<=', res['date_to']),
            ('date_to', '>=', res['date_from'])])
        date_from, date_to = res['date_from'], res['date_to']
        for year in years:
            if year.date_from <= current <= year.date_to:
                return {'date_from': year.date_from, 'date_to': year.date_to}
            if year.date_to < current:
                date_from = max(date_from, year.date_to + timedelta(days=1))
            else:
                date_to = min(date_to, year.date_from - timedelta(days=1))
        return {'date_from': date_from, 'date_to': date_to}

    def _get_unreconciled_statement_lines_redirect_action(self, unreconciled_statement_lines):
        """Open the kit's reconciliation screen on the journal of the
        transactions still to reconcile (e.g. when setting a lock date)."""
        action = self.env['ir.actions.actions']._for_xml_id(
            'base_accounting_kit.action_kit_bank_reconciliation')
        action['params'] = {'journal_id': unreconciled_statement_lines[:1].journal_id.id}
        return action
