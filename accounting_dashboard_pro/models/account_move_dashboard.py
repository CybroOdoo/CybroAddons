# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
#
#    This program is under the terms of the Odoo Proprietary License v1.0
#    (OPL-1)
#    It is forbidden to publish, distribute, sublicense, or sell copies of the
#    Software or modified copies of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#    IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY
#    CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT
#    OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR
#    THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
##############################################################################
from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models
from odoo.tools.translate import _
from odoo.exceptions import AccessError


class AccountMoveLineDashboard(models.Model):
    """Account Move Line extensions for dashboard compatibility."""
    _inherit = 'account.move.line'

    exclude_bank_lines = fields.Boolean(compute=lambda self: False, search='_search_exclude_bank_lines')
    
    def _search_exclude_bank_lines(self, operator, value):
        """Dummy search method for exclude_bank_lines to prevent UI crash when account_reports is not installed."""
        return []


class AccountMoveDashboard(models.Model):
    """Account Move extensions to provide dashboard data APIs."""
    _inherit = 'account.move'

    # -------------------------------------------------------------------------
    # HELPERS
    # -------------------------------------------------------------------------

    @api.model
    def _dashboard_check_group(self, group_xmlids):
        """Raise AccessError if current user lacks the given group(s)."""
        if isinstance(group_xmlids, str):
            group_xmlids = [group_xmlids]
        if not any(self.env.user.has_group(g) for g in group_xmlids):
            raise AccessError(_('You do not have access to this dashboard data.'))

    @api.model
    def _dashboard_get_period(self, period, date_from=None, date_to=None):
        """Return (date_from, date_to) tuple for the given period key."""
        today = fields.Date.context_today(self)
        if period == 'this_month':
            d_from = today.replace(day=1)
            d_to = today
        elif period == 'last_month':
            d_from = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
            d_to = today.replace(day=1) - timedelta(days=1)
        elif period == 'this_quarter':
            q = (today.month - 1) // 3
            d_from = date(today.year, q * 3 + 1, 1)
            d_to = today
        elif period == 'last_quarter':
            q = (today.month - 1) // 3
            d_to = date(today.year, q * 3 + 1, 1) - timedelta(days=1)
            lq = (d_to.month - 1) // 3
            d_from = date(d_to.year, lq * 3 + 1, 1)
        elif period == 'this_year':
            d_from = date(today.year, 1, 1)
            d_to = today
        elif period == 'last_year':
            d_from = date(today.year - 1, 1, 1)
            d_to = date(today.year - 1, 12, 31)
        elif period == 'custom' and date_from and date_to:
            d_from = fields.Date.from_string(date_from) if isinstance(date_from, str) else date_from
            d_to = fields.Date.from_string(date_to) if isinstance(date_to, str) else date_to
        else:
            d_from = today.replace(day=1)
            d_to = today
        return d_from, d_to

    @api.model
    def _dashboard_prev_period(self, date_from, date_to):
        """Return previous period dates with same length."""
        delta = (date_to - date_from).days + 1
        prev_to = date_from - timedelta(days=1)
        prev_from = prev_to - timedelta(days=delta - 1)
        return prev_from, prev_to

    @api.model
    def _dashboard_company_ids(self, company_ids=None):
        """Return company IDs to filter on."""
        if company_ids:
            allowed = self.env.companies.ids
            return [cid for cid in company_ids if cid in allowed]
        return self.env.companies.ids

    @staticmethod
    def _safe_change_pct(current, previous):
        """Calculate percentage change safely."""
        if previous:
            return round(((current - previous) / abs(previous)) * 100, 1)
        return 0.0

    # -------------------------------------------------------------------------
    # KPI DATA
    # -------------------------------------------------------------------------

    @api.model
    def get_dashboard_kpi_data(self, params):
        """
        Return KPI card data with previous period comparison.
        Access: group_account_invoice+
        """
        self._dashboard_check_group(['account.group_account_invoice', 'account.group_account_readonly', 'account.group_account_user'])

        period = params.get('period', 'this_month')
        date_from, date_to = self._dashboard_get_period(
            period, params.get('date_from'), params.get('date_to')
        )
        company_ids = self._dashboard_company_ids(params.get('company_ids'))
        prev_from, prev_to = self._dashboard_prev_period(date_from, date_to)
        today = fields.Date.context_today(self)

        result = {
            'user_groups': {
                'is_invoicing': self.env.user.has_group('account.group_account_invoice'),
                'is_basic': self.env.user.has_group('account.group_account_user'),
                'is_readonly': self.env.user.has_group('account.group_account_readonly'),
                'is_user': self.env.user.has_group('account.group_account_user'),
                'is_manager': self.env.user.has_group('account.group_account_manager'),
            },
        }
        # --- Invoice summary (current period) ---
        self.env.cr.execute("""
            SELECT move_type, state,
                   COUNT(*) as cnt,
                   COALESCE(SUM(amount_total_signed), 0) as total
            FROM account_move
            WHERE move_type IN ('out_invoice', 'out_refund', 'in_invoice', 'in_refund')
              AND company_id = ANY(%s)
              AND date BETWEEN %s AND %s
            GROUP BY move_type, state
        """, (company_ids, date_from, date_to))
        invoice_data = self.env.cr.dictfetchall()

        # Previous period invoice summary
        self.env.cr.execute("""
            SELECT move_type,
                   COALESCE(SUM(amount_total_signed), 0) as total
            FROM account_move
            WHERE move_type IN ('out_invoice', 'in_invoice')
              AND state = 'posted'
              AND company_id = ANY(%s)
              AND date BETWEEN %s AND %s
            GROUP BY move_type
        """, (company_ids, prev_from, prev_to))
        prev_invoice_data = self.env.cr.dictfetchall()
        prev_inv_map = {r['move_type']: r['total'] for r in prev_invoice_data}

        out_posted = sum(r['total'] for r in invoice_data if r['move_type'] == 'out_invoice' and r['state'] == 'posted')
        out_draft_count = sum(r['cnt'] for r in invoice_data if r['move_type'] == 'out_invoice' and r['state'] == 'draft')
        out_posted_count = sum(r['cnt'] for r in invoice_data if r['move_type'] == 'out_invoice' and r['state'] == 'posted')

        in_posted = sum(r['total'] for r in invoice_data if r['move_type'] == 'in_invoice' and r['state'] == 'posted')
        in_draft_count = sum(r['cnt'] for r in invoice_data if r['move_type'] == 'in_invoice' and r['state'] == 'draft')
        in_posted_count = sum(r['cnt'] for r in invoice_data if r['move_type'] == 'in_invoice' and r['state'] == 'posted')

        prev_out = prev_inv_map.get('out_invoice', 0)
        prev_in = prev_inv_map.get('in_invoice', 0)

        result['invoices'] = {
            'posted_amount': out_posted,
            'posted_count': out_posted_count,
            'draft_count': out_draft_count,
            'prev_amount': prev_out,
            'change_pct': self._safe_change_pct(out_posted, prev_out),
        }
        result['bills'] = {
            'posted_amount': abs(in_posted),
            'posted_count': in_posted_count,
            'draft_count': in_draft_count,
            'prev_amount': abs(prev_in),
            'change_pct': self._safe_change_pct(abs(in_posted), abs(prev_in)),
        }
        # --- Overdue ---
        self.env.cr.execute("""
            SELECT move_type,
                   COUNT(*) as cnt,
                   COALESCE(SUM(amount_residual_signed), 0) as total
            FROM account_move
            WHERE state = 'posted'
              AND payment_state IN ('not_paid', 'partial')
              AND invoice_date_due < %s
              AND move_type IN ('out_invoice', 'in_invoice')
              AND company_id = ANY(%s)
              AND date BETWEEN %s AND %s
            GROUP BY move_type
        """, (today, company_ids, date_from, date_to))
        overdue_data = self.env.cr.dictfetchall()

        result['overdue_receivable'] = {
            'count': sum(r['cnt'] for r in overdue_data if r['move_type'] == 'out_invoice'),
            'amount': sum(r['total'] for r in overdue_data if r['move_type'] == 'out_invoice'),
        }
        result['overdue_payable'] = {
            'count': sum(r['cnt'] for r in overdue_data if r['move_type'] == 'in_invoice'),
            'amount': abs(sum(r['total'] for r in overdue_data if r['move_type'] == 'in_invoice')),
        }

        # --- Financial KPIs (readonly+ users) ---
        if result['user_groups']['is_readonly']:
            # Revenue (current + prev)
            self.env.cr.execute("""
                SELECT COALESCE(SUM(amount_untaxed_signed), 0)
                FROM account_move
                WHERE state = 'posted' AND move_type = 'out_invoice'
                  AND date BETWEEN %s AND %s AND company_id = ANY(%s)
            """, (date_from, date_to, company_ids))
            revenue = self.env.cr.fetchone()[0]

            self.env.cr.execute("""
                SELECT COALESCE(SUM(amount_untaxed_signed), 0)
                FROM account_move
                WHERE state = 'posted' AND move_type = 'out_invoice'
                  AND date BETWEEN %s AND %s AND company_id = ANY(%s)
            """, (prev_from, prev_to, company_ids))
            prev_revenue = self.env.cr.fetchone()[0]

            # Expenses (current + prev)
            self.env.cr.execute("""
                SELECT COALESCE(SUM(amount_untaxed_signed), 0)
                FROM account_move
                WHERE state = 'posted' AND move_type = 'in_invoice'
                  AND date BETWEEN %s AND %s AND company_id = ANY(%s)
            """, (date_from, date_to, company_ids))
            expenses = abs(self.env.cr.fetchone()[0])

            self.env.cr.execute("""
                SELECT COALESCE(SUM(amount_untaxed_signed), 0)
                FROM account_move
                WHERE state = 'posted' AND move_type = 'in_invoice'
                  AND date BETWEEN %s AND %s AND company_id = ANY(%s)
            """, (prev_from, prev_to, company_ids))
            prev_expenses = abs(self.env.cr.fetchone()[0])

            net_profit = revenue - expenses
            prev_net_profit = prev_revenue - prev_expenses
            result['revenue'] = {
                'amount': revenue,
                'prev_amount': prev_revenue,
                'change_pct': self._safe_change_pct(revenue, prev_revenue),
            }
            result['expenses'] = {
                'amount': expenses,
                'prev_amount': prev_expenses,
                'change_pct': self._safe_change_pct(expenses, prev_expenses),
            }
            result['net_profit'] = {
                'amount': net_profit,
                'prev_amount': prev_net_profit,
                'change_pct': self._safe_change_pct(net_profit, prev_net_profit) if prev_net_profit else 0,
            }

        # --- Cash Balance (basic+ users or readonly users) ---
        if result['user_groups']['is_basic'] or result['user_groups']['is_readonly']:
            # Current cash balance
            self.env.cr.execute("""
                SELECT COALESCE(SUM(aml.balance), 0)
                FROM account_move_line aml
                WHERE aml.parent_state = 'posted'
                  AND aml.date BETWEEN %s AND %s
                  AND aml.company_id = ANY(%s)
                  AND EXISTS (
                      SELECT 1
                      FROM account_journal aj
                      WHERE aj.default_account_id = aml.account_id
                        AND aj.type IN ('bank', 'cash')
                  )
            """, (date_from, date_to, company_ids))

            cash_balance = self.env.cr.fetchone()[0]

            self.env.cr.execute("""
                SELECT COALESCE(SUM(aml.balance), 0)
                FROM account_move_line aml
                JOIN account_move am ON am.id = aml.move_id
                WHERE aml.parent_state = 'posted'
                  AND am.date <= %s
                  AND aml.company_id = ANY(%s)
                  AND EXISTS (
                      SELECT 1
                      FROM account_journal aj
                      WHERE aj.default_account_id = aml.account_id
                        AND aj.type IN ('bank', 'cash')
                  )""", (prev_to, company_ids))

            prev_cash_balance = self.env.cr.fetchone()[0]
            result['cash_balance'] = {
                'amount': cash_balance,
                'prev_amount': prev_cash_balance,
                'change_pct': self._safe_change_pct(cash_balance, prev_cash_balance),
            }
            # --- CASH FLOW KPIs ---

            # Total Receivable (all open customer invoices)
            self.env.cr.execute("""
                SELECT COALESCE(SUM(amount_residual_signed), 0)
                FROM account_move
                WHERE state = 'posted'
                  AND move_type = 'out_invoice'
                  AND date BETWEEN %s AND %s
                  AND payment_state IN ('not_paid', 'partial')
                  AND company_id = ANY(%s)
            """, (date_from, date_to,company_ids,))
            total_receivable = self.env.cr.fetchone()[0]

            # Previous receivable (open invoices as of prev_to)
            self.env.cr.execute("""
                SELECT COALESCE(SUM(amount_residual_signed), 0)
                FROM account_move
                WHERE state = 'posted'
                  AND move_type = 'out_invoice'
                  AND payment_state IN ('not_paid', 'partial')
                  AND date <= %s
                  AND company_id = ANY(%s)
            """, (prev_to, company_ids))
            prev_receivable = self.env.cr.fetchone()[0]

            # Total Payable (all open vendor bills)
            self.env.cr.execute("""
                SELECT COALESCE(SUM(ABS(amount_residual_signed)), 0)
                FROM account_move
                WHERE state = 'posted'
                  AND move_type = 'in_invoice'
                  AND date BETWEEN %s AND %s
                  AND payment_state IN ('not_paid', 'partial')
                  AND company_id = ANY(%s)
            """, (date_from, date_to, company_ids,))
            total_payable = self.env.cr.fetchone()[0]

            # Previous payable
            self.env.cr.execute("""
                SELECT COALESCE(SUM(ABS(amount_residual_signed)), 0)
                FROM account_move
                WHERE state = 'posted'
                  AND move_type = 'in_invoice'
                  AND payment_state IN ('not_paid', 'partial')
                  AND date <= %s
                  AND company_id = ANY(%s)
            """, (prev_to, company_ids))
            prev_payable = self.env.cr.fetchone()[0]

            # Net Cash Position = Cash Balance - Total Payable
            net_cash_position = cash_balance - total_payable
            prev_net_cash = prev_cash_balance - prev_payable

            # Cash Burn Rate (avg daily expenses in current period)
            period_days = max((date_to - date_from).days, 1)
            if result['user_groups']['is_readonly']:
                burn_rate = expenses / period_days if period_days else 0
            else:
                self.env.cr.execute("""
                    SELECT COALESCE(SUM(ABS(amount_untaxed_signed)), 0)
                    FROM account_move
                    WHERE state = 'posted' AND move_type = 'in_invoice'
                      AND date BETWEEN %s AND %s AND company_id = ANY(%s)
                """, (date_from, date_to, company_ids))
                expenses_for_burn = self.env.cr.fetchone()[0]
                burn_rate = expenses_for_burn / period_days

            # Previous burn rate
            prev_period_days = max((prev_to - prev_from).days, 1)
            self.env.cr.execute("""
                SELECT COALESCE(SUM(ABS(amount_untaxed_signed)), 0)
                FROM account_move
                WHERE state = 'posted' AND move_type = 'in_invoice'
                  AND date BETWEEN %s AND %s AND company_id = ANY(%s)
            """, (prev_from, prev_to, company_ids))
            prev_burn_rate = self.env.cr.fetchone()[0] / prev_period_days

            # Runway Days = Cash Balance / Burn Rate
            runway_days = round(cash_balance / burn_rate) if burn_rate > 0 else 999
            prev_runway = round(prev_cash_balance / prev_burn_rate) if prev_burn_rate > 0 else 999

            result['total_receivable'] = {
                'amount': total_receivable,
                'prev_amount': prev_receivable,
                'change_pct': self._safe_change_pct(total_receivable, prev_receivable),
            }
            result['total_payable'] = {
                'amount': total_payable,
                'prev_amount': prev_payable,
                'change_pct': self._safe_change_pct(total_payable, prev_payable),
            }
            result['net_cash_position'] = {
                'amount': net_cash_position,
                'prev_amount': prev_net_cash,
                'change_pct': self._safe_change_pct(net_cash_position, prev_net_cash) if prev_net_cash else 0,
            }
            result['cash_burn_rate'] = {
                'amount': round(burn_rate, 2),
                'prev_amount': round(prev_burn_rate, 2),
                'change_pct': self._safe_change_pct(burn_rate, prev_burn_rate),
            }
            result['runway_days'] = {
                'amount': runway_days,
                'prev_amount': prev_runway,
                'change_pct': self._safe_change_pct(runway_days, prev_runway),
            }

            # ------ NEW CFO KPIs ------

            # Working Capital = Total Receivable + Cash - Total Payable
            working_capital = total_receivable + cash_balance - total_payable
            prev_working_capital = prev_receivable + prev_cash_balance - prev_payable
            result['working_capital'] = {
                'amount': working_capital,
                'prev_amount': prev_working_capital,
                'change_pct': self._safe_change_pct(working_capital, prev_working_capital) if prev_working_capital else 0,
            }
            # Gross Margin % = (Revenue - COGS) / Revenue * 100
            # COGS approximated by expenses for bill product lines in period
            if result['user_groups']['is_readonly'] and revenue:
                gross_margin = round((revenue - expenses) / revenue * 100, 1)
                prev_gross = round((prev_revenue - prev_expenses) / prev_revenue * 100, 1) if prev_revenue else 0
            else:
                gross_margin = 0
                prev_gross = 0
            result['gross_margin'] = {
                'amount': gross_margin,
                'prev_amount': prev_gross,
                'change_pct': round(gross_margin - prev_gross, 1),  # pp change
            }
            # DSO = (Receivable / Revenue) * Period Days
            if result['user_groups']['is_readonly'] and revenue:
                dso = round(total_receivable / revenue * period_days, 1)
                prev_dso = round(prev_receivable / prev_revenue * prev_period_days, 1) if prev_revenue else 0
            else:
                dso = 0
                prev_dso = 0
            result['dso'] = {
                'amount': dso,
                'prev_amount': prev_dso,
                'change_pct': self._safe_change_pct(dso, prev_dso) if prev_dso else 0,
            }

            # DPO = (Payable / Expenses) * Period Days
            if result['user_groups']['is_readonly'] and expenses:
                dpo = round(total_payable / expenses * period_days, 1)
                prev_dpo = round(prev_payable / prev_expenses * prev_period_days, 1) if prev_expenses else 0
            else:
                dpo = 0
                prev_dpo = 0
            result['dpo'] = {
                'amount': dpo,
                'prev_amount': prev_dpo,
                'change_pct': self._safe_change_pct(dpo, prev_dpo) if prev_dpo else 0,
            }

        # --- Unreconciled count (basic+ users or readonly users) ---
        if result['user_groups']['is_basic'] or result['user_groups']['is_readonly']:
            result['unreconciled_count'] = self.env['account.bank.statement.line'].search_count([
                ('is_reconciled', '=', False),
                ('company_id', 'in', company_ids)
            ])

        result['currency_id'] = self.env.company.currency_id.id
        result['currency_symbol'] = self.env.company.currency_id.symbol
        result['period'] = {'date_from': str(date_from), 'date_to': str(date_to)}

        return result

    # -------------------------------------------------------------------------
    # CHART DATA
    # -------------------------------------------------------------------------

    @api.model
    def get_dashboard_chart_data(self, params):
        """Revenue vs Expense monthly chart data. Access: group_account_readonly+"""
        self._dashboard_check_group(['account.group_account_readonly', 'account.group_account_manager'])

        company_ids = self._dashboard_company_ids(params.get('company_ids'))
        today = fields.Date.context_today(self)
        date_from = today - relativedelta(months=11, day=1)

        self.env.cr.execute("""
            SELECT
                to_char(date, 'YYYY-MM') AS month,
                move_type,
                COALESCE(SUM(amount_untaxed_signed), 0) AS total
            FROM account_move
            WHERE state = 'posted'
              AND move_type IN ('out_invoice', 'in_invoice')
              AND date >= %s
              AND company_id = ANY(%s)
            GROUP BY to_char(date, 'YYYY-MM'), move_type
            ORDER BY month
        """, (date_from, company_ids))
        rows = self.env.cr.dictfetchall()

        months = []
        d = date_from
        while d <= today:
            months.append(d.strftime('%Y-%m'))
            d += relativedelta(months=1)

        revenue_map = {r['month']: r['total'] for r in rows if r['move_type'] == 'out_invoice'}
        expense_map = {r['month']: abs(r['total']) for r in rows if r['move_type'] == 'in_invoice'}

        return {
            'labels': months,
            'revenue': [revenue_map.get(m, 0) for m in months],
            'expenses': [expense_map.get(m, 0) for m in months],
        }

    @api.model
    def get_dashboard_cashflow(self, params):
        """Cash flow forecast for next N days. Access: group_account_readonly+"""
        self._dashboard_check_group(['account.group_account_readonly', 'account.group_account_manager'])

        company_ids = self._dashboard_company_ids(params.get('company_ids'))
        days = params.get('days', 90)
        today = fields.Date.context_today(self)
        end_date = today + timedelta(days=days)

        self.env.cr.execute("""
            SELECT COALESCE(SUM(aml.balance), 0)
            FROM account_move_line aml
            JOIN account_journal aj ON aj.default_account_id = aml.account_id
            WHERE aj.type IN ('bank', 'cash')
              AND aml.parent_state = 'posted'
              AND aml.company_id = ANY(%s)
        """, (company_ids,))
        current_balance = self.env.cr.fetchone()[0]

        self.env.cr.execute("""
            SELECT
                COALESCE(invoice_date_due, date) AS due,
                COALESCE(SUM(amount_residual_signed), 0) AS total
            FROM account_move
            WHERE state = 'posted'
              AND move_type = 'out_invoice'
              AND payment_state IN ('not_paid', 'partial')
              AND COALESCE(invoice_date_due, date) BETWEEN %s AND %s
              AND company_id = ANY(%s)
            GROUP BY due ORDER BY due
        """, (today, end_date, company_ids))
        inflows = {str(r['due']): r['total'] for r in self.env.cr.dictfetchall()}

        self.env.cr.execute("""
            SELECT
                COALESCE(invoice_date_due, date) AS due,
                COALESCE(SUM(ABS(amount_residual_signed)), 0) AS total
            FROM account_move
            WHERE state = 'posted'
              AND move_type = 'in_invoice'
              AND payment_state IN ('not_paid', 'partial')
              AND COALESCE(invoice_date_due, date) BETWEEN %s AND %s
              AND company_id = ANY(%s)
            GROUP BY due ORDER BY due
        """, (today, end_date, company_ids))
        outflows = {str(r['due']): r['total'] for r in self.env.cr.dictfetchall()}

        labels = []
        data = []
        balance = current_balance
        d = today
        while d <= end_date:
            ds = str(d)
            balance += inflows.get(ds, 0) - outflows.get(ds, 0)
            labels.append(ds)
            data.append(round(balance, 2))
            d += timedelta(days=1)

        return {
            'labels': labels,
            'data': data,
            'current_balance': current_balance,
        }

    @api.model
    def get_dashboard_aging(self, params):
        """Aging analysis. Access: group_account_basic+"""
        self._dashboard_check_group(['account.group_account_user', 'account.group_account_readonly', 'account.group_account_invoice'])

        company_ids = self._dashboard_company_ids(params.get('company_ids'))
        a_type = params.get('type', 'receivable')
        today = fields.Date.context_today(self)
        account_type = 'asset_receivable' if a_type == 'receivable' else 'liability_payable'

        self.env.cr.execute("""
            SELECT
                CASE
                    WHEN %s - COALESCE(aml.date_maturity, aml.date) <= 0 THEN 'current'
                    WHEN %s - COALESCE(aml.date_maturity, aml.date) BETWEEN 1 AND 30 THEN '1_30'
                    WHEN %s - COALESCE(aml.date_maturity, aml.date) BETWEEN 31 AND 60 THEN '31_60'
                    WHEN %s - COALESCE(aml.date_maturity, aml.date) BETWEEN 61 AND 90 THEN '61_90'
                    ELSE '90_plus'
                END AS bucket,
                COALESCE(SUM(ABS(aml.amount_residual)), 0) AS total
            FROM account_move_line aml
            JOIN account_account aa ON aa.id = aml.account_id
            WHERE aa.account_type = %s
              AND aml.parent_state = 'posted'
              AND aml.reconciled IS NOT TRUE
              AND aml.amount_residual != 0
              AND aml.company_id = ANY(%s)
            GROUP BY bucket
        """, (today, today, today, today, account_type, company_ids))
        rows = self.env.cr.dictfetchall()
        bucket_map = {r['bucket']: r['total'] for r in rows}

        return {
            'type': a_type,
            'labels': ['Current', '1-30', '31-60', '61-90', '90+'],
            'data': [
                bucket_map.get('current', 0),
                bucket_map.get('1_30', 0),
                bucket_map.get('31_60', 0),
                bucket_map.get('61_90', 0),
                bucket_map.get('90_plus', 0),
            ],
        }

    @api.model
    def get_dashboard_top_expenses(self, params):
        """Top expenses by category. Access: group_account_readonly+"""
        self._dashboard_check_group(['account.group_account_readonly', 'account.group_account_manager'])

        company_ids = self._dashboard_company_ids(params.get('company_ids'))
        period = params.get('period', 'this_month')
        date_from, date_to = self._dashboard_get_period(
            period, params.get('date_from'), params.get('date_to')
        )
        limit = params.get('limit', 10)

        lang = self.env.lang or 'en_US'
        self.env.cr.execute("""
            SELECT
                COALESCE(aa.name->>%(lang)s, aa.name->>'en_US', aa.name::text, 'Unknown') AS account_name,
                COALESCE(SUM(ABS(aml.balance)), 0) AS total
            FROM account_move_line aml
            JOIN account_account aa ON aa.id = aml.account_id
            JOIN account_move am ON am.id = aml.move_id
            WHERE aa.account_type = 'expense'
              AND am.state = 'posted'
              AND am.date BETWEEN %(date_from)s AND %(date_to)s
              AND aml.company_id = ANY(%(company_ids)s)
            GROUP BY aa.name
            ORDER BY total DESC
            LIMIT %(limit)s
        """, {'lang': lang, 'date_from': date_from, 'date_to': date_to,
              'company_ids': company_ids, 'limit': limit})

        rows = self.env.cr.dictfetchall()
        return {
            'labels': [r['account_name'] or 'Unknown' for r in rows],
            'data': [r['total'] for r in rows],
        }

    @api.model
    def get_dashboard_tax_summary(self, params):
        """Tax summary. Access: group_account_readonly+"""
        self._dashboard_check_group(['account.group_account_readonly', 'account.group_account_manager'])

        company_ids = self._dashboard_company_ids(params.get('company_ids'))
        period = params.get('period', 'this_month')
        date_from, date_to = self._dashboard_get_period(
            period, params.get('date_from'), params.get('date_to')
        )

        self.env.cr.execute("""
            SELECT
                CASE WHEN am.move_type IN ('out_invoice', 'out_refund') THEN 'collected'
                     ELSE 'paid' END AS direction,
                COALESCE(SUM(ABS(aml.balance)), 0) AS total
            FROM account_move_line aml
            JOIN account_move am ON am.id = aml.move_id
            JOIN account_account aa ON aa.id = aml.account_id
            WHERE aa.account_type IN ('liability_current', 'asset_current')
              AND aml.tax_line_id IS NOT NULL
              AND am.state = 'posted'
              AND am.date BETWEEN %s AND %s
              AND aml.company_id = ANY(%s)
            GROUP BY direction
        """, (date_from, date_to, company_ids))
        rows = self.env.cr.dictfetchall()
        tax_map = {r['direction']: r['total'] for r in rows}

        return {
            'collected': tax_map.get('collected', 0),
            'paid': tax_map.get('paid', 0),
            'net': tax_map.get('collected', 0) - tax_map.get('paid', 0),
        }

    # -------------------------------------------------------------------------
    # LIST DATA
    # -------------------------------------------------------------------------

    @api.model
    def get_dashboard_lists(self, params):
        """Get overdue invoices, upcoming bills, recent payments. Access: group_account_invoice+"""
        self._dashboard_check_group(['account.group_account_invoice', 'account.group_account_readonly', 'account.group_account_user'])

        company_ids = self._dashboard_company_ids(params.get('company_ids'))
        limit = params.get('limit', 10)
        today = fields.Date.context_today(self)
        result = {}

        self.env.cr.execute("""
            SELECT am.id, am.name,
                   rp.name AS partner_name,
                   am.amount_residual_signed AS amount,
                   am.invoice_date_due,
                   (%s - am.invoice_date_due) AS days_overdue
            FROM account_move am
            LEFT JOIN res_partner rp ON rp.id = am.partner_id
            WHERE am.state = 'posted'
              AND am.move_type = 'out_invoice'
              AND am.payment_state IN ('not_paid', 'partial')
              AND am.invoice_date_due < %s
              AND am.company_id = ANY(%s)
            ORDER BY days_overdue DESC LIMIT %s
        """, (today, today, company_ids, limit))
        result['overdue_invoices'] = self.env.cr.dictfetchall()

        self.env.cr.execute("""
            SELECT am.id, am.name,
                   rp.name AS partner_name,
                   ABS(am.amount_residual_signed) AS amount,
                   am.invoice_date_due,
                   (am.invoice_date_due - %s) AS days_until_due
            FROM account_move am
            LEFT JOIN res_partner rp ON rp.id = am.partner_id
            WHERE am.state = 'posted'
              AND am.move_type = 'in_invoice'
              AND am.payment_state IN ('not_paid', 'partial')
              AND am.invoice_date_due BETWEEN %s AND %s
              AND am.company_id = ANY(%s)
            ORDER BY am.invoice_date_due ASC LIMIT %s
        """, (today, today, today + timedelta(days=7), company_ids, limit))
        result['upcoming_bills'] = self.env.cr.dictfetchall()

        lang = self.env.lang or 'en_US'
        self.env.cr.execute("""
            SELECT ap.id, am.name,
                   rp.name AS partner_name,
                   ap.amount AS amount,
                   am.date, ap.payment_type,
                   COALESCE(aj.name->>%(lang)s, aj.name->>'en_US', aj.name::text) AS journal_name
            FROM account_payment ap
            JOIN account_move am ON am.id = ap.move_id
            LEFT JOIN res_partner rp ON rp.id = ap.partner_id
            LEFT JOIN account_journal aj ON aj.id = am.journal_id
            WHERE am.state = 'posted'
              AND am.company_id = ANY(%(company_ids)s)
            ORDER BY am.date DESC, ap.id DESC LIMIT %(limit)s
        """, {'lang': lang, 'company_ids': company_ids, 'limit': limit})
        result['recent_payments'] = self.env.cr.dictfetchall()

        # --- Unreconciled bank statement lines (basic+ users) ---
        if self.env.user.has_group('account.group_account_user'):
            lang = self.env.lang or 'en_US'
            self.env.cr.execute("""
                SELECT absl.id,
                       absl.payment_ref AS name,
                       rp.name AS partner_name,
                       absl.amount,
                       am.date,
                       COALESCE(aj.name->>%(lang)s, aj.name->>'en_US', aj.name::text) AS journal_name
                FROM account_bank_statement_line absl
                JOIN account_move am ON am.id = absl.move_id
                LEFT JOIN res_partner rp ON rp.id = absl.partner_id
                LEFT JOIN account_journal aj ON aj.id = am.journal_id
                WHERE NOT absl.is_reconciled
                  AND am.company_id = ANY(%(company_ids)s)
                ORDER BY am.date DESC LIMIT %(limit)s
            """, {'lang': lang, 'company_ids': company_ids, 'limit': limit})
            result['unreconciled_items'] = self.env.cr.dictfetchall()

        return result

    # -------------------------------------------------------------------------
    # ALERTS
    # -------------------------------------------------------------------------

    @api.model
    def get_account_journal_ids(self, params):
        """ Get default journal Ids """
        return self.env["account.journal"].search([
            ("type", "in", ["bank", "cash"])
        ]).mapped("default_account_id").ids

    @api.model
    def get_dashboard_alerts(self, params):
        """Smart alerts feed. Access: group_account_invoice+"""
        self._dashboard_check_group(['account.group_account_invoice', 'account.group_account_readonly', 'account.group_account_user'])

        company_ids = self._dashboard_company_ids(params.get('company_ids'))
        today = fields.Date.context_today(self)
        alerts = []
        self.env.cr.execute("""
            SELECT COUNT(*), COALESCE(SUM(amount_residual_signed), 0)
            FROM account_move
            WHERE state = 'posted'
              AND move_type = 'out_invoice'
              AND payment_state IN ('not_paid', 'partial')
              AND invoice_date_due < %s
              AND company_id = ANY(%s)
        """, (today - timedelta(days=30), company_ids))
        cnt, amt = self.env.cr.fetchone()
        if cnt:
            alerts.append({
                'type': 'danger',
                'icon': 'fa-exclamation-triangle',
                'title': _('%d invoices overdue by 30+ days') % cnt,
                'subtitle': _('Total: %s') % self.env.company.currency_id.symbol + f' {amt:,.2f}',
                'action': 'overdue_invoices',
            })

        if self.env.user.has_group('account.group_account_user'):
            unrec = self.env['account.bank.statement.line'].search_count([
                ('is_reconciled', '=', False),
                ('company_id', 'in', company_ids)
            ])
            if unrec:
                alerts.append({
                    'type': 'warning',
                    'icon': 'fa-university',
                    'title': _('%d unreconciled bank statement lines') % unrec,
                    'subtitle': _('Pending reconciliation'),
                    'action': 'reconcile',
                })

        self.env.cr.execute("""
            SELECT COUNT(*)
            FROM account_move
            WHERE state = 'posted'
              AND move_type = 'in_invoice'
              AND payment_state IN ('not_paid', 'partial')
              AND invoice_date_due = %s
              AND company_id = ANY(%s)
        """, (today, company_ids))
        due_today = self.env.cr.fetchone()[0]
        if due_today:
            alerts.append({
                'type': 'info',
                'icon': 'fa-calendar',
                'title': _('%d bills due today') % due_today,
                'subtitle': _('Review and schedule payments'),
                'action': 'bills_due_today',
            })

        self.env.cr.execute("""
            SELECT COUNT(*)
            FROM account_move
            WHERE state = 'draft'
              AND move_type IN ('out_invoice', 'in_invoice')
              AND company_id = ANY(%s)
        """, (company_ids,))
        drafts = self.env.cr.fetchone()[0]
        if drafts:
            alerts.append({
                'type': 'info',
                'icon': 'fa-file-text-o',
                'title': _('%d draft invoices/bills') % drafts,
                'subtitle': _('Awaiting confirmation'),
                'action': 'draft_moves',
            })

        return alerts

    def compute_period_dates(self, period):
        """
        Returns dict:
        {
            'date_from': 'YYYY-MM-DD',
            'date_to': 'YYYY-MM-DD'
        }
        """

        today = date.today()
        year = today.year
        month = today.month  # 1-12

        date_from = None
        date_to = None

        def end_of_month(y, m):
            """m = 1 to 12"""
            if m == 12:
                return date(y, 12, 31)
            return date(y, m + 1, 1) - timedelta(days=1)

        if period == "this_month":
            date_from = date(year, month, 1)
            date_to = today

        elif period == "last_month":
            if month == 1:
                y = year - 1
                m = 12
            else:
                y = year
                m = month - 1

            date_from = date(y, m, 1)
            date_to = end_of_month(y, m)

        elif period == "this_quarter":
            quarter_start_month = ((month - 1) // 3) * 3 + 1
            date_from = date(year, quarter_start_month, 1)
            date_to = today

        elif period == "last_quarter":
            quarter_start_month = ((month - 1) // 3) * 3 + 1

            # previous day of current quarter start = last quarter end
            last_quarter_end = date(year, quarter_start_month, 1) - timedelta(days=1)

            last_q_month = ((last_quarter_end.month - 1) // 3) * 3 + 1
            date_from = date(last_quarter_end.year, last_q_month, 1)
            date_to = last_quarter_end

        elif period == "this_year":
            date_from = date(year, 1, 1)
            date_to = today

        elif period == "last_year":
            date_from = date(year - 1, 1, 1)
            date_to = date(year - 1, 12, 31)

        return {
            "date_from": date_from.isoformat() if date_from else None,
            "date_to": date_to.isoformat() if date_to else None,
        }


    # ------------------------------------------------------------------
    # P&L Trend (12 months) — Revenue, Expenses, Net Profit lines
    # ------------------------------------------------------------------
    @api.model
    def get_dashboard_profit_trend(self, params):
        """Monthly P&L trend for the last 12 months. Access: group_account_readonly+"""
        self._dashboard_check_group('account.group_account_readonly')
        company_ids = self._dashboard_company_ids(params.get('company_ids'))
        today = fields.Date.context_today(self)
        date_from = today - relativedelta(months=11, day=1)
        self.env.cr.execute("""
            SELECT
                to_char(date, 'YYYY-MM') AS month,
                move_type,
                COALESCE(SUM(amount_untaxed_signed), 0) AS total
            FROM account_move
            WHERE state = 'posted'
              AND move_type IN ('out_invoice', 'out_refund', 'in_invoice', 'in_refund')
              AND date >= %s
              AND company_id = ANY(%s)
            GROUP BY to_char(date, 'YYYY-MM'), move_type
            ORDER BY month
        """, (date_from, company_ids))
        rows = self.env.cr.dictfetchall()

        months = []
        d = date_from
        while d <= today:
            months.append(d.strftime('%Y-%m'))
            d += relativedelta(months=1)

        revenue_map = {}
        expense_map = {}
        for r in rows:
            m = r['month']
            if r['move_type'] in ('out_invoice', 'out_refund'):
                revenue_map[m] = revenue_map.get(m, 0) + r['total']
            elif r['move_type'] in ('in_invoice', 'in_refund'):
                expense_map[m] = expense_map.get(m, 0) + abs(r['total'])

        revenue = [revenue_map.get(m, 0) for m in months]
        expenses = [expense_map.get(m, 0) for m in months]
        net_profit = [r - e for r, e in zip(revenue, expenses)]

        return {
            'labels': months,
            'revenue': revenue,
            'expenses': expenses,
            'net_profit': net_profit,
        }

    # ------------------------------------------------------------------
    # Expense Breakdown — by account group (doughnut)
    # ------------------------------------------------------------------
    @api.model
    def get_dashboard_expense_breakdown(self, params):
        """Expense breakdown by account. Access: group_account_readonly+"""
        self._dashboard_check_group('account.group_account_readonly')
        company_ids = self._dashboard_company_ids(params.get('company_ids'))
        period = params.get('period', 'this_month')
        date_from, date_to = self._dashboard_get_period(
            period, params.get('date_from'), params.get('date_to'))

        lang = self.env.lang or 'en_US'
        self.env.cr.execute("""
            SELECT
                COALESCE(aa.name->>%(lang)s, aa.name->>'en_US', aa.name::text, 'Other') AS account_name,
                COALESCE(SUM(ABS(aml.balance)), 0) AS total
            FROM account_move_line aml
            JOIN account_move am ON am.id = aml.move_id
            JOIN account_account aa ON aa.id = aml.account_id
            WHERE am.state = 'posted'
              AND am.move_type IN ('in_invoice', 'in_refund')
              AND am.date BETWEEN %(date_from)s AND %(date_to)s
              AND am.company_id = ANY(%(company_ids)s)
              AND aml.display_type = 'product'
            GROUP BY aa.name
            ORDER BY total DESC
            LIMIT 10
        """, {'lang': lang, 'date_from': date_from, 'date_to': date_to,
              'company_ids': company_ids})
        rows = self.env.cr.dictfetchall()

        return {
            'labels': [r['account_name'] for r in rows],
            'amounts': [r['total'] for r in rows],
        }

    # ------------------------------------------------------------------
    # Budget vs Actual — uses standard account_budget module if installed
    # ------------------------------------------------------------------
    @api.model
    def get_dashboard_budget_vs_actual(self, params):
        """Budget vs actual for confirmed budgets. Access: group_account_readonly+"""
        self._dashboard_check_group('account.group_account_readonly')
        company_ids = self._dashboard_company_ids(params.get('company_ids'))

        # Check if the budget module is installed
        if 'budget.analytic' not in self.env:
            return {'available': False, 'labels': [], 'budgeted': [], 'actual': []}

        today = fields.Date.context_today(self)
        BudgetLine = self.env['budget.line']
        lines = BudgetLine.search([
            ('budget_analytic_id.state', 'in', ['confirmed', 'done']),
            ('budget_analytic_id.company_id', 'in', company_ids),
            ('date_from', '<=', today),
            ('date_to', '>=', today),
        ], limit=20, order='budget_amount DESC')

        if not lines:
            return {'available': True, 'labels': [], 'budgeted': [], 'actual': []}

        labels = []
        budgeted = []
        actual = []
        for line in lines:
            label = line.budget_analytic_id.name
            if len(label) > 25:
                label = label[:22] + '...'
            labels.append(label)
            budgeted.append(line.budget_amount)
            actual.append(line.achieved_amount)

        return {
            'available': True,
            'labels': labels,
            'budgeted': budgeted,
            'actual': actual,
        }

    # ------------------------------------------------------------------
    # Monthly Cash Inflow/Outflow — stacked bar from payments
    # ------------------------------------------------------------------
    @api.model
    def get_dashboard_monthly_cashflow_bars(self, params):
        """Monthly cash inflows vs outflows from payments. Access: group_account_readonly+"""
        self._dashboard_check_group('account.group_account_readonly')
        company_ids = self._dashboard_company_ids(params.get('company_ids'))
        today = fields.Date.context_today(self)
        date_from = today - relativedelta(months=11, day=1)

        self.env.cr.execute("""
            SELECT
                to_char(am.date, 'YYYY-MM') AS month,
                ap.payment_type,
                COALESCE(SUM(ap.amount), 0) AS total
            FROM account_payment ap
            JOIN account_move am ON am.id = ap.move_id
            WHERE am.state = 'posted'
              AND am.date >= %s
              AND am.company_id = ANY(%s)
            GROUP BY to_char(am.date, 'YYYY-MM'), ap.payment_type
            ORDER BY month
        """, (date_from, company_ids))
        rows = self.env.cr.dictfetchall()

        months = []
        d = date_from
        while d <= today:
            months.append(d.strftime('%Y-%m'))
            d += relativedelta(months=1)

        inflow_map = {r['month']: r['total'] for r in rows if r['payment_type'] == 'inbound'}
        outflow_map = {r['month']: r['total'] for r in rows if r['payment_type'] == 'outbound'}

        return {
            'labels': months,
            'inflows': [inflow_map.get(m, 0) for m in months],
            'outflows': [outflow_map.get(m, 0) for m in months],
        }

    # ------------------------------------------------------------------
    # Cashflow Waterfall — Opening → Inflows → Outflows → Closing
    # ------------------------------------------------------------------
    @api.model
    def get_dashboard_cashflow_waterfall(self, params):
        """Cashflow waterfall for the selected period."""
        self._dashboard_check_group('account.group_account_readonly')
        company_ids = self._dashboard_company_ids(params.get('company_ids'))
        period = params.get('period', 'this_month')
        date_from, date_to = self._dashboard_get_period(
            period, params.get('date_from'), params.get('date_to'))

        # Opening cash balance (cash journal balances up to day before date_from)
        opening_date = date_from - relativedelta(days=1)
        self.env.cr.execute("""
            SELECT COALESCE(SUM(aml.balance), 0)
            FROM account_move_line aml
            JOIN account_journal aj ON aj.default_account_id = aml.account_id
            JOIN account_move am ON am.id = aml.move_id
            WHERE aj.type IN ('bank', 'cash')
              AND aml.parent_state = 'posted'
              AND am.date <= %s
              AND aml.company_id = ANY(%s)
        """, (opening_date, company_ids))
        opening = self.env.cr.fetchone()[0]

        # Inflows in period (inbound payments)
        self.env.cr.execute("""
            SELECT COALESCE(SUM(ap.amount), 0)
            FROM account_payment ap
            JOIN account_move am ON am.id = ap.move_id
            WHERE am.state = 'posted'
              AND ap.payment_type = 'inbound'
              AND am.date BETWEEN %s AND %s
              AND am.company_id = ANY(%s)
        """, (date_from, date_to, company_ids))
        inflows = self.env.cr.fetchone()[0]

        # Outflows in period (outbound payments)
        self.env.cr.execute("""
            SELECT COALESCE(SUM(ap.amount), 0)
            FROM account_payment ap
            JOIN account_move am ON am.id = ap.move_id
            WHERE am.state = 'posted'
              AND ap.payment_type = 'outbound'
              AND am.date BETWEEN %s AND %s
              AND am.company_id = ANY(%s)
        """, (date_from, date_to, company_ids))
        outflows = self.env.cr.fetchone()[0]

        closing = opening + inflows - outflows

        return {
            'labels': ['Opening', 'Cash In', 'Cash Out', 'Closing'],
            'values': [opening, inflows, -outflows, closing],
            'types': ['total', 'increase', 'decrease', 'total'],
        }

    # ------------------------------------------------------------------
    # Dynamic Bank / Cash Journal Balances
    # ------------------------------------------------------------------
    @api.model
    def get_dashboard_journal_balances(self, params):
        """Return monthly balance for each bank/cash journal."""
        self._dashboard_check_group(['account.group_account_user', 'account.group_account_readonly'])
        company_ids = self._dashboard_company_ids(params.get('company_ids'))
        today = fields.Date.context_today(self)

        # Discover all bank/cash journals for the companies
        journals = self.env['account.journal'].search([
            ('type', 'in', ['bank', 'cash']),
            ('company_id', 'in', company_ids),
        ], order='type, name')

        if not journals:
            return []

        # 12-month range
        date_from = today - relativedelta(months=11, day=1)
        months = []
        d = date_from
        while d <= today:
            months.append(d.strftime('%Y-%m'))
            d += relativedelta(months=1)

        result = []
        for journal in journals:
            if not journal.default_account_id:
                continue
            account_id = journal.default_account_id.id

            # Monthly cumulative balance
            self.env.cr.execute("""
                SELECT to_char(am.date, 'YYYY-MM') AS month,
                       COALESCE(SUM(aml.balance), 0) AS total
                FROM account_move_line aml
                JOIN account_move am ON am.id = aml.move_id
                WHERE aml.account_id = %s
                  AND aml.parent_state = 'posted'
                  AND am.date >= %s
                  AND aml.company_id = %s
                GROUP BY to_char(am.date, 'YYYY-MM')
                ORDER BY month
            """, (account_id, date_from, journal.company_id.id))
            month_rows = {r['month']: r['total'] for r in self.env.cr.dictfetchall()}

            # Opening balance (before date_from)
            self.env.cr.execute("""
                SELECT COALESCE(SUM(aml.balance), 0)
                FROM account_move_line aml
                JOIN account_move am ON am.id = aml.move_id
                WHERE aml.account_id = %s
                  AND aml.parent_state = 'posted'
                  AND am.date < %s
                  AND aml.company_id = %s
            """, (account_id, date_from, journal.company_id.id))
            opening = self.env.cr.fetchone()[0]

            # Build running balance
            balances = []
            running = opening
            for m in months:
                running += month_rows.get(m, 0)
                balances.append(round(running, 2))
            journal_name = journal.name
            if isinstance(journal_name, dict):
                journal_name = journal_name.get('en_US', journal_name.get('en', str(journal.id)))
            result.append({
                'journal_id': journal.id,
                'journal_name': journal_name,
                'journal_type': journal.type,
                'currency': journal.currency_id.symbol or journal.company_id.currency_id.symbol,
                'labels': months,
                'balances': balances,
                'current_balance': balances[-1] if balances else 0,
            })
        return result
