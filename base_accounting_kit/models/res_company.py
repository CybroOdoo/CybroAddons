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
from datetime import datetime
import calendar
from odoo import fields, models, api, _
from odoo.exceptions import RedirectWarning


class ResCompany(models.Model):
    """Model for inheriting res_company."""
    _inherit = "res.company"

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

    def _get_unreconciled_statement_lines_redirect_action(self, unreconciled_statement_lines):
        """Ensure 'views' is explicitly populated to avoid web client TypeError
        and redirect to the custom bank reconciliation widget."""
        action = super()._get_unreconciled_statement_lines_redirect_action(unreconciled_statement_lines)
        kanban_view = self.env.ref(
            'base_accounting_kit.account_bank_statement_line_view_kanban',
            raise_if_not_found=False
        )
        kanban_id = kanban_view.id if kanban_view else False

        if len(unreconciled_statement_lines) == 1:
            action['views'] = [(False, 'form')]
        else:
            action['view_mode'] = 'kanban,list,form'
            action['views'] = [(kanban_id, 'kanban'), (False, 'list'), (False, 'form')]

        return action
