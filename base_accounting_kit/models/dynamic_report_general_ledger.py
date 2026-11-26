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
from odoo import _, models


class DynamicGeneralLedger(models.AbstractModel):
    """General Ledger: the account rows of the dynamic Trial Balance
    (``_get_accounts``) shown as Debit / Credit / Balance, and the journal
    items of an account (``_get_account_move_entry``) loaded when it is
    unfolded. No computation of its own."""
    _name = 'account.dynamic.report.general_ledger'
    _inherit = 'account.dynamic.report.trial_balance'
    _description = 'General Ledger'

    _filters = ('date', 'comparison', 'target_move', 'journals', 'partners',
                'analytic', 'accounts')
    _columns_by = False

    def _report_title(self):
        return _("General Ledger")

    def _option_defs(self):
        return super()._option_defs() + [
            {'key': 'initial_balance', 'label': _("Include Initial Balances"),
             'type': 'bool', 'default': True},
            {'key': 'sortby', 'label': _("Sort by"), 'type': 'select',
             'default': 'sort_date',
             'values': {'sort_date': _("Date"),
                        'sort_journal_partner': _("Journal & Partner")}}]

    def _columns(self, options):
        periods = self._comparison_periods(self.env.company, options)
        return [{'name': _("Debit"), 'type': 'monetary'},
                {'name': _("Credit"), 'type': 'monetary'},
                {'name': _("Balance"), 'type': 'monetary'}] + [
            {'name': label, 'type': 'monetary'}
            for _from, _to, label in periods]

    def _lines(self, options):
        n_periods = options['comparison']['periods']
        lines = super()._lines(options)
        for line in lines:
            col = line['columns']
            balance = col[3] if options['initial_balance'] \
                else col[1] - col[2]
            line['columns'] = [col[1], col[2], balance] + (
                col[5:5 + n_periods] if n_periods else [])
        return lines

    def _child_lines(self, options, line_id):
        blanks = [''] * options['comparison']['periods']
        return [{'id': item['id'], 'name': item['name'], 'level': 1,
                 'parent_id': line_id,
                 'columns': [item['debit'], item['credit'],
                             item['balance']] + blanks}
                for item in self._ledger_items(
                    options, line_id, options['initial_balance'],
                    options['sortby'])]
