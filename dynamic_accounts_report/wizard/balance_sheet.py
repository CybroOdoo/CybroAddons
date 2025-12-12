import time
from odoo import fields, models, api, _
from dateutil.relativedelta import relativedelta

import io
import json
from odoo.exceptions import AccessError, UserError, AccessDenied

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class BalanceSheetView(models.TransientModel):
    _name = 'dynamic.balance.sheet.report'

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

    company_id = fields.Many2one('res.company', required=True,
                                 default=lambda self: self.env.company)
    journal_ids = fields.Many2many('account.journal',
                                   string='Journals', required=True,
                                   default=[])
    account_ids = fields.Many2many("account.account", string="Accounts")
    account_tag_ids = fields.Many2many("account.account.tag",
                                       string="Account Tags")
    analytic_ids = fields.Many2many(
        "account.analytic.account", string="Analytic Accounts")
    # analytic_tag_ids = fields.Many2many("account.analytic.tag",
    #                                     string="Analytic Tags")
    display_account = fields.Selection(
        [('all', 'All'), ('movement', 'With movements'),
         ('not_zero', 'With balance is not equal to 0')],
        string='Display Accounts', required=True, default='movement')
    target_move = fields.Selection(
        [('all', 'All'), ('posted', 'Posted')],
        string='Target Move', required=True, default='posted')
    date_from = fields.Date(string="Start date")
    date_to = fields.Date(string="End date")
    comparison_years = fields.Integer(string='Compare Prior Years', help='Number of prior years to include (1 = previous year only, 2 = last 2 years, etc.)')
    comparison_months = fields.Integer(string='Compare Prior Months', help='Number of prior months to include (1 = previous month only, 2 = last 2 months, etc.)')

    @api.model
    def view_report(self, option, tag, lang):
        r = self.env['dynamic.balance.sheet.report'].search(
            [('id', '=', option[0])])
        data = {
            'display_account': r.display_account,
            'model': self,
            'journals': r.journal_ids,
            'target_move': r.target_move,
            'accounts': r.account_ids,
            'account_tags': r.account_tag_ids,
            'analytics': r.analytic_ids,
            'comparison_years': r.comparison_years,
            'comparison_months': r.comparison_months,
        }
        if r.date_from:
            data.update({
                'date_from': r.date_from,
            })
        if r.date_to:
            data.update({
                'date_to': r.date_to,
            })

        company_ids = self.env.companies.ids
        company_domain = [('company_id', 'in', company_ids)]
        if r.account_tag_ids:
            company_domain.append(
                ('tag_ids', 'in', r.account_tag_ids.ids))
        if r.account_ids:
            company_domain.append(('id', 'in', r.account_ids.ids))

        new_account_ids = self.env['account.account'].search(company_domain)
        data.update({'accounts': new_account_ids, })
        filters = self.get_filter(option)
        records = self._get_report_values(data)

        if filters['account_tags'] != ['All']:
            tag_accounts = list(map(lambda x: x.code, new_account_ids))

            def filter_code(rec_dict):
                if rec_dict['code'] in tag_accounts:
                    return True
                else:
                    return False

            new_records = list(filter(filter_code, records['Accounts']))
            records['Accounts'] = new_records
        # trans_tag = self.env['ir.translation'].search(
        #     [('value', '=', tag), ('module', '=', 'dynamic_accounts_report')],
        #     limit=1).src
        # if trans_tag:
        #     tag_upd = trans_tag
        # else:
        tag_upd = tag
        lang = self.env.context.get('lang') or 'en_US'
        account_report_id = self.env['account.financial.report'].with_context(
            lang=lang).search([
            ('name', 'ilike', tag_upd)])
        new_data = {'id': self.id, 'date_from': False,
                    'enable_filter': True,
                    'debit_credit': True,
                    'date_to': False, 'account_report_id': account_report_id,
                    'target_move': filters['target_move'],
                    'view_format': 'vertical',
                    'company_id': self.company_id,
                    'used_context': {'journal_ids': False,
                                     'state': filters['target_move'].lower(),
                                     'date_from': filters['date_from'],
                                     'date_to': filters['date_to'],
                                     'strict_range': False,
                                     'company_id': self.company_id,
                                     'lang': lang}}
        account_lines = self.get_account_lines(new_data)
        report_lines = self.view_report_pdf(account_lines, new_data)[
            'report_lines']
        move_line_accounts = []
        move_lines_dict = {}
        for rec in records['Accounts']:
            move_line_accounts.append(rec['id'])
            move_lines_dict[rec['id']] = {}
            move_lines_dict[rec['id']]['debit'] = rec['debit']
            move_lines_dict[rec['id']]['credit'] = rec['credit']
            move_lines_dict[rec['id']]['balance'] = rec['balance']
            move_lines_dict[rec['id']]['account_type'] = rec.get('account_type', '')
            # Add comparison data to move_lines_dict
            for key, value in rec.items():
                if key.startswith('debit_prev_') or key.startswith('credit_prev_') or key.startswith('debit_month_') or key.startswith('credit_month_'):
                    move_lines_dict[rec['id']][key] = value
        report_lines_move = []
        parent_list = []

        def filter_movelines_parents(obj):
            for each in obj:
                if each['report_type'] == 'accounts' and 'account' in each and \
                        each['account']:
                    if each['account'] in move_line_accounts:
                        report_lines_move.append(each)
                        parent_list.append(each['p_id'])

                elif each['report_type'] == 'account_report':
                    report_lines_move.append(each)
                else:
                    report_lines_move.append(each)

        filter_movelines_parents(report_lines)
        for rec in report_lines_move:
            if rec['report_type'] == 'accounts':
                if rec['account'] in move_line_accounts:
                    rec['debit'] = move_lines_dict[rec['account']]['debit']
                    rec['credit'] = move_lines_dict[rec['account']]['credit']
                    rec['balance'] = move_lines_dict[rec['account']]['balance']
                    rec['account_type'] = move_lines_dict[rec['account']].get('account_type', '')
                    # Assign comparison data to account lines
                    account_data = move_lines_dict[rec['account']]
                    for key, value in account_data.items():
                        if key.startswith('debit_prev_') or key.startswith('credit_prev_') or key.startswith('debit_month_') or key.startswith('credit_month_'):
                            rec[key] = value

        parent_list = list(set(parent_list))
        max_level = 0
        for rep in report_lines_move:
            if rep['level'] > max_level:
                max_level = rep['level']

        def get_parents(obj):
            for item in report_lines_move:
                for each in obj:
                    if item['report_type'] != 'account_type' and \
                            each in item['c_ids']:
                        obj.append(item['r_id'])
                if item['report_type'] == 'account_report':
                    obj.append(item['r_id'])
                    break

        get_parents(parent_list)
        for i in range(max_level):
            get_parents(parent_list)

        parent_list = list(set(parent_list))
        final_report_lines = []
        for rec in report_lines_move:
            if rec['report_type'] != 'accounts':
                if rec['r_id'] in parent_list:
                    final_report_lines.append(rec)
            else:
                final_report_lines.append(rec)

        def filter_sum(obj):
            sum_list = {}
            for pl in parent_list:
                sum_list[pl] = {}
                sum_list[pl]['s_debit'] = 0
                sum_list[pl]['s_credit'] = 0
                sum_list[pl]['s_balance'] = 0
                # Initialize comparison sums
                for i in range(1, (data.get('comparison_years') or 0) + 1):
                    sum_list[pl]['s_debit_prev_%d' % i] = 0
                    sum_list[pl]['s_credit_prev_%d' % i] = 0
                for i in range(1, (data.get('comparison_months') or 0) + 1):
                    sum_list[pl]['s_debit_month_%d' % i] = 0
                    sum_list[pl]['s_credit_month_%d' % i] = 0

            for each in obj:
                if each['p_id'] and each['p_id'] in parent_list:
                    sum_list[each['p_id']]['s_debit'] += each['debit']
                    sum_list[each['p_id']]['s_credit'] += each['credit']
                    sum_list[each['p_id']]['s_balance'] += each['balance']
                    # Add comparison data
                    for i in range(1, (data.get('comparison_years') or 0) + 1):
                        debit_key = 'debit_prev_%d' % i
                        credit_key = 'credit_prev_%d' % i
                        sum_list[each['p_id']]['s_debit_prev_%d' % i] += each.get(debit_key, 0)
                        sum_list[each['p_id']]['s_credit_prev_%d' % i] += each.get(credit_key, 0)
                    for i in range(1, (data.get('comparison_months') or 0) + 1):
                        debit_key = 'debit_month_%d' % i
                        credit_key = 'credit_month_%d' % i
                        sum_list[each['p_id']]['s_debit_month_%d' % i] += each.get(debit_key, 0)
                        sum_list[each['p_id']]['s_credit_month_%d' % i] += each.get(credit_key, 0)
            return sum_list

        def assign_sum(obj):
            for each in obj:
                if each['r_id'] in parent_list and \
                        each['report_type'] != 'account_report':
                    each['debit'] = sum_list_new[each['r_id']]['s_debit']
                    each['credit'] = sum_list_new[each['r_id']]['s_credit']
                    # Assign comparison values
                    for i in range(1, (data.get('comparison_years') or 0) + 1):
                        each['debit_prev_%d' % i] = sum_list_new[each['r_id']]['s_debit_prev_%d' % i]
                        each['credit_prev_%d' % i] = sum_list_new[each['r_id']]['s_credit_prev_%d' % i]
                    for i in range(1, (data.get('comparison_months') or 0) + 1):
                        each['debit_month_%d' % i] = sum_list_new[each['r_id']]['s_debit_month_%d' % i]
                        each['credit_month_%d' % i] = sum_list_new[each['r_id']]['s_credit_month_%d' % i]

        for p in range(max_level):
            sum_list_new = filter_sum(final_report_lines)
            assign_sum(final_report_lines)

        company_id = self.env.company
        currency = company_id.currency_id
        symbol = currency.symbol
        rounding = currency.rounding
        decimal_places = currency.decimal_places
        position = currency.position

        for rec in final_report_lines:
            rec['debit'] = round(rec['debit'], decimal_places)
            rec['credit'] = round(rec['credit'], decimal_places)
            
            # Calculate balance based on account type (standard Odoo P&L logic)
            account_type = rec.get('account_type', '').lower()
            if 'income' in account_type:
                # For income accounts: balance = credit - debit (income is credit-based)
                rec['balance'] = rec['credit'] - rec['debit']
            elif 'expense' in account_type:
                # For expense accounts: balance = debit - credit (expenses are debit-based)  
                rec['balance'] = rec['debit'] - rec['credit']
            else:
                # Default calculation for other account types
                rec['balance'] = rec['debit'] - rec['credit']
                
            rec['balance'] = round(rec['balance'], decimal_places)
            
            # Apply standard Odoo sign logic to comparison balances
            for i in range(1, (data.get('comparison_years') or 0) + 1):
                debit_key = 'debit_prev_%d' % i
                credit_key = 'credit_prev_%d' % i
                balance_key = 'balance_prev_%d' % i
                if debit_key in rec and credit_key in rec:
                    if 'income' in account_type:
                        # For income accounts: balance = credit - debit
                        rec[balance_key] = rec[credit_key] - rec[debit_key]
                    elif 'expense' in account_type:
                        # For expense accounts: balance = debit - credit
                        rec[balance_key] = rec[debit_key] - rec[credit_key]
                    else:
                        # Default calculation
                        rec[balance_key] = rec[debit_key] - rec[credit_key]
            
            for i in range(1, (data.get('comparison_months') or 0) + 1):
                debit_key = 'debit_month_%d' % i
                credit_key = 'credit_month_%d' % i
                balance_key = 'balance_month_%d' % i
                if debit_key in rec and credit_key in rec:
                    if 'income' in account_type:
                        # For income accounts: balance = credit - debit
                        rec[balance_key] = rec[credit_key] - rec[debit_key]
                    elif 'expense' in account_type:
                        # For expense accounts: balance = debit - credit
                        rec[balance_key] = rec[debit_key] - rec[credit_key]
                    else:
                        # Default calculation
                        rec[balance_key] = rec[debit_key] - rec[credit_key]
            
            # Make income balance positive for the income row before Gross Profit
            # Check if this is an income row (typically has 'income' in name and is a summary row)
            account_name = rec.get('name', '').lower() if isinstance(rec.get('name'), str) else ''
            
            # Target the specific income summary row (before Gross Profit)
            # This is typically a summary row with 'income' in the name
            is_income_summary = ('income' in account_name and 
                                rec.get('report_type') == 'account_report' and
                                rec.get('level') == 1)  # Adjust level as needed
            
            if is_income_summary:
                rec['balance'] = abs(rec['balance'])
                # Make comparison balances positive for this income summary row
                for i in range(1, (data.get('comparison_years') or 0) + 1):
                    balance_key = 'balance_prev_%d' % i
                    if balance_key in rec:
                        rec[balance_key] = abs(rec[balance_key])
                
                for i in range(1, (data.get('comparison_months') or 0) + 1):
                    balance_key = 'balance_month_%d' % i
                    if balance_key in rec:
                        rec[balance_key] = abs(rec[balance_key])
            
            # Remove the balance_cmp logic as it may interfere with standard P&L calculations
            # if (rec['balance_cmp'] < 0 and rec['balance'] > 0) or (
            #         rec['balance_cmp'] > 0 and rec['balance'] < 0):
            #     rec['balance'] = rec['balance'] * -1

            if position == "before":
                rec['m_debit'] = symbol + " " + "{:,.2f}".format(rec['debit'])
                rec['m_credit'] = symbol + " " + "{:,.2f}".format(
                    rec['credit'])
                rec['m_balance'] = symbol + " " + "{:,.2f}".format(
                    rec['balance'])
            else:
                rec['m_debit'] = "{:,.2f}".format(rec['debit']) + " " + symbol
                rec['m_credit'] = "{:,.2f}".format(
                    rec['credit']) + " " + symbol
                rec['m_balance'] = "{:,.2f}".format(
                    rec['balance']) + " " + symbol
        user = self.env.user
        user_language = user.lang
        for item in records['Accounts']:
            if isinstance(item['name'], dict):
                item['new_name'] = item['name'][
                    user_language] if user_language in item['name'] else \
                    item['name']['en_US']
            else:
                item['new_name'] = item['name']
        merged_data = {}
        for line in records['Accounts']:
            account_id = line['account_id']
            if account_id not in merged_data:
                merged_data[account_id] = line
            else:
                merged_data[account_id]['debit'] += line['debit']
                merged_data[account_id]['credit'] += line['credit']
                merged_data[account_id]['balance'] += line['balance']
                # Merge comparison data
                for i in range(1, (data.get('comparison_years') or 0) + 1):
                    debit_key = 'debit_prev_%d' % i
                    credit_key = 'credit_prev_%d' % i
                    if debit_key in line and debit_key in merged_data[account_id]:
                        merged_data[account_id][debit_key] += line[debit_key]
                    if credit_key in line and credit_key in merged_data[account_id]:
                        merged_data[account_id][credit_key] += line[credit_key]
                for i in range(1, (data.get('comparison_months') or 0) + 1):
                    debit_key = 'debit_month_%d' % i
                    credit_key = 'credit_month_%d' % i
                    if debit_key in line and debit_key in merged_data[account_id]:
                        merged_data[account_id][debit_key] += line[debit_key]
                    if credit_key in line and credit_key in merged_data[account_id]:
                        merged_data[account_id][credit_key] += line[credit_key]
        report_list = list(merged_data.values())
        return {
            'name': tag,
            'type': 'ir.actions.client',
            'tag': tag,
            'filters': filters,
            'report_lines': report_list,
            'debit_total': records['debit_total'],
            'credit_total': records['credit_total'],
            'debit_balance': records['debit_balance'],
            'currency': currency,
            'bs_lines': final_report_lines,
            'lang': self.env.context.get('lang') or 'en_US',
            'debit_prev_totals': records.get('debit_prev_totals'),
            'credit_prev_totals': records.get('credit_prev_totals'),
            'debit_month_totals': records.get('debit_month_totals'),
            'credit_month_totals': records.get('credit_month_totals'),
            'comparison_year_labels': self._get_comparison_year_labels(data),
            'comparison_month_labels': self._get_comparison_month_labels(data),
        }

    def get_filter(self, option):
        data = self.get_filter_data(option)
        filters = {}
        if data.get('journal_ids'):
            filters['journals'] = self.env['account.journal'].browse(
                data.get('journal_ids')).mapped('code')
        else:
            filters['journals'] = ['All']
        if data.get('account_ids', []):
            filters['accounts'] = self.env['account.account'].browse(
                data.get('account_ids', [])).mapped('code')
        else:
            filters['accounts'] = ['All']
        if data.get('target_move'):
            filters['target_move'] = data.get('target_move')
        else:
            filters['target_move'] = 'posted'
        if data.get('date_from'):
            filters['date_from'] = data.get('date_from')
        else:
            filters['date_from'] = False
        if data.get('date_to'):
            filters['date_to'] = data.get('date_to')
        else:
            filters['date_to'] = False
        if data.get('analytic_ids', []):
            filters['analytics'] = self.env['account.analytic.account'].browse(
                data.get('analytic_ids', [])).mapped('name')
        else:
            filters['analytics'] = ['All']

        if data.get('account_tag_ids'):
            filters['account_tags'] = self.env['account.account.tag'].browse(
                data.get('account_tag_ids', [])).mapped('name')
        else:
            filters['account_tags'] = ['All']

        if data.get('comparison_years'):
            filters['comparison_years'] = data.get('comparison_years')
        if data.get('comparison_months'):
            filters['comparison_months'] = data.get('comparison_months')

        # if data.get('analytic_tag_ids', []):
        #     filters['analytic_tags'] = self.env['account.analytic.tag'].browse(
        #         data.get('analytic_tag_ids', [])).mapped('name')
        # else:
        #     filters['analytic_tags'] = ['All']

        filters['company_id'] = ''
        filters['accounts_list'] = data.get('accounts_list')
        filters['journals_list'] = data.get('journals_list')
        filters['analytic_list'] = data.get('analytic_list')
        filters['account_tag_list'] = data.get('account_tag_list')
        filters['analytic_tag_list'] = data.get('analytic_tag_list')
        filters['company_name'] = data.get('company_name')
        filters['target_move'] = data.get('target_move').capitalize()
        return filters

    def get_filter_data(self, option):
        r = self.env['dynamic.balance.sheet.report'].search(
            [('id', '=', option[0])])
        default_filters = {}
        company_ids = self.env.companies.ids
        company_domain = [('company_id', 'in', company_ids)]
        company_names = ', '.join(self.env.companies.mapped('name'))
        journal_ids = r.journal_ids if r.journal_ids else self.env[
            'account.journal'].search(company_domain, order="company_id, name")
        analytics = self.analytic_ids if self.analytic_ids else self.env[
            'account.analytic.account'].search(
            company_domain)
        account_tags = self.account_tag_ids if self.account_tag_ids else \
            self.env[
                'account.account.tag'].search([])
        # analytic_tags = self.analytic_tag_ids if self.analytic_tag_ids else \
        #     self.env[
        #         'account.analytic.tag'].sudo().search(
        #         ['|', ('company_id', 'in', company_ids),
        #          ('company_id', '=', False)])

        if r.account_tag_ids:
            company_domain.append(
                ('tag_ids', 'in', r.account_tag_ids.ids))

        accounts_ids = self.account_ids if self.account_ids else self.env[
            'account.account'].search(company_domain, order="company_id, name")

        journals = []
        o_company = False
        for j in journal_ids:
            if j.company_id != o_company:
                journals.append(('divider', j.company_id.name))
                o_company = j.company_id
            journals.append((j.id, j.name, j.code))

        accounts = []

        o_company = False
        for j in accounts_ids:
            if j.company_id != o_company:
                accounts.append(('divider', j.company_id.name))
                o_company = j.company_id
            accounts.append((j.id, j.name))

        filter_dict = {
            'journal_ids': r.journal_ids.ids,
            'account_ids': r.account_ids.ids,
            'analytic_ids': r.analytic_ids.ids,
            'company_id': company_ids,
            'date_from': r.date_from,
            'date_to': r.date_to,
            'target_move': r.target_move,
            'journals_list': journals,
            'accounts_list': accounts,
            'analytic_list': [(anl.id, anl.name) for anl in analytics],
            'company_name': company_names,
            # 'analytic_tag_ids': r.analytic_tag_ids.ids,
            # 'analytic_tag_list': [(anltag.id, anltag.name) for anltag in
            #                       analytic_tags],
            'account_tag_ids': r.account_tag_ids.ids,
            'account_tag_list': [(a.id, a.name) for a in account_tags],
            'comparison_years': r.comparison_years,
            'comparison_months': r.comparison_months,
        }
        filter_dict.update(default_filters)
        return filter_dict

    def _get_report_values(self, data):
        docs = data['model']
        display_account = data['display_account']
        decimal_places = self.env.company.currency_id.decimal_places
        init_balance = True
        journals = data['journals']
        accounts = self.env['account.account'].search([])
        if not accounts:
            raise UserError(_("No Accounts Found! Please Add One"))
        account_res = self._get_accounts(accounts, init_balance,
                                         display_account, data)
        current_lang = self.env.user.lang
        list_ac = []
        default_lg = self.env['ir.http']._get_default_lang()
        for rec in account_res:
            list_ac.append(rec['account_id'])
            if rec.get('name', None):
                localized_name = rec['name']
                if localized_name:
                    rec['name'] = localized_name
                else:
                    # If the translation for the current language is not available, use a default language or handle it as needed.
                    rec['name'] = rec['name'].get(default_lg,
                                                  '')  # Replace 'en_US' with your desired default language.
            else:
                # Handle the case where 'name' is not present in the dictionary.
                rec['name'] = ''  # You can use an
        debit_total = 0
        debit_total = sum(x['debit'] for x in account_res)
        credit_total = sum(x['credit'] for x in account_res)
        debit_balance = round(debit_total, decimal_places) - round(credit_total, decimal_places)
        
        # Calculate comparison totals
        debit_prev_totals = None
        credit_prev_totals = None
        if data.get('comparison_years') and data.get('comparison_years') > 0:
            years = data.get('comparison_years')
            debit_prev_totals = []
            credit_prev_totals = []
            for i in range(1, years + 1):
                debit_prev_totals.append(sum(x.get('debit_prev_%d' % i, 0.0) for x in account_res))
                credit_prev_totals.append(sum(x.get('credit_prev_%d' % i, 0.0) for x in account_res))
        
        debit_month_totals = None
        credit_month_totals = None
        if data.get('comparison_months') and data.get('comparison_months') > 0:
            months = data.get('comparison_months')
            debit_month_totals = []
            credit_month_totals = []
            for i in range(1, months + 1):
                debit_month_totals.append(sum(x.get('debit_month_%d' % i, 0.0) for x in account_res))
                credit_month_totals.append(sum(x.get('credit_month_%d' % i, 0.0) for x in account_res))
        
        return {
            'doc_ids': self.ids,
            'debit_total': debit_total,
            'credit_total': credit_total,
            'debit_balance': debit_balance,
            'debit_prev_totals': debit_prev_totals,
            'credit_prev_totals': credit_prev_totals,
            'debit_month_totals': debit_month_totals,
            'credit_month_totals': credit_month_totals,
            'docs': docs,
            'time': time,
            'Accounts': account_res,
        }

    @api.model
    def create(self, vals):
        vals['target_move'] = 'posted'
        res = super(BalanceSheetView, self).create(vals)
        return res

    def write(self, vals):
        if vals.get('target_move'):
            vals.update({'target_move': vals.get('target_move').lower()})
        if vals.get('journal_ids'):
            vals.update({'journal_ids': [(6, 0, vals.get('journal_ids'))]})
        if not vals.get('journal_ids'):
            vals.update({'journal_ids': [(5,)]})
        if vals.get('account_ids'):
            vals.update(
                {'account_ids': [(4, j) for j in vals.get('account_ids')]})
        if not vals.get('account_ids'):
            vals.update({'account_ids': [(5,)]})
        if vals.get('analytic_ids'):
            vals.update(
                {'analytic_ids': [(4, j) for j in vals.get('analytic_ids')]})
        if not vals.get('analytic_ids'):
            vals.update({'analytic_ids': [(5,)]})

        if vals.get('account_tag_ids'):
            vals.update({'account_tag_ids': [(4, j) for j in
                                             vals.get('account_tag_ids')]})
        if not vals.get('account_tag_ids'):
            vals.update({'account_tag_ids': [(5,)]})

        res = super(BalanceSheetView, self).write(vals)
        return res

    def _get_accounts(self, accounts, init_balance, display_account, data):
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        move_lines = {x: [] for x in accounts.ids}
        currency_id = self.env.company.currency_id
        decimal_places = self.env.company.currency_id.decimal_places

        # Prepare sql query base on selected parameters from wizard
        tables, where_clause, where_params = MoveLine._query_get()
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        final_filters = " AND ".join(wheres)
        final_filters = final_filters.replace('account_move_line__move_id',
                                              'm').replace(
            'account_move_line', 'l')
        new_final_filter = final_filters
        if data['target_move'] == 'posted':
            new_final_filter += " AND m.state = 'posted'"
        else:
            new_final_filter += " AND m.state in ('draft','posted')"
        if data.get('date_from'):
            new_final_filter += " AND l.date >= '%s'" % data.get('date_from')
        if data.get('date_to'):
            new_final_filter += " AND l.date <= '%s'" % data.get('date_to')
        if data['journals']:
            new_final_filter += ' AND j.id IN %s' % str(
                tuple(data['journals'].ids) + tuple([0]))
        if data.get('accounts'):
            WHERE = "WHERE l.account_id IN %s" % str(
                tuple(data.get('accounts').ids) + tuple([0]))
        else:
            WHERE = "WHERE l.account_id IN %s"
        if data.get('analytics'):
            WHERE += ' AND an.id IN %s' % str(
                tuple(data.get('analytics').ids) + tuple([0]))
        if data.get('account_tags'):
            WHERE += ' AND act.id IN %s' % str(
                tuple(data.get('account_tags').ids) + tuple([0]))

        # if data['analytic_tags']:
        #     WHERE += ' AND anltag.account_analytic_tag_id IN %s' % str(
        #         tuple(data.get('analytic_tags').ids) + tuple([0]))
        # current_lang = self.env.user.lang
        # Get move lines base on sql query and Calculate the total balance of move lines
        base_sql = ('''SELECT l.account_id AS account_id, a.code AS code,a.id AS id, a.name AS name, 
                    ROUND(COALESCE(SUM(l.debit),0),{}) AS debit, 
                    ROUND(COALESCE(SUM(l.credit),0),{}) AS credit, 
                    ROUND(COALESCE(SUM(l.balance),0),{}) AS balance,
                    anl.keys, act.name as tag, a.account_type
                    FROM account_move_line l
                    JOIN account_move m ON (l.move_id=m.id)
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)
                    LEFT JOIN account_account_tag_account_move_line_rel acc ON (acc.account_move_line_id=l.id)
                    JOIN account_journal j ON (l.journal_id=j.id)
                    JOIN account_account a ON (l.account_id = a.id) LEFT JOIN account_account_account_tag acct ON 
                    (acct.account_account_id = l.account_id)
                    LEFT JOIN account_account_tag act ON 
                    (act.id = acct.account_account_tag_id)
                    LEFT JOIN LATERAL (
                    SELECT jsonb_object_keys(l.analytic_distribution)::INT 
                    AS keys) anl ON true
                    LEFT JOIN account_analytic_account an 
                    ON (anl.keys = an.id)''').format(decimal_places, decimal_places, decimal_places)
        sql = base_sql + WHERE + final_filters + ''' GROUP BY l.account_id, 
                   a.code,a.id,a.name,anl.keys, act.name'''

        if data.get('accounts'):
            params = tuple(where_params)
        else:
            params = (tuple(accounts.ids),) + tuple(where_params)
        cr.execute(sql, params)

        account_res = cr.dictfetchall()

        # Prior years computation when requested
        prior_year_results = {}
        if data.get('comparison_years') and data.get('comparison_years') > 0:
            years = data.get('comparison_years')
            for i in range(1, years + 1):
                tables_p, where_clause_p, where_params_p = MoveLine._query_get()
                wheres_p = [""]
                if where_clause_p.strip():
                    wheres_p.append(where_clause_p.strip())
                filters_p = " AND ".join(wheres_p)
                filters_p = filters_p.replace('account_move_line__move_id',
                                              'm').replace(
                    'account_move_line', 'l')
                if data['target_move'] == 'posted':
                    filters_p += " AND m.state = 'posted'"
                else:
                    filters_p += " AND m.state in ('draft','posted')"
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
                    filters_p += " AND l.date >= '%s'" % fields.Date.to_string(date_from_prev)
                if date_to_prev:
                    date_to_prev = fields.Date.from_string(date_to_prev) - relativedelta(years=i)
                    filters_p += " AND l.date <= '%s'" % fields.Date.to_string(date_to_prev)

                if data['journals']:
                    filters_p += ' AND j.id IN %s' % str(tuple(data['journals'].ids) + tuple([0]))
                if data.get('accounts'):
                    WHERE_p = "WHERE l.account_id IN %s" % str(tuple(data.get('accounts').ids) + tuple([0]))
                else:
                    WHERE_p = "WHERE l.account_id IN %s"
                if data.get('analytics'):
                    WHERE_p += ' AND an.id IN %s' % str(tuple(data.get('analytics').ids) + tuple([0]))
                if data.get('account_tags'):
                    WHERE_p += ' AND act.id IN %s' % str(tuple(data.get('account_tags').ids) + tuple([0]))

                sql_p = base_sql + WHERE_p + filters_p + ''' GROUP BY l.account_id, 
                           a.code,a.id,a.name,anl.keys, act.name, a.account_type'''
                
                if data.get('accounts'):
                    params_p = tuple(where_params_p)
                else:
                    params_p = (tuple(accounts.ids),) + tuple(where_params_p)
                cr.execute(sql_p, params_p)
                for row in cr.dictfetchall():
                    aid = row['account_id']
                    if aid not in prior_year_results:
                        prior_year_results[aid] = {}
                    prior_year_results[aid]['debit_prev_%d' % i] = row.get('debit') or 0.0
                    prior_year_results[aid]['credit_prev_%d' % i] = row.get('credit') or 0.0
                    # Calculate balance based on account type for comparison periods
                    account_type = row.get('account_type', '').lower()
                    if 'income' in account_type:
                        # For income accounts: balance = credit - debit
                        prior_year_results[aid]['balance_prev_%d' % i] = (row.get('credit') or 0.0) - (row.get('debit') or 0.0)
                    elif 'expense' in account_type:
                        # For expense accounts: balance = debit - credit
                        prior_year_results[aid]['balance_prev_%d' % i] = (row.get('debit') or 0.0) - (row.get('credit') or 0.0)
                    else:
                        # Default calculation
                        prior_year_results[aid]['balance_prev_%d' % i] = (row.get('debit') or 0.0) - (row.get('credit') or 0.0)

        # Prior months computation when requested
        prior_month_results = {}
        if data.get('comparison_months') and data.get('comparison_months') > 0:
            months = data.get('comparison_months')
            for i in range(1, months + 1):
                tables_m, where_clause_m, where_params_m = MoveLine._query_get()
                wheres_m = [""]
                if where_clause_m.strip():
                    wheres_m.append(where_clause_m.strip())
                filters_m = " AND ".join(wheres_m)
                filters_m = filters_m.replace('account_move_line__move_id',
                                              'm').replace(
                    'account_move_line', 'l')
                if data['target_move'] == 'posted':
                    filters_m += " AND m.state = 'posted'"
                else:
                    filters_m += " AND m.state in ('draft','posted')"
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
                    filters_m += " AND l.date >= '%s'" % fields.Date.to_string(date_from_m)
                if date_to_m:
                    date_to_m = fields.Date.from_string(date_to_m) - relativedelta(months=i)
                    filters_m += " AND l.date <= '%s'" % fields.Date.to_string(date_to_m)

                if data['journals']:
                    filters_m += ' AND j.id IN %s' % str(tuple(data['journals'].ids) + tuple([0]))
                if data.get('accounts'):
                    WHERE_m = "WHERE l.account_id IN %s" % str(tuple(data.get('accounts').ids) + tuple([0]))
                else:
                    WHERE_m = "WHERE l.account_id IN %s"
                if data.get('analytics'):
                    WHERE_m += ' AND an.id IN %s' % str(tuple(data.get('analytics').ids) + tuple([0]))
                if data.get('account_tags'):
                    WHERE_m += ' AND act.id IN %s' % str(tuple(data.get('account_tags').ids) + tuple([0]))

                sql_m = base_sql + WHERE_m + filters_m + ''' GROUP BY l.account_id, 
                           a.code,a.id,a.name,anl.keys, act.name, a.account_type'''
                
                if data.get('accounts'):
                    params_m = tuple(where_params_m)
                else:
                    params_m = (tuple(accounts.ids),) + tuple(where_params_m)
                cr.execute(sql_m, params_m)
                for row in cr.dictfetchall():
                    aid = row['account_id']
                    if aid not in prior_month_results:
                        prior_month_results[aid] = {}
                    prior_month_results[aid]['debit_month_%d' % i] = row.get('debit') or 0.0
                    prior_month_results[aid]['credit_month_%d' % i] = row.get('credit') or 0.0
                    # Calculate balance based on account type for month comparison periods
                    account_type = row.get('account_type', '').lower()
                    if 'income' in account_type:
                        # For income accounts: balance = credit - debit
                        prior_month_results[aid]['balance_month_%d' % i] = (row.get('credit') or 0.0) - (row.get('debit') or 0.0)
                    elif 'expense' in account_type:
                        # For expense accounts: balance = debit - credit
                        prior_month_results[aid]['balance_month_%d' % i] = (row.get('debit') or 0.0) - (row.get('credit') or 0.0)
                    else:
                        # Default calculation
                        prior_month_results[aid]['balance_month_%d' % i] = (row.get('debit') or 0.0) - (row.get('credit') or 0.0)

        # Merge comparison data into main results
        for account in account_res:
            aid = account['account_id']
            if aid in prior_year_results:
                account.update(prior_year_results[aid])
            if aid in prior_month_results:
                account.update(prior_month_results[aid])

        return account_res

        # for row in cr.dictfetchall():
        #     balance = 0
        #     for line in move_lines.get(row['account_id']):
        #         balance += round(line['debit'], 2) - round(line['credit'], 2)
        #     row['balance'] += (round(balance, 2))
        #     row['m_id'] = row['account_id']
        #     move_lines[row.pop('account_id')].append(row)
        # # Calculate the debit, credit and balance for Accounts
        # account_res = []
        # for account in accounts:
        #     currency = account.currency_id and account.currency_id or account.company_id.currency_id
        #     res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
        #     res['code'] = account.code
        #     res['name'] = account.name
        #     res['id'] = account.id
        #     res['move_lines'] = move_lines[account.id]
        #     for line in res.get('move_lines'):
        #         res['debit'] += round(line['debit'], 2)
        #         res['credit'] += round(line['credit'], 2)
        #         res['balance'] = round(line['balance'], 2)
        #     if display_account == 'all':
        #         account_res.append(res)
        #     if display_account == 'movement' and res.get('move_lines'):
        #         account_res.append(res)
        #     if display_account == 'not_zero' and not currency.is_zero(
        #             res['balance']):
        #         account_res.append(res)
        #
        # return account_res

    @api.model
    def _get_currency(self):
        journal = self.env['account.journal'].browse(
            self.env.context.get('default_journal_id', False))
        if journal.currency_id:
            return journal.currency_id.id
        currency_array = [self.env.company.currency_id.symbol,
                          self.env.company.currency_id.position]
        return currency_array

    def get_dynamic_xlsx_report(self, options, response, report_data,
                                dfr_data):
        i_data = str(report_data)
        filters = json.loads(options)
        export_data = json.loads(dfr_data)
        rl_data = export_data.get('bs_lines', [])
        
        # Get comparison data from the export_data
        debit_prev_totals = export_data.get('debit_prev_totals', [])
        credit_prev_totals = export_data.get('credit_prev_totals', [])
        debit_month_totals = export_data.get('debit_month_totals', [])
        credit_month_totals = export_data.get('credit_month_totals', [])
        comparison_year_labels = export_data.get('comparison_year_labels', [])

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        sheet = workbook.add_worksheet()
        head = workbook.add_format({'align': 'center', 'bold': True,
                                    'font_size': '20px'})
        sub_heading = workbook.add_format(
            {'align': 'center', 'bold': True, 'font_size': '10px',
             'border': 1,
             'border_color': 'black'})
        side_heading_main = workbook.add_format(
            {'align': 'left', 'bold': True, 'font_size': '10px',
             'border': 1,
             'border_color': 'black'})

        side_heading_sub = workbook.add_format(
            {'align': 'left', 'bold': True, 'font_size': '10px',
             'border': 1,
             'border_color': 'black'})

        side_heading_sub.set_indent(1)
        txt = workbook.add_format({'font_size': '10px', 'border': 1})
        txt_name = workbook.add_format({'font_size': '10px', 'border': 1})
        txt_name_bold = workbook.add_format({'font_size': '10px', 'border': 1,
                                             'bold': True})
        txt_name.set_indent(2)
        txt_name_bold.set_indent(2)

        txt = workbook.add_format({'font_size': '10px', 'border': 1})

        sheet.merge_range('A2:D3',
                          filters.get('company_name') + ' : ' + i_data,
                          head)
        date_head = workbook.add_format({'align': 'center', 'bold': True,
                                         'font_size': '10px'})

        date_head.set_align('vcenter')
        date_head.set_text_wrap()
        date_head.set_shrink()
        date_head_left = workbook.add_format({'align': 'left', 'bold': True,
                                              'font_size': '10px'})

        date_head_right = workbook.add_format({'align': 'right', 'bold': True,
                                               'font_size': '10px'})

        date_head_left.set_indent(1)
        date_head_right.set_indent(1)

        if filters.get('date_from'):
            sheet.merge_range('A4:B4', 'From: ' + filters.get('date_from'),
                              date_head_left)
        if filters.get('date_to'):
            sheet.merge_range('C4:D4', 'To: ' + filters.get('date_to'),
                              date_head_right)

        sheet.merge_range('A5:D6', '  Accounts: ' + ', '.join(
            [lt or '' for lt in
             filters['accounts']]) + ';  Journals: ' + ', '.join(
            [lt or '' for lt in
             filters['journals']]) + ';  Account Tags: ' + ', '.join(
            [lt or '' for lt in
             filters['account_tags']]) + ';  Analytic: ' + ', '.join(
            [at or '' for at in
             filters['analytics']]) + ';  Target Moves: ' + filters.get(
            'target_move').capitalize(), date_head)

        sheet.set_column(0, 0, 30)
        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 15)
        sheet.set_column(3, 3, 15)
        
        # Set column widths for comparison columns
        if filters.get('comparison_years') and filters.get('comparison_years') > 0:
            year_cols = filters.get('comparison_years') * 3
            start_col = 4
            end_col = start_col + year_cols - 1
            sheet.set_column(start_col, end_col, 15)
        
        if filters.get('comparison_months') and filters.get('comparison_months') > 0:
            month_cols = filters.get('comparison_months') * 3
            start_col = 4
            if filters.get('comparison_years') and filters.get('comparison_years') > 0:
                start_col = 4 + (filters.get('comparison_years') * 3)
            end_col = start_col + month_cols - 1
            sheet.set_column(start_col, end_col, 15)

        row = 5
        col = 0

        row += 2
        sheet.write(row, col, '', sub_heading)
        sheet.write(row, col + 1, 'Debit', sub_heading)
        sheet.write(row, col + 2, 'Credit', sub_heading)
        sheet.write(row, col + 3, 'Balance', sub_heading)
        
        # Calculate column positions for comparison headers
        header_col = 4
        
        # Add prior year headers
        if filters.get('comparison_years') and filters.get('comparison_years') > 0:
            current_date = fields.Date.today()
            current_year = current_date.year
            for i in range(1, filters.get('comparison_years') + 1):
                year_label = str(current_year - i)
                sheet.write(row, header_col, f'Debit {year_label}', sub_heading)
                sheet.write(row, header_col + 1, f'Credit {year_label}', sub_heading)
                sheet.write(row, header_col + 2, f'Balance {year_label}', sub_heading)
                header_col += 3  # Move column position for next year
        
        # Add prior month headers
        if filters.get('comparison_months') and filters.get('comparison_months') > 0:
            month_labels = self._get_comparison_month_labels(filters)
            for i, month_label in enumerate(month_labels, 1):
                sheet.write(row, header_col, f'Debit {month_label}', sub_heading)
                sheet.write(row, header_col + 1, f'Credit {month_label}', sub_heading)
                sheet.write(row, header_col + 2, f'Balance {month_label}', sub_heading)
                header_col += 3  # Move column position for next month

        if rl_data:
            for fr in rl_data:

                row += 1
                if fr['level'] == 1:
                    sheet.write(row, col, fr['name'], side_heading_main)
                elif fr['level'] == 2:
                    sheet.write(row, col, fr['name'], side_heading_sub)
                else:
                    sheet.write(row, col, fr['name'], txt_name)
                sheet.write(row, col + 1, fr['debit'], txt)
                sheet.write(row, col + 2, fr['credit'], txt)
                sheet.write(row, col + 3, fr['balance'], txt)
                
                # Write prior year data
                data_col = 4
                if filters.get('comparison_years') and filters.get('comparison_years') > 0:
                    for i in range(1, filters.get('comparison_years') + 1):
                        # Use pre-calculated balance values for comparison periods
                        debit_key = 'debit_prev_%d' % i
                        credit_key = 'credit_prev_%d' % i
                        balance_key = 'balance_prev_%d' % i
                        
                        debit_val = fr.get(debit_key, 0.0)
                        credit_val = fr.get(credit_key, 0.0)
                        balance_val = fr.get(balance_key, 0.0)
                        
                        # If balance values exist but debit/credit don't, it means we're looking at summary data
                        if balance_val != 0.0 and debit_val == 0.0 and credit_val == 0.0:
                            # For summary rows, try to get from comparison totals
                            if fr.get('level', 0) <= 2:  # Header or sub-header
                                debit_val = debit_prev_totals[i-1] if debit_prev_totals and len(debit_prev_totals) >= i else 0.0
                                credit_val = credit_prev_totals[i-1] if credit_prev_totals and len(credit_prev_totals) >= i else 0.0
                        
                        sheet.write(row, data_col, debit_val, txt)
                        sheet.write(row, data_col + 1, credit_val, txt)
                        sheet.write(row, data_col + 2, balance_val, txt)
                        data_col += 3
                
                # Write prior month data
                if filters.get('comparison_months') and filters.get('comparison_months') > 0:
                    for i in range(1, filters.get('comparison_months') + 1):
                        # Use pre-calculated balance values for comparison periods
                        debit_key = 'debit_month_%d' % i
                        credit_key = 'credit_month_%d' % i
                        balance_key = 'balance_month_%d' % i
                        
                        debit_val = fr.get(debit_key, 0.0)
                        credit_val = fr.get(credit_key, 0.0)
                        balance_val = fr.get(balance_key, 0.0)
                        
                        # If balance values exist but debit/credit don't, it means we're looking at summary data
                        if balance_val != 0.0 and debit_val == 0.0 and credit_val == 0.0:
                            # For summary rows, try to get from comparison totals
                            if fr.get('level', 0) <= 2:  # Header or sub-header
                                debit_val = debit_month_totals[i-1] if debit_month_totals and len(debit_month_totals) >= i else 0.0
                                credit_val = credit_month_totals[i-1] if credit_month_totals and len(credit_month_totals) >= i else 0.0
                        
                        sheet.write(row, data_col, debit_val, txt)
                        sheet.write(row, data_col + 1, credit_val, txt)
                        sheet.write(row, data_col + 2, balance_val, txt)
                        data_col += 3

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
