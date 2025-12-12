# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2022-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
import time
from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta

import io
import json
from odoo.http import request
from odoo.exceptions import AccessError, UserError, AccessDenied

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class TrialView(models.TransientModel):
    _inherit = "account.report"
    _name = 'account.trial.balance'

    journal_ids = fields.Many2many('account.journal',

                                   string='Journals', required=True,
                                   default=[])
    display_account = fields.Selection(
        [('all', 'All'), ('movement', 'With movements'),
         ('not_zero', 'With balance is not equal to 0')],
        string='Display Accounts', required=True, default='movement')
    comparison_years = fields.Integer(string='Compare Prior Years', help='Number of prior years to include (1 = previous year only, 2 = last 2 years, etc.)')
    comparison_months = fields.Integer(string='Compare Prior Months', help='Number of prior months to include (1 = previous month only, 2 = last 2 months, etc.)')

    @api.model
    def view_report(self, option):
        r = self.env['account.trial.balance'].search([('id', '=', option[0])])

        data = {
            'display_account': r.display_account,
            'model': self,
            'journals': r.journal_ids,
            'target_move': r.target_move,
            'comparison_years': r.comparison_years,
            'comparison_months': r.comparison_months,

        }
        if r.date_from:
            data.update({
                'date_from':r.date_from,
            })
        if r.date_to:
            data.update({
                'date_to':r.date_to,
            })

        filters = self.get_filter(option)
        records = self._get_report_values(data)
        currency = self._get_currency()

        return {
            'name': "Trial Balance",
            'type': 'ir.actions.client',
            'tag': 't_b',
            'filters': filters,
            'report_lines': records['Accounts'],
            'debit_total': records['debit_total'],
            'credit_total': records['credit_total'],
            'debit_prev_totals': records.get('debit_prev_totals'),
            'credit_prev_totals': records.get('credit_prev_totals'),
            'debit_month_totals': records.get('debit_month_totals'),
            'credit_month_totals': records.get('credit_month_totals'),
            'comparison_year_labels': self._get_comparison_year_labels(data),
            'comparison_month_labels': self._get_comparison_month_labels(data),
            'currency': currency,
        }

    def get_filter(self, option):
        data = self.get_filter_data(option)
        filters = {}
        if data.get('journal_ids'):
            filters['journals'] = self.env['account.journal'].browse(data.get('journal_ids')).mapped('code')
        else:
            filters['journals'] = ['All']
        if data.get('target_move'):
            filters['target_move'] = data.get('target_move')
        if data.get('date_from'):
            filters['date_from'] = data.get('date_from')
        if data.get('date_to'):
            filters['date_to'] = data.get('date_to')
        if data.get('comparison_years'):
            filters['comparison_years'] = data.get('comparison_years')
        if data.get('comparison_months'):
            filters['comparison_months'] = data.get('comparison_months')

        filters['company_id'] = ''
        filters['journals_list'] = data.get('journals_list')
        filters['company_name'] = data.get('company_name')
        filters['target_move'] = data.get('target_move').capitalize()

        return filters

    def _get_comparison_year_labels(self, data):
        """Generate actual year labels for comparison columns"""
        year_labels = []
        if data.get('comparison_years') and data.get('comparison_years') > 0:
            current_date = fields.Date.today()
            current_year = current_date.year
            for i in range(1, data.get('comparison_years') + 1):
                year_labels.append(str(current_year - i))
        return year_labels

    def _get_comparison_month_labels(self, data):
        """Generate actual month names for comparison columns"""
        month_labels = []
        if data.get('comparison_months') and data.get('comparison_months') > 0:
            current_date = fields.Date.today()
            for i in range(1, data.get('comparison_months') + 1):
                # Calculate the month by going back i months from current date
                comparison_date = current_date - relativedelta(months=i)
                # Get month name (e.g., "November", "October")
                month_name = comparison_date.strftime("%B")
                month_labels.append(month_name)
        return month_labels

    def get_current_company_value(self):

        cookies_cids = [int(r) for r in request.httprequest.cookies.get('cids').split(",")] \
            if request.httprequest.cookies.get('cids') \
            else [request.env.user.company_id.id]
        for company_id in cookies_cids:
            if company_id not in self.env.user.company_ids.ids:
                cookies_cids.remove(company_id)
        if not cookies_cids:
            cookies_cids = [self.env.company.id]
        if len(cookies_cids) == 1:
            cookies_cids.append(0)
        return cookies_cids

    def get_filter_data(self, option):
        r = self.env['account.trial.balance'].search([('id', '=', option[0])])
        default_filters = {}
        company_id = self.env.companies.ids
        company_domain = [('company_id', 'in', company_id)]
        journal_ids = r.journal_ids if r.journal_ids else self.env['account.journal'].search(company_domain, order="company_id, name")


        journals = []
        o_company = False
        for j in journal_ids:
            if j.company_id != o_company:
                journals.append(('divider', j.company_id.name))
                o_company = j.company_id
            journals.append((j.id, j.name, j.code))

        filter_dict = {
            'journal_ids': r.journal_ids.ids,
            'company_id': company_id,
            'date_from': r.date_from,
            'date_to': r.date_to,
            'target_move': r.target_move,
            'comparison_years': r.comparison_years,
            'comparison_months': r.comparison_months,
            'journals_list': journals,
            # 'journals_list': [(j.id, j.name, j.code) for j in journals],

            'company_name': ', '.join(self.env.companies.mapped('name')),
        }
        filter_dict.update(default_filters)
        return filter_dict

    # def _get_report_values(self, data):
    #     docs = data['model']
    #     display_account = data['display_account']
    #     journals = data['journals']
    #     accounts = self.env['account.account'].search([])
    #     if not accounts:
    #         raise UserError(_("No Accounts Found! Please Add One"))
    #     account_res = self._get_accounts(accounts, display_account, data)
    #     debit_total = 0
    #     debit_total = sum(x['debit'] for x in account_res)
    #     credit_total = sum(x['credit'] for x in account_res)
    #     debit_prev_totals = None
    #     credit_prev_totals = None
    #     if data.get('comparison_years') and data.get('comparison_years') > 0:
    #         years = data.get('comparison_years')
    #         debit_prev_totals = []
    #         credit_prev_totals = []
    #         for i in range(1, years + 1):
    #             debit_prev_totals.append(sum(x.get('debit_prev_%d' % i, 0.0) for x in account_res))
    #             credit_prev_totals.append(sum(x.get('credit_prev_%d' % i, 0.0) for x in account_res))
    #
    #     debit_month_totals = None
    #     credit_month_totals = None
    #     if data.get('comparison_months') and data.get('comparison_months') > 0:
    #         months = data.get('comparison_months')
    #         debit_month_totals = []
    #         credit_month_totals = []
    #         for i in range(1, months + 1):
    #             debit_month_totals.append(sum(x.get('debit_month_%d' % i, 0.0) for x in account_res))
    #             credit_month_totals.append(sum(x.get('credit_month_%d' % i, 0.0) for x in account_res))
    #
    #
    #
    #     return {
    #         'doc_ids': self.ids,
    #         'debit_total': debit_total,
    #         'credit_total': credit_total,
    #         'debit_prev_totals': debit_prev_totals,
    #         'credit_prev_totals': credit_prev_totals,
    #         'debit_month_totals': debit_month_totals,
    #         'credit_month_totals': credit_month_totals,
    #         'docs': docs,
    #         'time': time,
    #         'Accounts': account_res,
    #     }
    def _get_report_values(self, data):
        docs = data['model']
        display_account = data['display_account']
        journals = data['journals']
        accounts = self.env['account.account'].search([])
        if not accounts:
            raise UserError(_("No Accounts Found! Please Add One"))
        account_res = self._get_accounts(accounts, display_account, data)

        debit_total = sum(x['debit'] for x in account_res)
        credit_total = sum(x['credit'] for x in account_res)

        # Previous Year totals
        debit_prev_totals = []
        credit_prev_totals = []
        comparison_years = data.get('comparison_years', 0)
        if comparison_years > 0:
            for i in range(1, comparison_years + 1):
                debit_prev_totals.append(sum(x.get(f'debit_prev_{i}', 0.0) for x in account_res))
                credit_prev_totals.append(sum(x.get(f'credit_prev_{i}', 0.0) for x in account_res))

        # Previous Month totals
        debit_month_totals = []
        credit_month_totals = []
        comparison_months = data.get('comparison_months', 0)
        if comparison_months > 0:
            for i in range(1, comparison_months + 1):
                debit_month_totals.append(sum(x.get(f'debit_month_{i}', 0.0) for x in account_res))
                credit_month_totals.append(sum(x.get(f'credit_month_{i}', 0.0) for x in account_res))

        # Pass Filters dictionary for QWeb template
        filters = {
            'comparison_years': comparison_years,
            'comparison_months': comparison_months,
            'comparison_year_labels': self._get_comparison_year_labels(data),
            'comparison_month_labels': self._get_comparison_month_labels(data),
        }

        return {
            'doc_ids': self.ids,
            'debit_total': debit_total,
            'credit_total': credit_total,
            'debit_prev_totals': debit_prev_totals,
            'credit_prev_totals': credit_prev_totals,
            'debit_month_totals': debit_month_totals,
            'credit_month_totals': credit_month_totals,
            'docs': docs,
            'time': time,
            'Accounts': account_res,
            'Filters': filters,  # <-- this is required for PDF template
        }

    @api.model
    def create(self, vals):
        vals['target_move'] = 'posted'
        vals['name'] = 'eee'
        res = super(TrialView, self).create(vals)
        return res

    def write(self, vals):
        if vals.get('target_move'):
            vals.update({'target_move': vals.get('target_move').lower()})
        if vals.get('journal_ids'):
            vals.update({'journal_ids': [(6, 0, vals.get('journal_ids'))]})
        if vals.get('journal_ids') == []:
            vals.update({'journal_ids': [(5,)]})
        res = super(TrialView, self).write(vals)
        return res

    def _get_accounts(self, accounts, display_account, data):
        account_result = {}
        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        tables = tables.replace('"', '')
        if not tables:
            tables = 'account_move_line'
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        filters = " AND ".join(wheres)
        if data['target_move'] == 'posted':
            filters += " AND account_move_line.parent_state = 'posted'"
        else:
            filters += " AND account_move_line.parent_state in ('draft','posted')"
        if data.get('date_from'):
            filters += " AND account_move_line.date >= '%s'" % data.get('date_from')
        if data.get('date_to'):
            filters += " AND account_move_line.date <= '%s'" % data.get('date_to')

        if data['journals']:
            filters += ' AND jrnl.id IN %s' % str(tuple(data['journals'].ids) + tuple([0]))
        tables += ' JOIN account_journal jrnl ON (account_move_line.journal_id=jrnl.id)'
        # compute the balance, debit and credit for the provided accounts
        request = (
                    "SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" + \
                    " FROM " + tables + " WHERE account_id IN %s " + filters + " GROUP BY account_id")
        params = (tuple(accounts.ids),) + tuple(where_params)
        self.env.cr.execute(request, params)
        for row in self.env.cr.dictfetchall():
            account_result[row.pop('id')] = row

        # Prior years computation when requested
        prior_year_results = {}
        if data.get('comparison_years') and data.get('comparison_years') > 0:
            years = data.get('comparison_years')
            for i in range(1, years + 1):
                tables_p, where_clause_p, where_params_p = self.env['account.move.line']._query_get()
                tables_p = tables_p.replace('"', '') if tables_p else 'account_move_line'
                wheres_p = [""]
                if where_clause_p.strip():
                    wheres_p.append(where_clause_p.strip())
                filters_p = " AND ".join(wheres_p)
                if data['target_move'] == 'posted':
                    filters_p += " AND account_move_line.parent_state = 'posted'"
                else:
                    filters_p += " AND account_move_line.parent_state in ('draft','posted')"
                # Compute date range shifted by i years
                date_from_prev = data.get('date_from')
                date_to_prev = data.get('date_to')
                
                # If no date range specified, use current fiscal year dates
                if not date_from_prev and not date_to_prev:
                    current_date = fields.Date.today()
                    current_year = current_date.year
                    # Default to current fiscal year (Jan 1 to Dec 31)
                    date_from_prev = fields.Date.from_string(f"{current_year}-01-01")
                    date_to_prev = fields.Date.from_string(f"{current_year}-12-31")

                if date_from_prev:
                    date_from_prev = fields.Date.from_string(date_from_prev) - relativedelta(years=i)
                    filters_p += " AND account_move_line.date >= '%s'" % fields.Date.to_string(date_from_prev)
                if date_to_prev:
                    date_to_prev = fields.Date.from_string(date_to_prev) - relativedelta(years=i)
                    filters_p += " AND account_move_line.date <= '%s'" % fields.Date.to_string(date_to_prev)

                if data['journals']:
                    filters_p += ' AND jrnl.id IN %s' % str(tuple(data['journals'].ids) + tuple([0]))
                tables_p += ' JOIN account_journal jrnl ON (account_move_line.journal_id=jrnl.id)'
                request_p = (
                    "SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance"
                    + " FROM " + tables_p + " WHERE account_id IN %s " + filters_p + " GROUP BY account_id"
                )
                params_p = (tuple(accounts.ids),) + tuple(where_params_p)
                self.env.cr.execute(request_p, params_p)
                for row in self.env.cr.dictfetchall():
                    aid = row.pop('id')
                    if aid not in prior_year_results:
                        prior_year_results[aid] = {}
                    prior_year_results[aid]['debit_prev_%d' % i] = row.get('debit') or 0.0
                    prior_year_results[aid]['credit_prev_%d' % i] = row.get('credit') or 0.0

        # Prior months computation when requested
        prior_month_results = {}
        if data.get('comparison_months') and data.get('comparison_months') > 0:
            months = data.get('comparison_months')
            for i in range(1, months + 1):
                tables_m, where_clause_m, where_params_m = self.env['account.move.line']._query_get()
                tables_m = tables_m.replace('"', '') if tables_m else 'account_move_line'
                wheres_m = [""]
                if where_clause_m.strip():
                    wheres_m.append(where_clause_m.strip())
                filters_m = " AND ".join(wheres_m)
                if data['target_move'] == 'posted':
                    filters_m += " AND account_move_line.parent_state = 'posted'"
                else:
                    filters_m += " AND account_move_line.parent_state in ('draft','posted')"
                # Compute date range shifted by i months
                date_from_m = data.get('date_from')
                date_to_m = data.get('date_to')
                
                # If no date range specified, use current month dates
                if not date_from_m and not date_to_m:
                    current_date = fields.Date.today()
                    # Default to current month (1st to last day)
                    date_from_m = current_date.replace(day=1)
                    # Get last day of current month
                    next_month = date_from_m + relativedelta(months=1)
                    date_to_m = next_month - relativedelta(days=1)
                
                if date_from_m:
                    date_from_m = fields.Date.from_string(date_from_m) - relativedelta(months=i)
                    filters_m += " AND account_move_line.date >= '%s'" % fields.Date.to_string(date_from_m)
                if date_to_m:
                    date_to_m = fields.Date.from_string(date_to_m) - relativedelta(months=i)
                    filters_m += " AND account_move_line.date <= '%s'" % fields.Date.to_string(date_to_m)

                if data['journals']:
                    filters_m += ' AND jrnl.id IN %s' % str(tuple(data['journals'].ids) + tuple([0]))
                tables_m += ' JOIN account_journal jrnl ON (account_move_line.journal_id=jrnl.id)'
                request_m = (
                    "SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance"
                    + " FROM " + tables_m + " WHERE account_id IN %s " + filters_m + " GROUP BY account_id"
                )
                params_m = (tuple(accounts.ids),) + tuple(where_params_m)
                self.env.cr.execute(request_m, params_m)
                for row in self.env.cr.dictfetchall():
                    aid = row.pop('id')
                    if aid not in prior_month_results:
                        prior_month_results[aid] = {}
                    prior_month_results[aid]['debit_month_%d' % i] = row.get('debit') or 0.0
                    prior_month_results[aid]['credit_month_%d' % i] = row.get('credit') or 0.0

        account_res = []
        for account in accounts:
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
            res['code'] = account.code
            res['name'] = account.name
            res['id'] = account.id
            if data.get('date_from'):

                res['Init_balance'] = self.get_init_bal(account, display_account, data)

            if account.id in account_result:
                res['debit'] = account_result[account.id].get('debit')
                res['credit'] = account_result[account.id].get('credit')
                res['balance'] = account_result[account.id].get('balance')
            if account.id in prior_year_results:
                res.update(prior_year_results[account.id])
            if account.id in prior_month_results:
                res.update(prior_month_results[account.id])
            if display_account == 'all':
                account_res.append(res)
            if display_account == 'not_zero' and not currency.is_zero(
                    res['balance']):
                account_res.append(res)
            if display_account == 'movement' and (
                    not currency.is_zero(res['debit']) or not currency.is_zero(
                    res['credit'])):
                account_res.append(res)
        return account_res

    def get_init_bal(self, account, display_account, data):
        if data.get('date_from'):

            tables, where_clause, where_params = self.env[
                'account.move.line']._query_get()
            tables = tables.replace('"', '')
            if not tables:
                tables = 'account_move_line'
            wheres = [""]
            if where_clause.strip():
                wheres.append(where_clause.strip())
            filters = " AND ".join(wheres)
            if data['target_move'] == 'posted':
                filters += " AND account_move_line.parent_state = 'posted'"
            else:
                filters += " AND account_move_line.parent_state in ('draft','posted')"
            if data.get('date_from'):
                filters += " AND account_move_line.date < '%s'" % data.get('date_from')

            if data['journals']:
                filters += ' AND jrnl.id IN %s' % str(tuple(data['journals'].ids) + tuple([0]))
            tables += ' JOIN account_journal jrnl ON (account_move_line.journal_id=jrnl.id)'

            # compute the balance, debit and credit for the provided accounts
            request = (
                    "SELECT account_id AS id, SUM(debit) AS debit, SUM(credit) AS credit, (SUM(debit) - SUM(credit)) AS balance" + \
                    " FROM " + tables + " WHERE account_id = %s" % account.id + filters + " GROUP BY account_id")
            params = tuple(where_params)
            self.env.cr.execute(request, params)
            for row in self.env.cr.dictfetchall():
                return row

    @api.model
    def _get_currency(self):
        journal = self.env['account.journal'].browse(
            self.env.context.get('default_journal_id', False))
        if journal.currency_id:
            return journal.currency_id.id
        lang = self.env.user.lang
        if not lang:
            lang = 'en_US'
        lang = lang.replace("_", '-')

        currency_array = [self.env.company.currency_id.symbol,
                          self.env.company.currency_id.position,
                          lang,self.env.company.currency_id.decimal_places]
        return currency_array

    def get_dynamic_xlsx_report(self, data, response ,report_data, dfr_data):
        report_data_main = json.loads(report_data)
        output = io.BytesIO()
        total = json.loads(dfr_data)
        filters = json.loads(data)
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        head = workbook.add_format({'align': 'center', 'bold': True,
                                    'font_size': '20px'})
        sub_heading = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px',
             'border': 1,
             'border_color': 'black'})
        txt = workbook.add_format({'font_size': '10px', 'border': 1})
        txt_l = workbook.add_format({'font_size': '10px', 'border': 1, 'bold': True})
        sheet.merge_range('A2:D3', filters.get('company_name') + ':' + ' Trial Balance', head)
        date_head = workbook.add_format({'align': 'center', 'bold': True,
                                         'font_size': '10px'})
        date_style = workbook.add_format({'align': 'center',
                                          'font_size': '10px'})
        if filters.get('date_from'):
            sheet.merge_range('A4:B4', 'From:4:D4', 'To: '+ filters.get('date_to'), date_head)
        sheet.merge_range('A5:D6', 'Journals: ' + ', '.join([ lt or '' for lt in filters['journals'] ]) + '  Target Moves: '+ filters.get('target_move'), date_head)
        
        # Set up headers dynamically based on comparison settings
        col_headers = ['Code', 'Account']
        if filters.get('date_from'):
            col_headers.extend(['Initial Debit', 'Initial Credit'])
        
        # Add prior year headers
        if filters.get('comparison_years') and filters.get('comparison_years') > 0:
            current_date = fields.Date.today()
            current_year = current_date.year
            for i in range(1, filters.get('comparison_years') + 1):
                year_label = str(current_year - i)
                col_headers.extend([f'Debit {year_label}', f'Credit {year_label}'])

        # Add prior month headers
        if filters.get('comparison_months') and filters.get('comparison_months') > 0:
            month_labels = self._get_comparison_month_labels(filters)
            for i, month_label in enumerate(month_labels, 1):
                col_headers.extend([f'Debit {month_label}', f'Credit {month_label}'])

        # Add current period headers
        col_headers.extend(['Debit', 'Credit'])
        
        # Write headers
        row = 6
        for col_idx, header in enumerate(col_headers):
            sheet.write(row, col_idx, header, sub_heading)
        
        # Set column widths
        for i in range(len(col_headers)):
            sheet.set_column(i, i, 15)
        sheet.set_column(0, 0, 15)  # Code column
        sheet.set_column(1, 1, 30)  # Account name column wider

        row = 6
        col = 0
        
        for rec_data in report_data_main:
            row += 1
            col = 0
            sheet.write(row, col, rec_data['code'], txt)
            sheet.write(row, col + 1, rec_data['name'], txt)
            col += 2
            
            if filters.get('date_from'):
                if rec_data.get('Init_balance'):
                    sheet.write(row, col, rec_data['Init_balance']['debit'], txt)
                    sheet.write(row, col + 1, rec_data['Init_balance']['credit'], txt)
                else:
                    sheet.write(row, col, 0, txt)
                    sheet.write(row, col + 1, 0, txt)
                col += 2
            
            # Add prior year data
            if filters.get('comparison_years') and filters.get('comparison_years') > 0:
                for i in range(1, filters.get('comparison_years') + 1):
                    sheet.write(row, col, rec_data.get('debit_prev_%d' % i, 0.0), txt)
                    sheet.write(row, col + 1, rec_data.get('credit_prev_%d' % i, 0.0), txt)
                    col += 2
            
            # Add prior month data
            if filters.get('comparison_months') and filters.get('comparison_months') > 0:
                for i in range(1, filters.get('comparison_months') + 1):
                    sheet.write(row, col, rec_data.get('debit_month_%d' % i, 0.0), txt)
                    sheet.write(row, col + 1, rec_data.get('credit_month_%d' % i, 0.0), txt)
                    col += 2
            
            # Add current period data
            sheet.write(row, col, rec_data['debit'], txt)
            sheet.write(row, col + 1, rec_data['credit'], txt)
        
        # Write totals
        row += 1
        col = 0
        sheet.write(row, col, 'Total', txt_l)
        col += 1
        sheet.write(row, col, '', txt_l)  # Empty cell for Account column to maintain alignment
        col += 1
        
        if filters.get('date_from'):
            col += 2  # Skip initial balance columns
        
        # Add prior year totals
        if filters.get('comparison_years') and filters.get('comparison_years') > 0:
            debit_prev_totals = total.get('debit_prev_totals', [])
            credit_prev_totals = total.get('credit_prev_totals', [])
            for i in range(1, filters.get('comparison_years') + 1):
                sheet.write(row, col, 
                           debit_prev_totals[i-1] if debit_prev_totals and len(debit_prev_totals) >= i else 0.0, txt_l)
                sheet.write(row, col + 1, 
                           credit_prev_totals[i-1] if credit_prev_totals and len(credit_prev_totals) >= i else 0.0, txt_l)
                col += 2
        
        # Add prior month totals
        if filters.get('comparison_months') and filters.get('comparison_months') > 0:
            debit_month_totals = total.get('debit_month_totals', [])
            credit_month_totals = total.get('credit_month_totals', [])
            for i in range(1, filters.get('comparison_months') + 1):
                sheet.write(row, col, 
                           debit_month_totals[i-1] if debit_month_totals and len(debit_month_totals) >= i else 0.0, txt_l)
                sheet.write(row, col + 1, 
                           credit_month_totals[i-1] if credit_month_totals and len(credit_month_totals) >= i else 0.0, txt_l)
                col += 2
        
        # Add current period totals
        sheet.write(row, col, total.get('debit_total'), txt_l)
        sheet.write(row, col + 1, total.get('credit_total'), txt_l)

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
