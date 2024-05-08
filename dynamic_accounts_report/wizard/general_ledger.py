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

import io
import json
from odoo.exceptions import AccessError, UserError, AccessDenied

try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter


class GeneralView(models.TransientModel):
    _inherit = "account.report"
    _name = 'account.general.ledger'

    journal_ids = fields.Many2many('account.journal',
                                   string='Journals', required=True,
                                   default=[])
    account_ids = fields.Many2many("account.account",
                                   string="Accounts")
    account_tag_ids = fields.Many2many("account.account.tag",
                                       string="Account Tags")
    analytic_ids = fields.Many2many("account.analytic.account",
                                    string="Analytic Accounts")
    display_account = fields.Selection(
        [('all', 'All'), ('movement', 'With movements'),
         ('not_zero', 'With balance is not equal to 0')],
        string='Display Accounts', required=True, default='movement')
    titles = fields.Char('Title')
    target_move = fields.Selection([('posted', 'All Posted Entries'),
                                    ('all', 'All Entries')],
                                   string='Target Moves', required=True)
    date_from = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')

    @api.model
    def view_report(self, option, title):
        r = self.env['account.general.ledger'].search([('id', '=', option[0])])
        self = r
        # Create a dictionary for title to journal type mapping
        title_mapping = {
            'General Ledger': 'all',
            'Bank Book': 'bank',
            'Cash Book': 'cash',
        }
        # Get the translated title if available, or fallback to the original
        # title
        trans_title = self.env['ir.actions.client'].with_context(
            lang=self.env.user.lang).search([('name', '=', title)]).name
        title_key = trans_title if trans_title else title
        # Get journal type based on the title mapping, default to 'all' if not
        # found
        if title_key in title_mapping:
            journal_type = title_mapping[title_key]
        else:
            journal_type = 'all'
        company_id = self.env.companies.ids
        # Initialize 'journals' based on journal type
        if journal_type == 'all':
            journals = r.journal_ids or self.env['account.journal'].search(
                [('company_id', 'in', company_id)])
        else:
            journals = self.env['account.journal'].search(
                [('type', '=', journal_type),
                 ('company_id', 'in', company_id)])
        r.write({'titles': title})
        data = {
            'display_account': r.display_account,
            'model': self,
            'journals': journals,
            'target_move': r.target_move,
            'accounts': r.account_ids,
            'account_tags': r.account_tag_ids,
            'analytics': r.analytic_ids,
        }
        if r.date_from:
            data.update({
                'date_from': r.date_from,
            })
        if r.date_to:
            data.update({
                'date_to': r.date_to,
            })
        filters = self.get_filter(option)
        records = self._get_report_value(data)
        currency = self._get_currency()
        default_lg = self.env['ir.http']._get_default_lang().code
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
        report_list = list(merged_data.values())
        return {
            'name': title,
            'type': 'ir.actions.client',
            'tag': 'g_l',
            'filters': filters,
            'report_lines': report_list,
            'debit_total': records['debit_total'],
            'credit_total': records['credit_total'],
            'debit_balance': records['debit_balance'],
            'currency': currency,
        }

    def get_filter(self, option):
        data = self.get_filter_data(option)
        filters = {}
        # filter on journal
        if data.get('journal_ids'):
            filters['journals'] = self.env['account.journal'].browse(
                data.get('journal_ids')).mapped('code')
        else:
            filters['journals'] = ['All']
        if data.get('account_tag_ids', []):
            filters['account_tags'] = data.get('account_tag_ids')
        else:
            filters['account_tags'] = ['All']
        # filter on target move
        if data.get('target_move'):
            filters['target_move'] = data.get('target_move')
        # filter on date range
        if data.get('date_from'):
            filters['date_from'] = data.get('date_from')
        if data.get('date_to'):
            filters['date_to'] = data.get('date_to')
        # filter on accounts
        if data.get('account_ids', []):
            filters['accounts'] = self.env['account.account'].browse(
                data.get('account_ids', [])).mapped('name')
        else:
            filters['accounts'] = ['All']
        # filter on analytic accounts
        if data.get('analytic_ids', []):
            filters['analytics'] = self.env['account.analytic.account'].browse(
                data.get('analytic_ids', [])).mapped('name')
        else:
            filters['analytics'] = ['All']
        filters['company_id'] = ''
        filters['accounts_list'] = data.get('accounts_list')
        filters['account_tag_list'] = data.get('account_tag_list')
        filters['journals_list'] = data.get('journals_list')
        filters['analytic_list'] = data.get('analytic_list')
        filters['company_name'] = data.get('company_name')
        filters['target_move'] = data.get('target_move').capitalize()
        return filters

    def get_filter_data(self, option):
        r = self.env['account.general.ledger'].search([('id', '=', option[0])])
        default_filters = {}
        company_id = self.env.companies
        company_domain = [('company_id', 'in', company_id.ids)]

        account_tags = r.account_tag_ids if r.account_tag_ids else self.env[
            'account.account.tag'].search([])
        analytics_ids = r.analytic_ids if r.analytic_ids else self.env[
            'account.analytic.account'].search(company_domain,
                                               order="company_id, name")
        journal_ids = r.journal_ids if r.journal_ids else self.env[
            'account.journal'].search(company_domain, order="company_id, name")
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
        analytics = []
        o_company = False
        for j in analytics_ids:
            if j.company_id != o_company:
                analytics.append(('divider', j.company_id.name))
                o_company = j.company_id
            analytics.append((j.id, j.name))
        filter_dict = {
            'journal_ids': r.journal_ids.ids,
            'analytic_ids': r.analytic_ids.ids,
            'account_ids': r.account_ids.ids,
            'account_tags': r.account_tag_ids.ids,
            'company_id': company_id.ids,
            'date_from': r.date_from,
            'date_to': r.date_to,
            'target_move': r.target_move,
            'journals_list': journals,
            'accounts_list': accounts,
            'account_tag_list': [(a.id, a.name) for a in account_tags],
            'analytic_list': analytics,
            'company_name': ', '.join(self.env.companies.mapped('name')),
        }
        filter_dict.update(default_filters)
        return filter_dict

    def _get_report_value(self, data):
        docs = data['model']
        display_account = data['display_account']
        init_balance = True
        # journal report values
        journals = data['journals']
        if not journals:
            raise UserError(_("No journals Found! Please Add One"))
        company_id = self.env.companies
        company_domain = [('company_id', 'in', company_id.ids)]
        accounts = self.env['account.account'].search(company_domain)
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

        title = "General Ledger"
        account_line = self.get_accounts_line(list_ac, title)['report_lines']
        acc_line_list = []
        acc_line_list.clear()
        for line in account_line[0]['move_lines']:
            acc_line_list.append(line)
        for res in account_res:
            line_list = []
            line_list.clear()
            for line in acc_line_list:
                if line['account_id'] == res['account_id']:
                    line_list.append(line)
            res['move_lines'] = line_list
        debit_total = 0
        debit_total = sum(x['debit'] for x in account_res)
        credit_total = sum(x['credit'] for x in account_res)
        debit_balance = round(debit_total, 2) - round(credit_total, 2)
        return {
            'doc_ids': self.ids,
            'debit_total': debit_total,
            'credit_total': credit_total,
            'debit_balance': debit_balance,
            'docs': docs,
            'time': time,
            'Accounts': account_res,
        }

    @api.model
    def create(self, vals):
        vals['target_move'] = 'posted'
        vals['name'] = 'eee'
        res = super(GeneralView, self).create(vals)
        return res

    def write(self, vals):
        if vals.get('target_move'):
            vals.update({'target_move': vals.get('target_move').lower()})
        # journal filter
        if vals.get('journal_ids'):
            vals.update({'journal_ids': [(6, 0, vals.get('journal_ids'))]})
        if vals.get('journal_ids') == []:
            vals.update({'journal_ids': [(5,)]})
        # Accounts filter
        if vals.get('account_ids'):
            vals.update(
                {'account_ids': [(6, 0, vals.get('account_ids'))]})
        if vals.get('account_ids') == []:
            vals.update({'account_ids': [(5,)]})
        # Account Tag filter
        if vals.get('account_tag_ids'):
            vals.update({'account_tag_ids': [(6, 0,
                                              vals.get('account_tag_ids'))]})
        if vals.get('account_tag_ids') == []:
            vals.update({'account_tag_ids': [(5,)]})
        # Analytic filter
        if vals.get('analytic_ids'):
            vals.update({'analytic_ids': [(6, 0, vals.get('analytic_ids'))]})
        if vals.get('analytic_ids') == []:
            vals.update({'analytic_ids': [(5,)]})
        res = super(GeneralView, self).write(vals)
        return res

    def _get_accounts(self, accounts, init_balance, display_account, data):
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        move_lines = {x: [] for x in accounts.ids}
        # Prepare initial sql query and Get the initial move lines
        if init_balance and data.get('date_from'):
            init_tables, init_where_clause, init_where_params = MoveLine.with_context(
                date_from=self.env.context.get('date_from'), date_to=False,
                initial_bal=True)._query_get()
            init_wheres = [""]
            if init_where_clause.strip():
                init_wheres.append(init_where_clause.strip())
            init_filters = " AND ".join(init_wheres)
            filters = init_filters.replace('account_move_line__move_id',
                                           'm').replace('account_move_line',
                                                        'l')
            new_filter = filters
            if data['target_move'] == 'posted':
                new_filter += " AND m.state = 'posted'"
            else:
                new_filter += " AND m.state in ('draft','posted')"
            if data.get('date_from'):
                new_filter += " AND l.date < '%s'" % data.get('date_from')
            if data['journals']:
                new_filter += ' AND j.id IN %s' % str(
                    tuple(data['journals'].ids) + tuple([0]))
            if data.get('accounts'):
                WHERE = "WHERE l.account_id IN %s" % str(
                    tuple(data.get('accounts').ids) + tuple([0]))
            else:
                WHERE = "WHERE l.account_id IN %s"
            if data.get('analytics'):
                WHERE += ' AND an.id IN %s' % str(
                    tuple(data.get('analytics').ids) + tuple([0]))
            if data['account_tags']:
                WHERE += ' AND tag IN %s' % str(data.get('account_tags'))
            sql = ('''SELECT
            l.account_id AS account_id,
            a.code AS code,
            a.id AS id,
            a.name AS name,
            ROUND(COALESCE(SUM(l.debit),0),2) AS debit,
            ROUND(COALESCE(SUM(l.credit),0),2) AS credit,
            ROUND(COALESCE(SUM(l.balance),0),2) AS balance,
            anl.keys,
            act.name AS tag
            FROM
                account_move_line l
            LEFT JOIN
                account_move m ON (l.move_id = m.id)
            LEFT JOIN
                res_currency c ON (l.currency_id = c.id)
            LEFT JOIN
                res_partner p ON (l.partner_id = p.id)
            JOIN
                account_journal j ON (l.journal_id = j.id)
            JOIN
                account_account a ON (l.account_id = a.id)
            LEFT JOIN
                account_account_account_tag acct ON (acct.account_account_id = l.account_id)
            LEFT JOIN
                account_account_tag act ON (act.id = acct.account_account_tag_id)
            LEFT JOIN LATERAL (
                SELECT jsonb_array_elements_text(l.analytic_distribution->'ids')::INT AS keys
            ) anl ON true
            LEFT JOIN
                account_analytic_account an ON (anl.keys = an.id) '''+ WHERE + new_filter + '''
            GROUP BY
                l.account_id, a.code, a.id, a.name, anl.keys, act.name''')

            if data.get('accounts'):
                params = tuple(init_where_params)
            else:
                params = (tuple(accounts.ids),) + tuple(init_where_params)
            cr.execute(sql, params)
            for row in cr.dictfetchall():
                row['m_id'] = row['account_id']
                move_lines[row.pop('account_id')].append(row)
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

        if self.analytic_ids:
            WHERE += ' AND an.id IN %s' % str(
                tuple(self.analytic_ids.ids) + tuple([0]))
        if data.get('account_tags'):
            WHERE += ' AND act.id IN %s' % str(
                tuple(data.get('account_tags').ids) + tuple([0]))

        # Get move lines base on sql query and Calculate the total balance
        # of move lines
        sql = ('''SELECT l.account_id AS account_id, a.code AS code, 
                    a.id AS id, a.name AS name,  l.id as line_id,
                    ROUND(COALESCE(SUM(l.debit),0),2) AS debit,
                    ROUND(COALESCE(SUM(l.credit),0),2) AS credit,
                    ROUND(COALESCE(SUM(l.balance),0),2) AS balance,
                    anl.keys, act.name as tag
                    FROM account_move_line l
                    LEFT JOIN account_move m ON (l.move_id = m.id)
                    LEFT JOIN res_currency c ON (l.currency_id = c.id)
                    LEFT JOIN res_partner p ON (l.partner_id = p.id)
                    JOIN account_journal j ON (l.journal_id = j.id)
                    JOIN account_account a ON (l.account_id = a.id)
                    LEFT JOIN account_account_account_tag acct ON 
                    (acct.account_account_id = l.account_id)
                    LEFT JOIN account_account_tag act ON 
                    (act.id = acct.account_account_tag_id)
                    LEFT JOIN LATERAL (
                    SELECT jsonb_object_keys(l.analytic_distribution)::INT 
                    AS keys) anl ON true
                    LEFT JOIN account_analytic_account an 
                    ON (anl.keys = an.id)'''
               + WHERE + new_final_filter + ''' GROUP BY l.account_id, 
                   a.code,a.id,a.name,anl.keys, act.name, l.id''')
        if data.get('accounts'):
            params = tuple(where_params)
        else:
            params = (tuple(accounts.ids),) + tuple(where_params)
        cr.execute(sql, params)
        account_res = cr.dictfetchall()
        unique_line_ids = set()
        filtered_records = []
        for record in account_res:
            line_id = record['line_id']
            if line_id not in unique_line_ids:
                unique_line_ids.add(line_id)
                filtered_records.append(record)
        return filtered_records

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
                          self.env.company.currency_id.position, lang]
        return currency_array

    def get_accounts_line(self, account_id, title):
        # to get the english translation of the title
        record_id = self.env['ir.actions.client'].with_context(
            lang=self.env.user.lang). \
            search([('name', '=', title)]).id
        trans_title = self.env['ir.actions.client'].with_context(
            lang='en_US').search([('id', '=', record_id)]).name
        company_id = self.env.companies.ids
        # Journal based account lines
        if self.journal_ids:
            journals = self.journal_ids
        else:
            journals = self.env['account.journal'].search(
                [('company_id', 'in', company_id)])
        if title == 'General Ledger' or trans_title == 'General Ledger':
            if self.journal_ids:
                journals = self.journal_ids
            else:
                journals = self.env['account.journal'].search(
                    [('company_id', 'in', company_id)])
        if title == 'Bank Book' or trans_title == 'Bank Book':
            journals = self.env['account.journal'].search(
                [('type', '=', 'bank'), ('company_id', 'in', company_id)])
        if title == 'Cash Book' or trans_title == 'Cash Book':
            journals = self.env['account.journal'].search(
                [('type', '=', 'cash'), ('company_id', 'in', company_id)])
        # account based move lines
        if account_id:
            accounts = self.env['account.account'].search(
                [('id', '=', account_id)])
        else:
            company_id = self.env.companies
            company_domain = [('company_id', 'in', company_id.ids)]
            accounts = self.env['account.account'].search(company_domain)
        cr = self.env.cr
        MoveLine = self.env['account.move.line']
        move_lines = {x: [] for x in accounts.ids}

        # Prepare initial sql query and Get the initial move lines
        if self.date_from:
            init_tables, init_where_clause, init_where_params = MoveLine.with_context(
                date_from=self.env.context.get('date_from'), date_to=False,
                initial_bal=True)._query_get()
        tables, where_clause, where_params = MoveLine._query_get()
        wheres = [""]
        if where_clause.strip():
            wheres.append(where_clause.strip())
        final_filters = " AND ".join(wheres)
        final_filters = final_filters.replace('account_move_line__move_id',
                                              'm').replace(
            'account_move_line', 'l')
        new_final_filter = final_filters
        if self.target_move == 'posted':
            new_final_filter += " AND m.state = 'posted'"
        else:
            new_final_filter += " AND m.state in ('draft','posted')"
        if self.date_from:
            new_final_filter += " AND l.date >= '%s'" % self.date_from
        if self.date_to:
            new_final_filter += " AND l.date <= '%s'" % self.date_to
        if journals:
            new_final_filter += ' AND j.id IN %s' % str(
                tuple(journals.ids) + tuple([0]))
        if accounts:
            WHERE = "WHERE l.account_id IN %s" % str(
                tuple(accounts.ids) + tuple([0]))
        else:
            WHERE = "WHERE l.account_id IN %s"
        if self.analytic_ids:
            WHERE += ' AND an.id IN %s' % str(
                tuple(self.analytic_ids.ids) + tuple([0]))

        # Get move lines base on sql query and Calculate the total balance of
        # move lines
        # print(new_final_filter)
        sql = ('''SELECT DISTINCT ON (l.id) l.id AS lid,m.id AS move_id, l.account_id AS account_id,
                l.date AS ldate, j.code AS lcode, l.currency_id, l.amount_currency,
                l.ref AS lref, l.name AS lname, COALESCE(l.debit,0) AS debit, 
                COALESCE(l.credit,0) AS credit, COALESCE(SUM(l.balance),0) AS balance,
                m.name AS move_name, c.symbol AS currency_code, 
                p.name AS partner_name, anl.keys
                FROM account_move_line l
                JOIN account_move m ON (l.move_id=m.id)
                LEFT JOIN res_currency c ON (l.currency_id=c.id)
                LEFT JOIN res_partner p ON (l.partner_id=p.id)
                LEFT JOIN LATERAL (
                SELECT jsonb_object_keys(l.analytic_distribution)::INT 
                AS keys) anl ON true
                LEFT JOIN account_analytic_account an ON (anl.keys = an.id)                
                JOIN account_journal j ON (l.journal_id=j.id)
                JOIN account_account a ON (l.account_id = a.id) '''
               + WHERE + new_final_filter + ''' GROUP BY l.id, m.id,  
               l.account_id, l.date, j.code, l.currency_id, l.amount_currency,
               l.ref, l.name, m.name, c.symbol, c.position, p.name, anl.keys''')

        params = tuple(where_params)
        # print('new_final_filter', sql, params)
        cr.execute(sql, params)
        account_ress = cr.dictfetchall()
        i = 0
        # Calculate the debit, credit and balance for Accounts
        account_res = []
        for account in accounts:
            currency = (account.currency_id and account.currency_id or
                        account.company_id.currency_id)
            res = dict((fn, 0.0) for fn in ['credit', 'debit', 'balance'])
            res['code'] = account.code
            res['name'] = account.name
            res['id'] = account.id
            res['move_lines'] = account_ress
            account_res.append(res)
        currency = self._get_currency()
        return {
            'report_lines': account_res,
            'currency': currency,
        }

    def get_dynamic_xlsx_report(self, data, response, report_data, dfr_data):
        user = self.env.user
        user_language = user.lang
        report_data_main = json.loads(report_data)
        output = io.BytesIO()
        name_data = json.loads(dfr_data)
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
        txt_l = workbook.add_format(
            {'font_size': '10px', 'border': 1, 'bold': True})
        sheet.merge_range('A2:J3',
                          filters.get('company_name') + ':' + name_data.get(
                              'name'), head)
        date_head = workbook.add_format({'align': 'center', 'bold': True,
                                         'font_size': '10px'})
        date_style = workbook.add_format({'align': 'center',
                                          'font_size': '10px'})
        if filters.get('date_from'):
            sheet.merge_range('B4:C4', 'From: ' + filters.get('date_from'),
                              date_head)
        if filters.get('date_to'):
            sheet.merge_range('H4:I4', 'To: ' + filters.get('date_to'),
                              date_head)
        sheet.merge_range('A5:J6', '  Journals: ' + ', '.join(
            [lt or '' for lt in
             filters['journals']]) + '  Accounts: ' + ', '.join(
            [lt or '' for lt in
             filters['accounts']]) + '  Account Tags: ' + ', '.join(
            [at or '' for at in
             filters['analytics']]) + '  Target Moves : ' + filters.get(
            'target_move'), date_head)
        sheet.write('A8', 'Code', sub_heading)
        sheet.write('B8', 'Amount', sub_heading)
        sheet.write('C8', 'Date', sub_heading)
        sheet.write('D8', 'JRNL', sub_heading)
        sheet.write('E8', 'Partner', sub_heading)
        sheet.write('F8', 'Move', sub_heading)
        sheet.write('G8', 'Entry Label', sub_heading)
        sheet.write('H8', 'Debit', sub_heading)
        sheet.write('I8', 'Credit', sub_heading)
        sheet.write('J8', 'Balance', sub_heading)
        row = 6
        col = 0
        sheet.set_column(8, 0, 15)
        sheet.set_column('B:B', 40)
        sheet.set_column(8, 2, 15)
        sheet.set_column(8, 3, 15)
        sheet.set_column(8, 4, 15)
        sheet.set_column(8, 5, 15)
        sheet.set_column(8, 6, 50)
        sheet.set_column(8, 7, 26)
        sheet.set_column(8, 8, 15)
        sheet.set_column(8, 9, 15)
        for rec_data in report_data_main:
            language = user_language if user_language in rec_data[
                'name'] else 'en_US'
            row += 1
            sheet.write(row + 1, col, rec_data['code'], txt)
            if isinstance(rec_data['name'], dict):
                sheet.write(row + 1, col + 1, rec_data['name'][language], txt)
            else:
                sheet.write(row + 1, col + 1, rec_data['name'], txt)
            sheet.write(row + 1, col + 2, '', txt)
            sheet.write(row + 1, col + 3, '', txt)
            sheet.write(row + 1, col + 4, '', txt)
            sheet.write(row + 1, col + 5, '', txt)
            sheet.write(row + 1, col + 6, '', txt)
            sheet.write(row + 1, col + 7, rec_data['debit'], txt)
            sheet.write(row + 1, col + 8, rec_data['credit'], txt)
            sheet.write(row + 1, col + 9, rec_data['balance'], txt)
            for line_data in rec_data['move_lines']:
                row += 1
                sheet.write(row + 1, col, '', txt)
                sheet.write(row + 1, col + 1, '', txt)
                sheet.write(row + 1, col + 2, line_data.get('ldate'), txt)
                sheet.write(row + 1, col + 3, line_data.get('lcode'), txt)
                sheet.write(row + 1, col + 4, line_data.get('partner_name'),
                            txt)
                sheet.write(row + 1, col + 5, line_data.get('move_name'), txt)
                sheet.write(row + 1, col + 6, line_data.get('lname'), txt)
                sheet.write(row + 1, col + 7, line_data.get('debit'), txt)
                sheet.write(row + 1, col + 8, line_data.get('credit'), txt)
                sheet.write(row + 1, col + 9, line_data.get('balance'), txt)
        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()
