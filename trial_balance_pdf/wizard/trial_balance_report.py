# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Chethana Ramachandran(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models

selection_field = {'posted': 'Posted Entries only',
                   'draft': 'Include UnPosted Entries'}


class TrialBalanceReport(models.TransientModel):
    """Create new model"""
    _name = 'trial.balance.report'
    _description = 'trial balance report'

    start_date = fields.Date(string="Start Date",
                             help="Select start date to fetch the trial "
                                  "balance data")
    end_date = fields.Date(string="End Date",
                           help="Select end date to fetch the trial "
                                "balance data")
    journals_ids = fields.Many2many('account.journal', string="Journals",
                                    help="Select the journals to added in the"
                                         "trail balance")
    company_id = fields.Many2one('res.company', string="Company",
                                 help="Select the company of the journals",
                                 default=lambda self: self.env.company)
    state = fields.Selection([
        ('posted', 'Posted Entries only'),
        ('draft', 'Include UnPosted Entries'),
    ], tracking=True, string="State", help="Select the state of journal "
                                           "entries which we want to report")

    def button_to_get_pdf(self):
        """It will create the report using defined query"""
        where_conditions = []
        parameters = []
        state_value = ""
        currency = self.env.user.company_id.currency_id.symbol
        if self.start_date:
            where_conditions.append("account_move_line.date >= %s")
            parameters.append(self.start_date)
        if self.end_date:
            where_conditions.append("account_move_line.date <= %s")
            parameters.append(self.end_date)
        if self.company_id:
            where_conditions.append("account_move_line.company_id = %s")
            parameters.append(str(self.company_id.id))
        if self.state == 'posted':
            where_conditions.append("parent_state = 'posted'")
        if self.state == 'draft':
            where_conditions.append("parent_state in ('posted', 'draft')")
        if self.journals_ids:
            journal_ids = [journal.id for journal in self.journals_ids]
            where_conditions.append("journal_id IN %s")
            parameters.append(tuple(journal_ids))
        where_query = " AND ".join(where_conditions)
        query = """
            SELECT
                account_account.code AS code,
                account_account.name AS ac_name,
                SUM(account_move_line.debit) AS debit,
                SUM(account_move_line.credit) AS credit,
                SUM(account_move_line.debit) - SUM(account_move_line.credit) AS 
                balance
            FROM
                account_move_line
            JOIN
                account_account ON account_account.id = 
                account_move_line.account_id
            {}
            GROUP BY
                account_id,
                account_account.name,
                account_account.code
        """.format("WHERE " + where_query if where_conditions else "")
        self.env.cr.execute(query, tuple(parameters))
        main_query = self.env.cr.dictfetchall()
        total_credit = 0.0
        total_debit = 0.0
        for rec in main_query:
            total_credit += rec['credit']
            total_debit += rec['debit']
        balance = total_debit - total_credit
        if self.state:
            state_value = selection_field[self.state]
        journals = str(self.journals_ids.mapped('name'))
        result = journals[1:-1].replace("'", "")
        data = {
            'query': main_query,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'total_credit': round(total_credit, 2),
            'total_debit': round(total_debit, 2),
            'balance': round(balance),
            'currency': currency,
            'state': state_value,
            'journals_name': result
        }
        return self.env.ref(
            'trial_balance_pdf.action_report_trial_balance').report_action(
            self, data=data)
