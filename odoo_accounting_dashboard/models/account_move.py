# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
import calendar
from odoo import api, models, fields


class AccountMove(models.Model):
    """Inherited account.move model to retrieve data for the accounting dashboard."""
    _inherit = 'account.move'

    @api.model
    def get_datas(self):
        """Retrieve key financial metrics for dashboard tiles: open invoice count,
        paid invoice count, total income, unreconciled items, and journal list."""
        self.check_access('read')
        company_id = self.env.company.id

        open_invoice = self.search_count([
            ('state', '=', 'draft'),
            ('move_type', 'in', ('out_invoice', 'in_invoice')),
            ('company_id', '=', company_id),
        ])

        paid_invoice = self.search_count([
            ('payment_state', '=', 'paid'),
            ('move_type', 'in', ('out_invoice', 'in_invoice')),
            ('company_id', '=', company_id),
        ])

        self.env.cr.execute("""
            SELECT COALESCE(SUM(aml.debit), 0) AS debit,
                   COALESCE(SUM(aml.credit), 0) AS credit
              FROM account_move_line aml
              JOIN account_account aa ON aa.id = aml.account_id
              JOIN account_move am ON am.id = aml.move_id
             WHERE aa.account_type IN ('income', 'income_other')
               AND am.state = 'posted'
               AND am.company_id = %s
        """, [company_id])
        row = self.env.cr.dictfetchone()
        raw_income = (row['credit'] - row['debit']) if row else 0.0
        income = format(raw_income, ".2f")

        self.env.cr.execute("""
            SELECT COUNT(*) AS cnt
              FROM account_move_line l
              JOIN account_account a ON a.id = l.account_id
              JOIN account_move m ON m.id = l.move_id
             WHERE l.full_reconcile_id IS NULL
               AND l.balance != 0
               AND a.reconcile IS TRUE
               AND m.company_id = %s
        """, [company_id])
        reconcile_count = [self.env.cr.fetchone()[0]]

        journal_list = self.env['account.journal'].search([
            ('company_id', '=', company_id)
        ])
        journal_data = [{
            'id': j.id,
            'name': j.name,
            'type': j.type,
        } for j in journal_list]

        return {
            'open_invoice': open_invoice,
            'paid_invoice': paid_invoice,
            'income': income,
            'currency_symbol': self.env.company.currency_id.symbol,
            'unreconcile_items': reconcile_count,
            'journal_data': journal_data,
        }

    @api.model
    def get_income_chart(self, income):
        """Retrieve income, expense, and profit chart data for current month or year."""
        self.check_access('read')
        company_id = self.env.company.id
        today = fields.Date.today()

        if income == 'income_this_month':
            last_day = calendar.monthrange(today.year, today.month)[1]
            day_list = list(range(1, last_day + 1))

            query_income = """
                SELECT EXTRACT(DAY FROM aml.date)::int AS day,
                       COALESCE(SUM(aml.credit - aml.debit), 0) AS total
                  FROM account_move_line aml
                  JOIN account_account aa ON aa.id = aml.account_id
                  JOIN account_move am ON am.id = aml.move_id
                 WHERE aa.account_type IN ('income', 'income_other')
                   AND am.state = 'posted'
                   AND am.company_id = %s
                   AND EXTRACT(MONTH FROM aml.date) = %s
                   AND EXTRACT(YEAR FROM aml.date) = %s
                 GROUP BY day
            """
            self.env.cr.execute(query_income, [company_id, today.month, today.year])
            income_map = {row['day']: float(row['total']) for row in self.env.cr.dictfetchall()}

            query_expense = """
                SELECT EXTRACT(DAY FROM aml.date)::int AS day,
                       COALESCE(SUM(aml.debit - aml.credit), 0) AS total
                  FROM account_move_line aml
                  JOIN account_account aa ON aa.id = aml.account_id
                  JOIN account_move am ON am.id = aml.move_id
                 WHERE aa.account_type IN ('expense', 'expense_depreciation', 'expense_direct_cost')
                   AND am.state = 'posted'
                   AND am.company_id = %s
                   AND EXTRACT(MONTH FROM aml.date) = %s
                   AND EXTRACT(YEAR FROM aml.date) = %s
                 GROUP BY day
            """
            self.env.cr.execute(query_expense, [company_id, today.month, today.year])
            expense_map = {row['day']: float(row['total']) for row in self.env.cr.dictfetchall()}

            date_res = []
            income_res = []
            expense_res = []
            profit_res = []
            for d in day_list:
                inc = round(income_map.get(d, 0.0), 2)
                exp = round(expense_map.get(d, 0.0), 2)
                date_res.append(d)
                income_res.append(inc)
                expense_res.append(exp)
                profit_res.append(round(inc - exp, 2))

            return {
                'income': income_res,
                'expense': expense_res,
                'date': date_res,
                'profit': profit_res,
            }
        else:
            month_list = list(calendar.month_name)[1:]

            query_income = """
                SELECT EXTRACT(MONTH FROM aml.date)::int AS month_num,
                       COALESCE(SUM(aml.credit - aml.debit), 0) AS total
                  FROM account_move_line aml
                  JOIN account_account aa ON aa.id = aml.account_id
                  JOIN account_move am ON am.id = aml.move_id
                 WHERE aa.account_type IN ('income', 'income_other')
                   AND am.state = 'posted'
                   AND am.company_id = %s
                   AND EXTRACT(YEAR FROM aml.date) = %s
                 GROUP BY month_num
            """
            self.env.cr.execute(query_income, [company_id, today.year])
            income_map = {row['month_num']: float(row['total']) for row in self.env.cr.dictfetchall()}

            query_expense = """
                SELECT EXTRACT(MONTH FROM aml.date)::int AS month_num,
                       COALESCE(SUM(aml.debit - aml.credit), 0) AS total
                  FROM account_move_line aml
                  JOIN account_account aa ON aa.id = aml.account_id
                  JOIN account_move am ON am.id = aml.move_id
                 WHERE aa.account_type IN ('expense', 'expense_depreciation', 'expense_direct_cost')
                   AND am.state = 'posted'
                   AND am.company_id = %s
                   AND EXTRACT(YEAR FROM aml.date) = %s
                 GROUP BY month_num
            """
            self.env.cr.execute(query_expense, [company_id, today.year])
            expense_map = {row['month_num']: float(row['total']) for row in self.env.cr.dictfetchall()}

            date_res = []
            income_res = []
            expense_res = []
            profit_res = []
            for m_idx, m_name in enumerate(month_list, start=1):
                inc = round(income_map.get(m_idx, 0.0), 2)
                exp = round(expense_map.get(m_idx, 0.0), 2)
                date_res.append(m_name)
                income_res.append(inc)
                expense_res.append(exp)
                profit_res.append(round(inc - exp, 2))

            return {
                'income': income_res,
                'expense': expense_res,
                'date': date_res,
                'profit': profit_res,
            }

    @api.model
    def get_payment_data(self, payment_list_filter, payment_data_filter):
        """Retrieve customer and vendor paid invoices scoped to the current company."""
        self.check_access('read')
        today = fields.Date.today()
        company_id = self.env.company.id

        if payment_data_filter == 'this_month':
            last_day = calendar.monthrange(today.year, today.month)[1]
            start_date = f"{today.year}-{today.month:02d}-01"
            end_date = f"{today.year}-{today.month:02d}-{last_day}"
        else:
            start_date = f"{today.year}-01-01"
            end_date = f"{today.year}-12-31"

        move_type = 'out_invoice' if payment_list_filter == 'customer_payment' else 'in_invoice'
        domain = [
            ('move_type', '=', move_type),
            ('payment_state', '=', 'paid'),
            ('state', '=', 'posted'),
            ('company_id', '=', company_id),
            ('invoice_date', '>=', start_date),
            ('invoice_date', '<=', end_date),
        ]

        invoices = self.search(domain)
        return [{
            'id': inv.id,
            'partner': inv.partner_id.name or '',
            'amount': round(inv.amount_total, 2),
            'date': str(inv.invoice_date or ''),
        } for inv in invoices]

    @api.model
    def get_top_datas(self, top_filter):
        """Return top customers and top vendors ranked by total invoiced amount."""
        self.check_access('read')
        today = fields.Date.today()
        company_id = self.env.company.id

        if top_filter == 'this_month':
            last_day = calendar.monthrange(today.year, today.month)[1]
            start_date = f"{today.year}-{today.month:02d}-01"
            end_date = f"{today.year}-{today.month:02d}-{last_day}"
        else:
            start_date = f"{today.year}-01-01"
            end_date = f"{today.year}-12-31"

        date_domain = [
            ('invoice_date', '>=', start_date),
            ('invoice_date', '<=', end_date),
            ('company_id', '=', company_id),
            ('state', '=', 'posted'),
        ]

        vendor_bills = self.search(date_domain + [('move_type', '=', 'in_invoice')])
        customer_invoices = self.search(date_domain + [('move_type', '=', 'out_invoice')])

        vendor_totals = {}
        for bill in vendor_bills:
            pid = bill.partner_id.id
            if pid:
                if pid not in vendor_totals:
                    vendor_totals[pid] = {
                        'id': pid,
                        'name': bill.partner_id.name or '',
                        'amount': 0.0,
                    }
                vendor_totals[pid]['amount'] += bill.amount_total

        top_vendors = sorted(
            vendor_totals.values(), key=lambda v: v['amount'], reverse=True
        )
        for v in top_vendors:
            v['amount'] = round(float(v['amount'] or 0.0), 2)

        customer_totals = {}
        for inv in customer_invoices:
            pid = inv.partner_id.id
            if pid:
                if pid not in customer_totals:
                    customer_totals[pid] = {
                        'id': pid,
                        'name': inv.partner_id.name or '',
                        'amount': 0.0,
                    }
                customer_totals[pid]['amount'] += inv.amount_total

        top_customers = sorted(
            customer_totals.values(), key=lambda c: c['amount'], reverse=True
        )
        for c in top_customers:
            c['amount'] = round(float(c['amount'] or 0.0), 2)

        return {
            'top_vendors': top_vendors,
            'top_customers': top_customers,
        }

    @api.model
    def get_aged_payable(self, aged_filter, aged_payable_filter):
        """Retrieve aged payable or aged receivable data for current month or year."""
        self.check_access('read')
        company_id = self.env.company.id
        today = fields.Date.today()
        move_type = 'out_invoice' if aged_filter == 'aged_receive' else 'in_invoice'

        base_query = """
            SELECT rp.name AS partner_name,
                   am.partner_id AS partner_id,
                   COALESCE(SUM(am.amount_total), 0.0) AS amount
              FROM account_move am
              JOIN res_partner rp ON rp.id = am.partner_id
             WHERE am.move_type = %s
               AND am.payment_state = 'not_paid'
               AND am.state = 'posted'
               AND am.company_id = %s
               AND am.partner_id = rp.commercial_partner_id
        """
        params = [move_type, company_id]

        if aged_payable_filter == 'this_month':
            query = base_query + """
               AND EXTRACT(MONTH FROM am.invoice_date_due) = %s
               AND EXTRACT(YEAR FROM am.invoice_date_due) = %s
             GROUP BY am.partner_id, rp.name
             ORDER BY amount DESC
            """
            params.extend([today.month, today.year])
        else:
            query = base_query + """
               AND EXTRACT(YEAR FROM am.invoice_date_due) = %s
             GROUP BY am.partner_id, rp.name
             ORDER BY amount DESC
            """
            params.append(today.year)

        self.env.cr.execute(query, params)
        records = self.env.cr.dictfetchall()
        partner = [item['partner_name'] for item in records]
        amount = [round(float(item['amount'] or 0.0), 2) for item in records]

        return {
            'partner': partner,
            'amount': amount,
        }

    @api.model
    def get_sale_revenue(self, top_sale_cust_filter):
        """Retrieve top-10 revenue generating customers for the period."""
        self.check_access('read')
        company_id = self.env.company.id
        today = fields.Date.today()

        base_query = """
            SELECT account_move.partner_id                 AS customer_id,
                   MAX(res_partner.name)                   AS customer,
                   SUM(account_move.amount_untaxed_signed) AS total_amount
              FROM account_move
              JOIN res_partner ON res_partner.id = account_move.partner_id
             WHERE account_move.move_type  = 'out_invoice'
               AND account_move.state      = 'posted'
               AND account_move.company_id = %s
        """
        params = [company_id]

        if top_sale_cust_filter == 'this_month':
            query = base_query + """
               AND EXTRACT(MONTH FROM account_move.invoice_date) = %s
               AND EXTRACT(YEAR FROM account_move.invoice_date) = %s
             GROUP BY account_move.partner_id
             ORDER BY total_amount DESC
             LIMIT 10
            """
            params.extend([today.month, today.year])
        else:
            query = base_query + """
               AND EXTRACT(YEAR FROM account_move.invoice_date) = %s
             GROUP BY account_move.partner_id
             ORDER BY total_amount DESC
             LIMIT 10
            """
            params.append(today.year)

        self.env.cr.execute(query, params)
        res = self.env.cr.dictfetchall()
        for r in res:
            r['total_amount'] = round(float(r['total_amount'] or 0.0), 2)
        return res

    @api.model
    def get_bank_balance(self):
        """Retrieve bank and cash account balances for the current company."""
        self.check_access('read')
        company_id = self.env.company.id
        journals = self.env['account.journal'].search([
            ('type', 'in', ['bank', 'cash']),
            ('company_id', '=', company_id),
        ])

        if not journals:
            return []

        self.env.cr.execute("""
            SELECT journal.id AS journal_id,
                   COALESCE(statement.balance_end_real, 0) AS balance_end_real,
                   COALESCE(without_statement.amount, 0)   AS unlinked_amount
              FROM account_journal journal
         LEFT JOIN LATERAL (
                       SELECT first_line_index,
                              balance_end_real
                         FROM account_bank_statement
                        WHERE journal_id = journal.id
                          AND company_id = %s
                          AND first_line_index IS NOT NULL
                     ORDER BY date DESC, id DESC
                        LIMIT 1
                   ) statement ON TRUE
         LEFT JOIN LATERAL (
                       SELECT COALESCE(SUM(stl.amount), 0.0) AS amount
                         FROM account_bank_statement_line stl
                         JOIN account_move move ON move.id = stl.move_id
                        WHERE stl.statement_id IS NULL
                          AND move.state != 'cancel'
                          AND stl.journal_id = journal.id
                          AND stl.company_id = %s
                          AND stl.internal_index >= COALESCE(statement.first_line_index, '')
                   ) without_statement ON TRUE
             WHERE journal.id = ANY(%s)
        """, [company_id, company_id, journals.ids])
        running_balances = {
            row['journal_id']: float(row['balance_end_real']) + float(row['unlinked_amount'])
            for row in self.env.cr.dictfetchall()
        }

        self.env.cr.execute("""
            SELECT move.journal_id AS journal_id,
                   SUM(CASE
                       WHEN payment.payment_type = 'outbound' THEN -payment.amount
                       ELSE payment.amount
                   END) AS amount_total
              FROM account_payment payment
              JOIN account_move move ON move.origin_payment_id = payment.id
              JOIN account_journal journal ON move.journal_id = journal.id
             WHERE payment.is_matched IS TRUE
               AND move.state = 'posted'
               AND payment.journal_id = ANY(%s)
               AND payment.company_id = %s
               AND payment.outstanding_account_id = journal.default_account_id
          GROUP BY move.journal_id
        """, [journals.ids, company_id])
        direct_balances = {
            row['journal_id']: float(row['amount_total'] or 0.0)
            for row in self.env.cr.dictfetchall()
        }

        records = []
        for journal in journals:
            balance = (
                running_balances.get(journal.id, 0.0)
                + direct_balances.get(journal.id, 0.0)
            )
            if not balance and journal.default_account_id:
                self.env.cr.execute("""
                    SELECT COALESCE(SUM(debit - credit), 0.0)
                      FROM account_move_line l
                      JOIN account_move m ON m.id = l.move_id
                     WHERE l.account_id = %s
                       AND m.state = 'posted'
                       AND m.company_id = %s
                """, [journal.default_account_id.id, company_id])
                row = self.env.cr.fetchone()
                balance = row[0] if row else 0.0
            records.append({
                'name': journal.name,
                'balance': round(float(balance or 0.0), 2),
                'id': journal.default_account_id.id if journal.default_account_id else journal.id,
            })
        return records
