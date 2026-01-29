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
    _inherit = "account.common.report"
    _name = 'account.general.ledger'

    journal_ids = fields.Many2many('account.journal',

                                   string='Journals', required=True,
                                   default=[])
    account_ids = fields.Many2many(
        "account.account",
        string="Accounts",
    )
    account_tag_ids = fields.Many2many("account.account.tag",
                                       string="Account Tags")

    analytic_ids = fields.Many2many(
        "account.analytic.account", string="Analytic Accounts"
    )
    analytic_tag_ids = fields.Many2many("account.analytic.tag",
                                        string="Analytic Tags")

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
        new_title = ''
        trans_title = self.env['ir.translation'].search([('value', '=', title),
                                                         ('module', '=',
                                                          'dynamic_accounts_report')],
                                                        limit=1).src
        company_id = self.env.companies.ids
        if r.journal_ids:
            journals = r.journal_ids
        else:
            journals = self.env['account.journal'].search(
                [('company_id', 'in', company_id)])
        if title == 'General Ledger' or trans_title == 'General Ledger':
            if r.journal_ids:
                journals = r.journal_ids
            else:
                journals = self.env['account.journal'].search(
                    [('company_id', 'in', company_id)])
            new_title = title
        if title == 'Bank Book' or trans_title == 'Bank Book':
            journals = self.env['account.journal'].search(
                [('type', '=', 'bank'), ('company_id', 'in', company_id)])

            new_title = title
        if title == 'Cash Book' or trans_title == 'Cash Book':
            journals = self.env['account.journal'].search(
                [('type', '=', 'cash'), ('company_id', 'in', company_id)])
            new_title = title
        r.write({
            'titles': new_title,
        })
        data = {
            'display_account': r.display_account,
            'model': self,
            'journals': journals,
            'target_move': r.target_move,
            'accounts': r.account_ids,
            'account_tags': r.account_tag_ids,
            'analytics': r.analytic_ids,
            'analytic_tags': r.analytic_tag_ids,

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
        records = self._get_report_values(data)
        currency = self._get_currency()
        return {
            'name': new_title,
            'type': 'ir.actions.client',
            'tag': 'g_l',
            'filters': filters,
            'report_lines': records['Accounts'],
            'debit_total': records['debit_total'],
            'credit_total': records['credit_total'],
            'debit_balance': records['debit_balance'],
            'currency': currency,
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
        if data.get('account_tag_ids', []):
            filters['account_tags'] = data.get('account_tag_ids')
        else:
            filters['account_tags'] = ['All']
        if data.get('target_move'):
            filters['target_move'] = data.get('target_move')
        if data.get('date_from'):
            filters['date_from'] = data.get('date_from')
        if data.get('date_to'):
            filters['date_to'] = data.get('date_to')
        if data.get('analytic_ids', []):
            filters['analytics'] = self.env['account.analytic.account'].browse(
                data.get('analytic_ids', [])).mapped('name')
        else:
            filters['analytics'] = ['All']
        if data.get('analytic_tag_ids', []):
            filters['account_tags'] = self.env['account.account.tag'].browse(
                data.get('account_tag_ids', [])).mapped('name')
        else:
            filters['analytic_tags'] = ['All']

        filters['company_id'] = ''
        filters['accounts_list'] = data.get('accounts_list')
        filters['account_tag_list'] = data.get('account_tag_list')
        filters['journals_list'] = data.get('journals_list')
        filters['analytic_list'] = data.get('analytic_list')
        filters['analytic_tag_list'] = data.get('analytic_tag_list')
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
        analytics = r.analytic_ids if r.analytic_ids else self.env[
            'account.analytic.account'].search(
            company_domain)
        analytic_tags = r.analytic_tag_ids if r.analytic_tag_ids else self.env[
            'account.analytic.tag'].search([])

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

        filter_dict = {
            'journal_ids': r.journal_ids.ids,
            'analytic_ids': r.analytic_ids.ids,
            'analytic_tag_ids': r.analytic_tag_ids.ids,
            'account_ids': r.account_ids.ids,
            'account_tag_ids': r.account_tag_ids.ids,
            'company_id': company_id.ids,
            'date_from': r.date_from,
            'date_to': r.date_to,
            'target_move': r.target_move,
            # 'journals_list': [(j.id, j.name, j.code) for j in journals],
            'journals_list': journals,
            # 'accounts_list': [(a.id, a.name) for a in accounts],
            'accounts_list': accounts,
            'account_tag_list': [(a.id, a.name) for a in account_tags],
            'analytic_list': [(anl.id, anl.name) for anl in analytics],
            'analytic_tag_list': [(anltag.id, anltag.name) for anltag in
                                  analytic_tags],
            'company_name': ', '.join(self.env.companies.mapped('name')),
        }
        filter_dict.update(default_filters)
        return filter_dict

    def _get_report_values(self, data):

        docs = data['model']

        display_account = data['display_account']
        init_balance = True
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
        res = super(GeneralView, self).create(vals)
        return res

    def write(self, vals):
        if vals.get('target_move'):
            vals.update({'target_move': vals.get('target_move').lower()})
        if vals.get('journal_ids'):
            vals.update({'journal_ids': [(6, 0, vals.get('journal_ids'))]})
        if vals.get('journal_ids') == []:
            vals.update({'journal_ids': [(5,)]})
        if vals.get('account_ids'):
            vals.update(
                {'account_ids': [(4, j) for j in vals.get('account_ids')]})
        if vals.get('account_ids') == []:
            vals.update({'account_ids': [(5,)]})
        if vals.get('account_tag_ids'):
            vals.update({'account_tag_ids': [(4, j) for j in
                                             vals.get('account_tag_ids')]})
        if vals.get('account_tag_ids') == []:
            vals.update({'account_tag_ids': [(5,)]})
        if vals.get('analytic_ids'):
            vals.update(
                {'analytic_ids': [(4, j) for j in vals.get('analytic_ids')]})
        if vals.get('analytic_ids') == []:
            vals.update({'analytic_ids': [(5,)]})
        if vals.get('analytic_tag_ids') == []:
            vals.update({'analytic_tag_ids': [(4, j) for j in
                                              vals.get('analytic_tag_ids')]})
        if vals.get('analytic_tag_ids') == []:
            vals.update({'analytic_tag_ids': [(5,)]})
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
                WHERE += ' AND anl.id IN %s' % str(
                    tuple(data.get('analytics').ids) + tuple([0]))
            if data.get('analytic_tags'):
                WHERE += ' AND anltag.account_analytic_tag_id IN %s' % str(
                    tuple(data.get('analytic_tags').ids) + tuple([0]))

            sql = ("""SELECT 0 AS lid, l.account_id AS account_id, '' AS ldate, '' AS lcode, 0.0 AS amount_currency, '' AS lref, 'Initial Balance' AS lname, COALESCE(SUM(l.debit),0.0) AS debit, COALESCE(SUM(l.credit),0.0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance, '' AS lpartner_id,\
                        '' AS move_name, '' AS mmove_id, '' AS currency_code,\
                        NULL AS currency_id,\
                        '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,\
                        '' AS partner_name\
                        FROM account_move_line l\
                        LEFT JOIN account_move m ON (l.move_id=m.id)\
                        LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                        LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                        LEFT JOIN account_move i ON (m.id =i.id)\
                        LEFT JOIN account_account_tag_account_move_line_rel acc ON (acc.account_move_line_id=l.id)
                        LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                        LEFT JOIN account_analytic_tag_account_move_line_rel anltag ON (anltag.account_move_line_id=l.id)
                        JOIN account_journal j ON (l.journal_id=j.id)"""
                   + WHERE + new_filter + ' GROUP BY l.account_id')
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
        if data.get('analytics'):
            WHERE += ' AND anl.id IN %s' % str(
                tuple(data.get('analytics').ids) + tuple([0]))

        if data.get('analytic_tags'):
            WHERE += ' AND anltag.account_analytic_tag_id IN %s' % str(
                tuple(data.get('analytic_tags').ids) + tuple([0]))

        # Get move lines base on sql query and Calculate the total balance of move lines
        sql = ('''SELECT l.account_id AS account_id, a.code AS code,a.id AS id, a.name AS name, ROUND(COALESCE(SUM(l.debit),0),2) AS debit, ROUND(COALESCE(SUM(l.credit),0),2) AS credit, ROUND(COALESCE(SUM(l.balance),0),2) AS balance

                            FROM account_move_line l\
                            JOIN account_move m ON (l.move_id=m.id)\
                            LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                            LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                            LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                            LEFT JOIN account_account_tag_account_move_line_rel acc ON (acc.account_move_line_id=l.id)
                            LEFT JOIN account_analytic_tag_account_move_line_rel anltag ON (anltag.account_move_line_id=l.id)
                            JOIN account_journal j ON (l.journal_id=j.id)\
                            JOIN account_account a ON (l.account_id = a.id) '''
               + WHERE + new_final_filter + ''' GROUP BY l.account_id, a.code, a.name, a.id''')
        if data.get('accounts'):
            params = tuple(where_params)
        else:
            params = (tuple(accounts.ids),) + tuple(where_params)
        cr.execute(sql, params)
        account_res = cr.dictfetchall()

        return account_res

        # for row in cr.dictfetchall():
        #     balance = 0
        #     for line in move_lines.get(row['account_id']):
        #         balance += round(line['debit'],2) - round(line['credit'],2)
        #     row['balance'] += round(balance,2)
        #     row['m_id'] = row['account_id']
        #     move_lines[row.pop('account_id')].append(row)
        #
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
        #         res['debit'] += round(line['debit'],2)
        #         res['credit'] += round(line['credit'],2)
        #         res['balance'] = round(line['balance'],2)
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
        lang = self.env.user.lang
        if not lang:
            lang = 'en_US'
        lang = lang.replace("_", '-')
        currency_array = [self.env.company.currency_id.symbol,
                          self.env.company.currency_id.position, lang]
        return currency_array

    def get_accounts_line(self, account_id, title):
        trans_title = self.env['ir.translation'].search([('value', '=', title),
                                                         ('module', '=',
                                                          'dynamic_accounts_report')],
                                                        limit=1).src
        company_id = self.env.companies.ids
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
                date_from=self.date_from, date_to=False,
                initial_bal=True)._query_get()
            init_wheres = [""]
            if init_where_clause.strip():
                init_wheres.append(init_where_clause.strip())
            init_filters = " AND ".join(init_wheres)
            filters = init_filters.replace('account_move_line__move_id',
                                           'm').replace('account_move_line',
                                                        'l')
            new_filter = filters
            if self.target_move == 'posted':
                new_filter += " AND m.state = 'posted'"
            else:
                new_filter += " AND m.state in ('draft','posted')"
            if self.date_from:
                new_filter += " AND l.date < '%s'" % self.date_from
            if journals:
                new_filter += ' AND j.id IN %s' % str(
                    tuple(journals.ids) + tuple([0]))
            if accounts:
                WHERE = " WHERE l.account_id IN %s" % str(
                    tuple(accounts.ids) + tuple([0]))
            else:
                WHERE = "WHERE l.account_id IN %s"
            if self.analytic_ids:
                WHERE += ' AND anl.id IN %s' % str(
                    tuple(self.analytic_ids.ids) + tuple([0]))
            if self.analytic_tag_ids:
                WHERE += ' AND anltag.account_analytic_tag_id IN %s' % str(
                    tuple(self.analytic_tag_ids.ids) + tuple([0]))

            sql = ("""SELECT 0 AS lid, l.account_id AS account_id, '' AS ldate, '' AS lcode, 0.0 AS amount_currency, '' AS lref, 'Initial Balance' AS lname, COALESCE(SUM(l.debit),0.0) AS debit, COALESCE(SUM(l.credit),0.0) AS credit, COALESCE(SUM(l.debit),0) - COALESCE(SUM(l.credit), 0) as balance, '' AS lpartner_id,\
                        '' AS move_name, '' AS mmove_id, '' AS currency_code,\
                        NULL AS currency_id,\
                        '' AS invoice_id, '' AS invoice_type, '' AS invoice_number,\
                        '' AS partner_name\
                        FROM account_move_line l\
                        LEFT JOIN account_move m ON (l.move_id=m.id)\
                        LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                        LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                        LEFT JOIN account_move i ON (m.id =i.id)\
                        LEFT JOIN account_account_tag_account_move_line_rel acc ON (acc.account_move_line_id=l.id)
                        LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                        LEFT JOIN account_analytic_tag_account_move_line_rel anltag ON (anltag.account_move_line_id=l.id)
                        JOIN account_journal j ON (l.journal_id=j.id)"""
                   + WHERE + new_filter + ' GROUP BY l.account_id')
            if self.account_ids:
                params = tuple(init_where_params)
            else:
                # params = (tuple(accounts.ids)) + tuple(init_where_params)
                params = init_where_params
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
            WHERE += ' AND anl.id IN %s' % str(
                tuple(self.analytic_ids.ids) + tuple([0]))

        if self.analytic_tag_ids:
            WHERE += ' AND anltag.account_analytic_tag_id IN %s' % str(
                tuple(self.analytic_tag_ids.ids) + tuple([0]))

        # Get move lines base on sql query and Calculate the total balance of move lines
        sql = ('''SELECT l.id AS lid,m.id AS move_id, l.account_id AS account_id, l.date AS ldate, j.code AS lcode, l.currency_id, l.amount_currency, l.ref AS lref, l.name AS lname, COALESCE(SUM(l.debit),0) AS debit, COALESCE(SUM(l.credit),0) AS credit, COALESCE(SUM(l.balance),0) AS balance,\
                    m.name AS move_name, c.symbol AS currency_code, p.name AS partner_name\
                    FROM account_move_line l\
                    JOIN account_move m ON (l.move_id=m.id)\
                    LEFT JOIN res_currency c ON (l.currency_id=c.id)\
                    LEFT JOIN res_partner p ON (l.partner_id=p.id)\
                    LEFT JOIN account_analytic_account anl ON (l.analytic_account_id=anl.id)
                    LEFT JOIN account_account_tag_account_move_line_rel acc ON (acc.account_move_line_id=l.id)
                    LEFT JOIN account_analytic_tag_account_move_line_rel anltag ON (anltag.account_move_line_id=l.id)
                    JOIN account_journal j ON (l.journal_id=j.id)\
                    JOIN account_account a ON (l.account_id = a.id) '''
               + WHERE + new_final_filter + ''' GROUP BY l.id, m.id,  l.account_id, l.date, j.code, l.currency_id, l.amount_currency, l.ref, l.name, m.name, c.symbol, c.position, p.name ORDER BY l.date''')

        params = tuple(where_params)
        cr.execute(sql, params)
        account_ress = cr.dictfetchall()
        i = 0
        # Calculate the debit, credit and balance for Accounts
        account_res = []
        for account in accounts:
            currency = account.currency_id and account.currency_id or account.company_id.currency_id
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
        # sheet.merge_range('A5:J6', 'Journals: ' + ', '.join(
        #     [lt or '' for lt in filters['journals']]) + '  Target Moves: ' + filters.get('target_move'), date_head)

        sheet.merge_range('A5:J6', '  Journals: ' + ', '.join(
            [lt or '' for lt in
             filters['journals']]) + '  Accounts: ' + ', '.join(
            [lt or '' for lt in
             filters['accounts']]) + '  Account Tags: ' + ', '.join(
            [lt or '' for lt in
             filters['analytic_tags']]) + '  Analytic: ' + ', '.join(
            [at or '' for at in
             filters['analytics']]) + '  Target Moves : ' + filters.get(
            'target_move'),
                          date_head)

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

            row += 1
            sheet.write(row + 1, col, rec_data['code'], txt)
            sheet.write(row + 1, col + 1, rec_data['name'], txt)
            sheet.write(row + 1, col + 2, '', txt)
            sheet.write(row + 1, col + 3, '', txt)
            sheet.write(row + 1, col + 4, '', txt)
            sheet.write(row + 1, col + 5, '', txt)
            sheet.write(row + 1, col + 6, '', txt)

            sheet.write(row + 1, col + 7, rec_data['debit'], txt)
            sheet.write(row + 1, col + 8, rec_data['credit'], txt)
            sheet.write(row + 1, col + 9, rec_data['balance'], txt)
            if rec_data.get('move_lines'):
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
