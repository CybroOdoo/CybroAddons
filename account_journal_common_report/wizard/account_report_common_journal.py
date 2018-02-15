# -*- coding: utf-8 -*-

from odoo import fields, models


class AccountJournalReport(models.TransientModel):
    _inherit = "account.common.journal.report"
    _name = "account.journal.report"

    sort_selection = fields.Selection([('date', 'Date'), ('move_name', 'Journal Entry Number'),], 'Entries Sorted by', required=True, default='move_name')

    def _print_report(self, data):
        data = self.pre_print_report(data)
        data['form'].update({'sort_selection': self.sort_selection})
        return self.env.ref('account_journal_common_report.action_report_common_journal').with_context(landscape=True).report_action(self, data=data)
