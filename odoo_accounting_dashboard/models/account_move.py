# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import calendar
from odoo import api, models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model
    def get_datas(self):
        """Getting data for tiles in the dashboard: open invoice count, paid
        invoice count, total income, unreconciled items, and journal list.

        Bug fix: the original implementation called self.search([]) with no
        domain, loading every account.move record in the database into memory.
        Replaced with two focused search_count() calls scoped to the current
        company, and SQL-level aggregates for the income and reconcile counts.
        """
        company_id = self.env.company.id

        # Count draft moves (open invoices) for the current company only
        open_invoice = self.search_count([
            ('state', '=', 'draft'),
            ('move_type', 'in', ('out_invoice', 'in_invoice')),
            ('company_id', '=', company_id),
        ])

        # Count paid customer/vendor invoices for the current company only
        paid_invoice = self.search_count([
            ('payment_state', '=', 'paid'),
            ('move_type', 'in', ('out_invoice', 'in_invoice')),
            ('company_id', '=', company_id),
        ])

        # Total income: credit > debit on income-type accounts (company-scoped)
        self.env.cr.execute("""
            SELECT COALESCE(SUM(aml.debit), 0) AS debit,
                   COALESCE(SUM(aml.credit), 0) AS credit
            FROM account_move_line aml
            JOIN account_account aa ON aa.id = aml.account_id
            JOIN account_move am ON am.id = aml.move_id
            WHERE aa.account_type = 'income'
              AND am.company_id = %s
        """, [company_id])
        row = self.env.cr.dictfetchone()
        raw_income = (row['credit'] - row['debit']) if row else 0.0
        income = format(raw_income, ".2f")

        # Unreconciled items (company-scoped)
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

        # Journals for the current company
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
        """ Getting datas for income expense and profit chart based on current month and year """
        if income == 'income_this_month':
            query_income = """ select sum(debit)-sum(credit) as income ,cast(to_char(account_move_line.date, 'DD')as int)
                            as date , account_type from account_move_line , account_account
                            where account_move_line.account_id=account_account.id AND account_type='income' AND Extract(month FROM account_move_line.date) = Extract(month FROM DATE(NOW()))  
                            AND Extract(YEAR FROM account_move_line.date) = Extract(YEAR FROM DATE(NOW())) group by account_type,date """
            self.env.cr.execute(query_income)
            record = self.env.cr.dictfetchall()
            query_expense = """ select sum(debit)-sum(credit) as expense ,cast(to_char(account_move_line.date, 'DD')as int)
                            as date , account_type from account_move_line , account_account where  
                            account_move_line.account_id=account_account.id AND account_type='expense' AND Extract(month FROM account_move_line.date) = Extract(month FROM DATE(NOW()))  
                            AND Extract(YEAR FROM account_move_line.date) = Extract(YEAR FROM DATE(NOW())) group by account_type,date """
            self.env.cr.execute(query_expense)
            result = self.env.cr.dictfetchall()

            now = fields.Date.today()
            last_day = calendar.monthrange(now.year, now.month)[1]
            day_list = list(range(1, last_day + 1))
            records = []
            for date in day_list:
                last_month_inc = list(
                    filter(lambda m: m['date'] == date, record))
                last_month_exp = list(
                    filter(lambda m: m['date'] == date, result))
                if not last_month_inc and not last_month_exp:
                    records.append({
                        'date': date,
                        'income': 0.0,
                        'expense': 0.0,
                        'profit': 0.0
                    })
                elif (not last_month_inc) and last_month_exp:
                    last_month_exp[0].update({
                        'income': 0.0,
                        'expense': -1 * last_month_exp[0]['expense'] if
                        last_month_exp[0]['expense'] < 1 else
                        last_month_exp[0]['expense']
                    })
                    last_month_exp[0].update({
                        'profit': last_month_exp[0]['income'] -
                                  last_month_exp[0]['expense']
                    })
                    records.append(last_month_exp[0])
                elif (not last_month_exp) and last_month_inc:
                    last_month_inc[0].update({
                        'expense': 0.0,
                        'income': -1 * last_month_inc[0]['income'] if
                        last_month_inc[0]['income'] < 1 else
                        last_month_inc[0]['income']
                    })
                    last_month_inc[0].update({
                        'profit': last_month_inc[0]['income'] -
                                  last_month_inc[0]['expense']
                    })
                    records.append(last_month_inc[0])
                else:
                    last_month_inc[0].update({
                        'income': -1 * last_month_inc[0]['income'] if
                        last_month_inc[0]['income'] < 1 else
                        last_month_inc[0]['income'],
                        'expense': -1 * last_month_exp[0]['expense'] if
                        last_month_exp[0]['expense'] < 1 else
                        last_month_exp[0]['expense']
                    })
                    last_month_inc[0].update({
                        'profit': last_month_inc[0]['income'] -
                                  last_month_inc[0]['expense']
                    })
                    records.append(last_month_inc[0])
            income = []
            expense = []
            date = []
            profit = []
            for rec in records:
                income.append(rec['income'])
                expense.append(rec['expense'])
                date.append(rec['date'])
                profit.append(rec['profit'])
            return {
                'income': income,
                'expense': expense,
                'date': date,
                'profit': profit
            }
        elif income == 'income_this_year':
            query_income = """ select sum(debit)-sum(credit) as income ,to_char(account_move_line.date, 'Month')  as month ,
                            account_type from account_move_line ,account_account
                            where account_move_line.account_id=account_account.id AND account_type = 'income' 
                            AND to_char(DATE(NOW()), 'YY') = to_char(account_move_line.date, 'YY')
                            group by account_type,month """
            self.env.cr.execute(query_income)
            record = self.env.cr.dictfetchall()
            query_expense = """ select sum(debit)-sum(credit) as expense ,to_char(account_move_line.date, 'Month')  as month ,
                            account_type from account_move_line , account_account where 
                            account_move_line.account_id=account_account.id AND account_type = 'expense'
                            AND to_char(DATE(NOW()), 'YY') = to_char(account_move_line.date, 'YY')
                            group by account_type,month """
            self.env.cr.execute(query_expense)
            result = self.env.cr.dictfetchall()

            month_list = calendar.month_name[1:]
            records = []
            for month in month_list:
                last_month_inc = list(
                    filter(lambda m: m['month'].strip() == month, record))
                last_month_exp = list(
                    filter(lambda m: m['month'].strip() == month, result))
                if not last_month_inc and not last_month_exp:
                    records.append({
                        'month': month,
                        'income': 0.0,
                        'expense': 0.0,
                        'profit': 0.0,
                    })
                elif (not last_month_inc) and last_month_exp:
                    last_month_exp[0].update({
                        'income': 0.0,
                        'expense': -1 * last_month_exp[0]['expense'] if
                        last_month_exp[0]['expense'] < 1 else
                        last_month_exp[0]['expense']
                    })
                    last_month_exp[0].update({
                        'profit': last_month_exp[0]['income'] -
                                  last_month_exp[0]['expense']
                    })
                    records.append(last_month_exp[0])
                elif (not last_month_exp) and last_month_inc:
                    last_month_inc[0].update({
                        'expense': 0.0,
                        'income': -1 * last_month_inc[0]['income'] if
                        last_month_inc[0]['income'] < 1 else
                        last_month_inc[0]['income']
                    })
                    last_month_inc[0].update({
                        'profit': last_month_inc[0]['income'] -
                                  last_month_inc[0]['expense']
                    })
                    records.append(last_month_inc[0])
                else:
                    last_month_inc[0].update({
                        'income': -1 * last_month_inc[0]['income'] if
                        last_month_inc[0]['income'] < 1 else
                        last_month_inc[0]['income'],
                        'expense': -1 * last_month_exp[0]['expense'] if
                        last_month_exp[0]['expense'] < 1 else
                        last_month_exp[0]['expense']
                    })
                    last_month_inc[0].update({
                        'profit': last_month_inc[0]['income'] -
                                  last_month_inc[0]['expense']
                    })
                    records.append(last_month_inc[0])
            income = []
            expense = []
            month = []
            profit = []
            for rec in records:
                income.append(rec['income'])
                expense.append(rec['expense'])
                month.append(rec['month'])
                profit.append(rec['profit'])
            return {
                'income': income,
                'expense': expense,
                'date': month,
                'profit': profit,
            }

    @api.model
    def get_payment_data(self, payment_list_filter, payment_data_filter):
        """ Getting datas for customer payment list and vendor payment list based on current year and month"""
        last_day = (calendar.monthrange(fields.Date.today().year, fields.Date.today().month))[1]
        if payment_list_filter == 'customer_payment':
            if payment_data_filter == 'this_month':
                start_date = f"{fields.Date.today().year}-{fields.Date.today().month:02d}-01"
                end_date = f"{fields.Date.today().year}-{fields.Date.today().month:02d}-{last_day}"
                invoices = self.search(
                    [('move_type', '=', 'out_invoice'),
                     ('payment_state', '=', 'paid'),
                     ('invoice_date', '>=', start_date),
                     ('invoice_date', '<=', end_date)])
            else:
                start_date = f"{fields.Date.today().year}-01-01"
                end_date = f"{fields.Date.today().year}-12-31"
                invoices = self.search(
                    [('move_type', '=', 'out_invoice'),
                     ('payment_state', '=', 'paid'),
                     ('invoice_date', '>=', start_date),
                     ('invoice_date', '<=', end_date)])
            result = []
            for i in invoices:
                result.append({'id': i.id,
                               'partner': i.partner_id.name,
                               'amount': i.amount_total,
                               'date': str(i.invoice_date)})
            return result
        else:
            if payment_data_filter == 'this_month':
                start_date = f"{fields.Date.today().year}-{fields.Date.today().month:02d}-01"
                end_date = f"{fields.Date.today().year}-{fields.Date.today().month:02d}-{last_day}"
                vendor_bills = self.search(
                    [('move_type', '=', 'in_invoice'),
                     ('payment_state', '=', 'paid'),
                     ('invoice_date', '>=', start_date),
                     ('invoice_date', '<=', end_date)])
            else:
                start_date = f"{fields.Date.today().year}-01-01"
                end_date = f"{fields.Date.today().year}-12-31"
                vendor_bills = self.search(
                    [('move_type', '=', 'in_invoice'),
                     ('payment_state', '=', 'paid'),
                     ('invoice_date', '>=', start_date),
                     ('invoice_date', '<=', end_date)])
            result = []
            for i in vendor_bills:
                result.append({'id': i.id,
                               'partner': i.partner_id.name,
                               'amount': i.amount_total,
                               'date': str(i.invoice_date)})
            return result

    @api.model
    def get_top_datas(self, top_filter):
        """Return top customers and top vendors ranked by total invoiced amount
        for the selected period (this_month / this_year).

        Bug fix: the original implementation called filtered() but discarded
        the result, so partners were listed in arbitrary order with no amounts.
        Replaced with a dict-based aggregation that sums amount_total per
        partner and sorts descending, producing a genuine ranking.
        """
        today = fields.Date.today()
        last_day = calendar.monthrange(today.year, today.month)[1]

        if top_filter == 'this_month':
            start_date = f"{today.year}-{today.month:02d}-01"
            end_date = f"{today.year}-{today.month:02d}-{last_day}"
        else:
            start_date = f"{today.year}-01-01"
            end_date = f"{today.year}-12-31"

        date_domain = [
            ('invoice_date', '>=', start_date),
            ('invoice_date', '<=', end_date),
            ('company_id', '=', self.env.company.id),
            ('state', '=', 'posted'),
        ]

        vendor_bills = self.search(
            date_domain + [('move_type', '=', 'in_invoice')])
        customer_invoices = self.search(
            date_domain + [('move_type', '=', 'out_invoice')])

        # Aggregate total amount per vendor partner and sort descending
        vendor_totals = {}
        for bill in vendor_bills:
            pid = bill.partner_id.id
            if pid:
                if pid not in vendor_totals:
                    vendor_totals[pid] = {
                        'id': pid,
                        'name': bill.partner_id.name,
                        'amount': 0.0,
                    }
                vendor_totals[pid]['amount'] += bill.amount_total
        top_vendors = sorted(
            vendor_totals.values(), key=lambda v: v['amount'], reverse=True
        )

        # Aggregate total amount per customer partner and sort descending
        customer_totals = {}
        for inv in customer_invoices:
            pid = inv.partner_id.id
            if pid:
                if pid not in customer_totals:
                    customer_totals[pid] = {
                        'id': pid,
                        'name': inv.partner_id.name,
                        'amount': 0.0,
                    }
                customer_totals[pid]['amount'] += inv.amount_total
        top_customers = sorted(
            customer_totals.values(), key=lambda v: v['amount'], reverse=True
        )

        return {
            'top_vendors': top_vendors,
            'top_customers': top_customers,
        }

    @api.model
    def get_aged_payable(self, aged_filter, aged_payable_filter):
        """ Getting Datas for aged payable and aged receivable chart based on current month and year"""
        if aged_filter == 'aged_receive':
            if aged_payable_filter == 'this_month':
                self.env.cr.execute(""" select to_char(account_move.date, 'Month') as month, res_partner.name as due_partner, account_move.partner_id as parent,
                                   sum(account_move.amount_total) as amount from account_move, res_partner where account_move.partner_id = res_partner.id
                                   AND account_move.move_type = 'out_invoice'
                                   AND payment_state = 'not_paid'
                                   AND Extract(month FROM account_move.invoice_date_due) = Extract(month FROM DATE(NOW()))
                                   AND Extract(YEAR FROM account_move.invoice_date_due) = Extract(YEAR FROM DATE(NOW()))
                                   AND account_move.partner_id = res_partner.commercial_partner_id
                                   group by parent, due_partner, month
                                   order by amount desc""")
            else:
                self.env.cr.execute("""select  res_partner.name as due_partner, account_move.partner_id as parent,
                                                sum(account_move.amount_total) as amount from account_move, res_partner where account_move.partner_id = res_partner.id
                                                AND account_move.move_type = 'out_invoice'
                                                AND payment_state = 'not_paid'
                                                AND Extract(YEAR FROM account_move.invoice_date_due) = Extract(YEAR FROM DATE(NOW()))
                                                AND account_move.partner_id = res_partner.commercial_partner_id
                                                group by parent, due_partner
                                                order by amount desc""")
            record = self.env.cr.dictfetchall()
            partner = [item['due_partner'] for item in record]
            amount = [item['amount'] for item in record]
            return {'partner': partner,
                    'amount': amount, }
        else:
            if aged_payable_filter == 'this_month':
                self.env.cr.execute("""select to_char(account_move.date, 'Month') as month, res_partner.name as bill_partner, account_move.partner_id as parent,
                                sum(account_move.amount_total) as amount from account_move, res_partner where account_move.partner_id = res_partner.id
                                AND account_move.move_type = 'in_invoice'
                                AND payment_state = 'not_paid'
                                AND Extract(month FROM account_move.invoice_date_due) = Extract(month FROM DATE(NOW()))
                                AND Extract(YEAR FROM account_move.invoice_date_due) = Extract(YEAR FROM DATE(NOW()))
                                AND account_move.partner_id = res_partner.commercial_partner_id
                                group by parent, bill_partner, month
                                order by amount desc""")
            else:
                self.env.cr.execute("""select to_char(account_move.date, 'Month') as month, res_partner.name as bill_partner, account_move.partner_id as parent,
                                sum(account_move.amount_total) as amount from account_move, res_partner where account_move.partner_id = res_partner.id
                                AND account_move.move_type = 'in_invoice'
                                AND payment_state = 'not_paid'
                                AND Extract(YEAR FROM account_move.invoice_date_due) = Extract(YEAR FROM DATE(NOW()))
                                AND account_move.partner_id = res_partner.commercial_partner_id
                                group by parent, bill_partner, month
                                order by amount desc""")
            record = self.env.cr.dictfetchall()
            partner = [item['bill_partner'] for item in record]
            amount = [item['amount'] for item in record]
            return {'partner': partner,
                    'amount': amount, }

    @api.model
    def get_sale_revenue(self, top_sale_cust_filter):
        """Getting top-10 sale revenue customers for the current month or year.

        Fixes applied:
          1. state = 'posted'       — exclude draft and cancelled invoices.
          2. company_id filter      — scope to the current company only.
          3. amount_untaxed_signed  — show net revenue (excl. tax) instead of
                                      the tax-inclusive amount_total_signed.
          4. Parameterized query    — prevent SQL injection via %s placeholders.
        """
        company_id = self.env.company.id

        base_query = """
            SELECT account_move.partner_id             AS customer_id,
                   MAX(res_partner.name)               AS customer,
                   SUM(account_move.amount_untaxed_signed) AS total_amount
              FROM account_move
              JOIN res_partner ON res_partner.id = account_move.partner_id
             WHERE account_move.move_type  = 'out_invoice'
               AND account_move.state      = 'posted'
               AND account_move.company_id = %s
        """

        if top_sale_cust_filter == 'this_month':
            query = base_query + """
               AND EXTRACT(month FROM account_move.invoice_date)
                   = EXTRACT(month FROM CURRENT_DATE)
               AND EXTRACT(year  FROM account_move.invoice_date)
                   = EXTRACT(year  FROM CURRENT_DATE)
             GROUP BY account_move.partner_id
             ORDER BY total_amount DESC
             LIMIT 10
            """
        else:  # this_year
            query = base_query + """
               AND EXTRACT(year FROM account_move.invoice_date)
                   = EXTRACT(year FROM CURRENT_DATE)
             GROUP BY account_move.partner_id
             ORDER BY total_amount DESC
             LIMIT 10
            """

        self.env.cr.execute(query, [company_id])
        return self.env.cr.dictfetchall()


    @api.model
    def get_bank_balance(self):
        """Getting data for bank and cash balance.

        Uses the exact same logic as Odoo's native Accounting app dashboard
        (account_journal_dashboard.py) so that the balance shown here always
        matches what the user sees in the native app.

        Native formula:
          Balance = last_statement.balance_end_real
                  + SUM(unlinked statement lines since last statement)
                  + SUM(direct bank payments that bypassed the suspense account)

        When no bank statements exist the formula simplifies to:
          Balance = SUM(all unlinked statement lines for the journal)
        """
        company_id = self.env.company.id
        journals = self.env['account.journal'].search([
            ('type', 'in', ['bank', 'cash']),
            ('company_id', '=', company_id),
        ])

        # Step 1: running balance = last statement balance_end_real
        #         + unlinked statement lines since the last statement
        # (mirrors _get_journal_dashboard_bank_running_balance)
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
            row['journal_id']: row['balance_end_real'] + row['unlinked_amount']
            for row in self.env.cr.dictfetchall()
        }

        # Step 2: direct bank payments (payments whose outstanding account IS
        #         the journal's default/bank account, i.e. bypassed suspense)
        # (mirrors _get_direct_bank_payments)
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
            row['journal_id']: (row['amount_total'] or 0.0)
            for row in self.env.cr.dictfetchall()
        }

        records = []
        for journal in journals:
            balance = (
                running_balances.get(journal.id, 0.0)
                + direct_balances.get(journal.id, 0.0)
            )
            records.append({
                'name': journal.name,
                'balance': balance,
                'id': journal.default_account_id.id,
            })
        return records
