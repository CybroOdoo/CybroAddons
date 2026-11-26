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
from odoo import models


class DayBookPdfReport(models.AbstractModel):
    _name = 'report.base_accounting_kit.day_book_report_template'
    _description = 'Day Book Report'

    def _get_day_entries(self, accounts):
        """Return the entries of the period grouped by day, in one query.

        The filters come from ``_query_get`` and the context (dates,
        journals, Target Moves, company); cancelled entries never count.

        :return: list of ``{'date', 'debit', 'credit', 'balance',
            'child_lines'}`` ordered by date, only days with entries.
        """
        if not accounts:
            return []
        tables, where_clause, where_params = self.env[
            'account.move.line']._query_get()
        filters = (' AND ' + where_clause) if where_clause.strip() else ''
        filters = filters.replace('account_move_line__move_id', 'm').replace(
            'account_move_line', 'l')
        sql = ('''
                SELECT l.id AS lid,
                COALESCE(acc.name->>%s, acc.name->>'en_US') AS accname,
                l.account_id AS
                account_id, l.date AS ldate, j.code AS lcode, l.currency_id,
                l.amount_currency, l.ref AS lref, l.name AS lname,
                COALESCE(l.debit,0) AS debit, COALESCE(l.credit,0) AS credit,
                COALESCE(l.debit,0) - COALESCE(l.credit,0) AS balance,
                m.name AS move_name, c.symbol AS currency_code, p.name
                AS partner_name
                FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                JOIN account_journal j ON (l.journal_id=j.id)
                JOIN account_account acc ON (l.account_id = acc.id)
                WHERE l.account_id IN %s''' + filters + '''
                ORDER BY l.date, l.move_id, l.id
        ''')
        self.env.cr.execute(sql, (self.env.lang or 'en_US', tuple(accounts.ids))
                            + tuple(where_params))
        days = {}
        for line in self.env.cr.dictfetchall():
            day = days.setdefault(line['ldate'], {
                'date': line['ldate'], 'debit': 0.0, 'credit': 0.0,
                'balance': 0.0, 'child_lines': []})
            day['debit'] += line['debit']
            day['credit'] += line['credit']
            day['balance'] += line['balance']
            day['child_lines'].append(line)
        return [days[key] for key in sorted(days)]
