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
from odoo import _, api, models
from odoo.exceptions import UserError


class ReportJournalEntry(models.AbstractModel):
    """Journal Entry PDF: journal entries only (invoices and bills have
    their own documents)."""
    _name = 'report.base_accounting_kit.report_journal_entry'
    _description = 'Journal Entry Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        moves = self.env['account.move'].browse(docids)
        if any(move.move_type != 'entry' for move in moves):
            raise UserError(_("Only journal entries can be printed with this "
                              "report. Use the invoice PDF for invoices and "
                              "bills."))
        return {
            'doc_ids': moves.ids,
            'doc_model': 'account.move',
            'docs': moves,
        }
