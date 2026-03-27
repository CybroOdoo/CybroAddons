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
from odoo import models, api, _
from odoo.exceptions import RedirectWarning


class ResCompany(models.Model):
    """Model for inheriting res_company."""
    _inherit = "res.company"

    @api.model_create_multi
    def create(self, vals_list):
        """Ensure fiscal year day does not exceed the maximum valid day for the selected month during record creation."""
        for vals in vals_list:
            if 'fiscalyear_last_month' in vals and 'fiscalyear_last_day' in vals:
                month = vals.get('fiscalyear_last_month')
                day = vals.get('fiscalyear_last_day')
                if month and day:
                    if vals.account_opening_date:
                        year = vals.account_opening_date.year
                    else:
                        year = datetime.now().year
                    max_day = calendar.monthrange(year, int(month))[1]
                    if int(day) > max_day:
                        vals['fiscalyear_last_day'] = max_day
        return super(ResCompany, self).create(vals_list)

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

        return super(ResCompany, self).write(vals)

    def _validate_locks(self, values):
        """Validate the hard lock date by checking for unposted entries and unreconciled bank statement lines."""
        if values.get('hard_lock_date'):
            draft_entries = self.env['account.move'].search([
                ('company_id', 'in', self.ids),
                ('state', '=', 'draft'),
                ('date', '<=', values['hard_lock_date'])])
            if draft_entries:
                error_msg = _('There are still unposted entries in the '
                              'period you want to lock. You should either post '
                              'or delete them.')
                action_error = {
                    'view_mode': 'list',
                    'name': 'Unposted Entries',
                    'res_model': 'account.move',
                    'type': 'ir.actions.act_window',
                    'domain': [('id', 'in', draft_entries.ids)],
                    'search_view_id': [self.env.ref('account.view_account_move_filter').id, 'search'],
                    'views': [[self.env.ref('account.view_move_tree').id, 'list'], [self.env.ref('account.view_move_form').id, 'form']],
                }
                raise RedirectWarning(error_msg, action_error, _('Show unposted entries'))

            unreconciled_statement_lines = self.env['account.bank.statement.line'].search([
                ('company_id', 'in', self.ids),
                ('is_reconciled', '=', False),
                ('date', '<=', values['hard_lock_date']),
                ('move_id.state', 'in', ('draft', 'posted')),
            ])
            if unreconciled_statement_lines:
                error_msg = _("There are still unreconciled bank statement lines in the period you want to lock."
                            "You should either reconcile or delete them.")
                action_error = {
                    'view_mode': 'kanban',
                    'name': 'Unreconciled Transactions',
                    'res_model': 'account.bank.statement.line',
                    'type': 'ir.actions.act_window',
                    'domain': [('id', 'in', unreconciled_statement_lines.ids)],
                    'views': [[self.env.ref(
                        'base_accounting_kit.account_bank_statement_line_view_kanban').id,
                               'kanban']]
                }
                raise RedirectWarning(error_msg, action_error, _('Show Unreconciled Bank Statement Lines'))
