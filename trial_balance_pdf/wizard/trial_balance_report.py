# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE(LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSERGENERAL PUBLIC
#    LICENSE (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models
from odoo.tools import SQL


class TrialBalanceReport(models.TransientModel):
    """ Create new model """
    _name = 'trial.balance.report'
    _description = 'Trial Balance Report'

    start_date = fields.Date(string="Start Date",
                             help="Select start date to fetch the trial "
                                  "balance data")
    end_date = fields.Date(string="End Date",
                           help="Select end date to fetch the trial "
                                "balance data")
    journals_ids = fields.Many2many('account.journal', string="Journals",
                                    help="Select the journals to be added to the trial balance")
    company_id = fields.Many2one('res.company', string="Company",
                                 help="Select the company of the journals",
                                 default=lambda self: self.env.company)
    state = fields.Selection([
        ('posted', 'Posted Entries only'),
        ('draft', 'Include Unposted Entries'),
    ], default='posted', string="State",
       help="Select the state of journal entries which we want to report")

    def button_to_get_pdf(self):
        """ It will create the report using defined query """
        self.env['account.move.line'].flush_model()
        company = self.company_id or self.env.company
        where_conditions = []

        if self.start_date:
            where_conditions.append(SQL("account_move_line.date >= %s", self.start_date))
        if self.end_date:
            where_conditions.append(SQL("account_move_line.date <= %s", self.end_date))
        if company:
            where_conditions.append(SQL("account_move_line.company_id = %s", company.id))
        if self.state == 'posted':
            where_conditions.append(SQL("account_move_line.parent_state = 'posted'"))
        elif self.state == 'draft':
            where_conditions.append(SQL("account_move_line.parent_state IN ('posted', 'draft')"))
        else:
            where_conditions.append(SQL("account_move_line.parent_state != 'cancel'"))
        if self.journals_ids:
            where_conditions.append(SQL("account_move_line.journal_id IN %s", tuple(self.journals_ids.ids)))

        where_clause = SQL("WHERE %s", SQL(" AND ").join(where_conditions)) if where_conditions else SQL()
        query = SQL(
            """
            SELECT
                account_move_line.account_id,
                SUM(account_move_line.debit) AS debit,
                SUM(account_move_line.credit) AS credit,
                SUM(account_move_line.debit) - SUM(account_move_line.credit) AS balance
            FROM
                account_move_line
            %s
            GROUP BY
                account_move_line.account_id
            """,
            where_clause,
        )
        self.env.cr.execute(query)
        main_query = self.env.cr.dictfetchall()

        accounts = self.env['account.account'].with_company(company).browse(
            [row['account_id'] for row in main_query]
        )
        account_map = {acc.id: (acc.code or '', acc.name or '') for acc in accounts}

        final_results = []
        total_credit = 0.0
        total_debit = 0.0
        for row in main_query:
            account_id = row['account_id']
            code, ac_name = account_map.get(account_id, ('', ''))
            debit = float(row['debit'] or 0.0)
            credit = float(row['credit'] or 0.0)
            balance = float(row['balance'] or 0.0)
            total_debit += debit
            total_credit += credit
            final_results.append({
                'code': code,
                'ac_name': ac_name,
                'debit': debit,
                'credit': credit,
                'balance': balance,
            })
        final_results.sort(key=lambda x: x['code'] or '')

        total_balance = total_debit - total_credit
        state_value = dict(
            self._fields['state']._description_selection(self.env)
        ).get(self.state, '') if self.state else ''
        journals = ", ".join(self.journals_ids.mapped('name'))
        data = {
            'query': final_results,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'company_id': company.id,
            'total_credit': total_credit,
            'total_debit': total_debit,
            'balance': total_balance,
            'state': state_value,
            'journals_name': journals,
        }
        return self.env.ref(
            'trial_balance_pdf.action_report_trial_balance').report_action(
            self, data=data)
