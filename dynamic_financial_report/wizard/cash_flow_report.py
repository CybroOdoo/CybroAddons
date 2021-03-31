from odoo import models, fields, api
import io
import json
from odoo.exceptions import UserError, ValidationError
try:
    from odoo.tools.misc import xlsxwriter
except ImportError:
    import xlsxwriter
FETCH_RANGE = 2000


class CashFlow(models.TransientModel):
    _name = "dynamic.cash.flow"
    journal_ids = fields.Many2many(
        "account.journal",
        string="Journals",
    )
    target_moves = fields.Selection(
        [('all', 'All entries'),
         ('posted', 'Posted Only')], string='Target Moves', default='all'
    )
    analytic_ids = fields.Many2many(
        "account.analytic.account", string="Analytic Accounts"
    )
    analytic_tag_ids = fields.Many2many("account.analytic.tag",
                                        string="Analytic Tags")
    account_ids = fields.Many2many(
        "account.account",
        string="Accounts",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
    )
    date_from = fields.Date(
        default='2021-01-01',
        string="Start date",
    )
    date_to = fields.Date(
        default=fields.Date.today(),
        string="End date",
    )
    partner_ids = fields.Many2many('res.partner', string='Partner')
    partner_category_ids = fields.Many2many('res.partner.category',
                                            string='Partner_tags')
    include_details = fields.Boolean(string="Include Details", default=True)
    level = fields.Selection([('summary', 'Summary'),
                              ('consolidated', 'Consolidated'),
                              ('detailed', 'Detailed'),
                              ('very', 'Very Detailedy')],
                                  string='Levels')

    reconciled = fields.Selection([('reconciled', 'Reconciled Only'),
                                   ('unreconciled', 'Unreconciled Only')],
                                  string='Reconcile Type')

    type = fields.Selection(
        [('receivable', 'Receivable Only'),
         ('payable', 'Payable only')],
        string='Account Type', required=False
    )

    def get_journal_lines(self, account, data, offset=0, fetch_range=FETCH_RANGE):
        account_type_id = self.env.ref(
            'account.data_account_type_liquidity').id
        offset_count = offset * fetch_range
        state = """AND am.state = 'posted' """ if data.get('target_moves') == 'posted' else ''
        sql2 = """SELECT aa.name as account_name, aj.name, sum(aml.debit) AS total_debit,
         sum(aml.credit) AS total_credit, COALESCE(SUM(aml.debit - aml.credit),0) AS balance FROM (SELECT am.* FROM account_move as am
             LEFT JOIN account_move_line aml ON aml.move_id = am.id
             LEFT JOIN account_account aa ON aa.id = aml.account_id
             LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
             WHERE am.date BETWEEN '""" + str(
            data.get('date_from')) + """' and '""" + str(
            data.get('date_to')) + """' AND aat.id='""" + str(
            account_type_id) + """' """ + state + """) am
                                 LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                 LEFT JOIN account_account aa ON aa.id = aml.account_id
                                 LEFT JOIN account_journal aj ON aj.id = am.journal_id
                                 WHERE aa.id = """ + str(account.id) + """
                                 GROUP BY aa.name, aj.name"""

        cr = self._cr
        cr.execute(sql2)
        fetched_data = cr.dictfetchall()
        if fetched_data:
            return {
                'account': account.name,
                'id': account.id,
                'journal_lines': fetched_data,
                'offset': offset_count,
            }

    def process_filters(self):
        # To show on report headers
        data = self.get_filters(default_filters={})
        filters = {}
        if data.get('date_from', False):
            filters['date_from'] = data.get('date_from')
        if data.get('date_to', False):
            filters['date_to'] = data.get('date_to')
        if data.get('company_id'):
            filters['company_id'] = data.get('company_id')
        else:
            filters['company_id'] = ''

        if data.get('include_details'):
            filters['include_details'] = True
        else:
            filters['include_details'] = False
        if data.get('target_moves') == 'all':
            filters['target_moves'] = 'All Entries'
        else:
            filters['target_moves'] = 'Posted Only'
        return filters

    def get_filters(self, default_filters={}):
        company_id = self.env.user.company_id
        company_domain = [('company_id', '=', company_id.id)]
        partner_company_domain = [('parent_id', '=', False),
                                  '|',
                                  ('company_id', '=', company_id.id),
                                  ('company_id', '=', False)]

        filter_dict = {
            'account_ids': self.account_ids.ids,
            'company_id': self.company_id and self.company_id.id or False,
            'date_from': self.date_from,
            'date_to': self.date_to,
            'reconciled': self.reconciled,
            'type': self.type,
            'level': self.level,
            'target_moves' : self.target_moves,
            'company_name': self.company_id and self.company_id.name,
        }
        filter_dict.update(default_filters)
        return filter_dict

    def get_data(self):
        filters = self.process_filters()
        account_lines = self.report_data()
        if account_lines['date_from'] is False:
            raise ValidationError("Please attach your document")
        return filters, account_lines

    def get_page_list(self, total_count):
        page_count = int(total_count / FETCH_RANGE)
        if total_count % FETCH_RANGE:
            page_count += 1
        return [i + 1 for i in range(0, int(page_count))] or []

    @api.model
    def create(self, vals):
        ret = super(CashFlow, self).create(vals)
        return ret

    def write(self, vals):
        if vals['date_from'] is False:
            raise ValidationError("Please enter start date")
        if vals['date_to'] is False:
            raise ValidationError("Please enter  date")
        if vals.get('journal_ids'):
            vals.update(
                {'journal_ids': [(4, j) for j in vals.get('journal_ids')]})
        if vals.get('journal_ids') == []:
            vals.update({'journal_ids': [(5,)]})
        if vals.get('analytic_ids'):
            vals.update({'analytic_ids': [(4, j) for j in vals.get('analytic_ids')]})
        if vals.get('analytic_ids') == []:
            vals.update({'analytic_ids': [(5,)]})

        if vals.get('analytic_tag_ids'):
            vals.update({'analytic_tag_ids': [(4, j) for j in vals.get('analytic_tag_ids')]})
        if vals.get('analytic_tag_ids') == []:
            vals.update({'analytic_tag_ids': [(5,)]})
        ret = super(CashFlow, self).write(vals)
        return ret

    def report_data(self):
        cr = self.env.cr
        data = self.get_filters(default_filters={})
        company_id = self.env.user.company_id
        currency = company_id.currency_id
        symbol = company_id.currency_id.symbol
        rounding = company_id.currency_id.rounding
        position = company_id.currency_id.position

        fetched_data = []
        account_res = []
        journal_res = []
        fetched = []

        account_type_id = self.env.ref('account.data_account_type_liquidity').id
        model = self.env.context.get('active_model')
        if data.get('level') == 'summary':
            state = """ WHERE am.state = 'posted' """ if data.get('target_moves') == 'posted' else ''
            query3 = """SELECT to_char(am.date, 'Month') as month_part, extract(YEAR from am.date) as year_part,
                     sum(aml.debit) AS total_debit, sum(aml.credit) AS total_credit,
                             sum(aml.balance) AS total_balance FROM (SELECT am.date, am.id, am.state FROM account_move as am
                             LEFT JOIN account_move_line aml ON aml.move_id = am.id
                             LEFT JOIN account_account aa ON aa.id = aml.account_id
                             LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                             WHERE am.date BETWEEN '""" + str(
                data.get('date_from')) + """' and '""" + str(
                data.get('date_to')) + """' AND aat.id='""" + str(
                account_type_id) + """' ) am
                                         LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                         LEFT JOIN account_account aa ON aa.id = aml.account_id
                                         LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                         """ + state + """GROUP BY month_part,year_part"""
            cr = self._cr
            cr.execute(query3)
            fetched_data = cr.dictfetchall()
        elif data.get('date_from') is False:
            account_type_id = self.env.ref(
                'account.data_account_type_liquidity').id
            state = """AND am.state = 'posted' """ if data.get(
                'level') == 'posted' else ''
            sql = """SELECT DISTINCT aa.id, aa.name,aa.code, sum(aml.debit) AS total_debit,
                                            sum(aml.credit) AS total_credit,sum(aml.balance) AS total_balance
                                             FROM (SELECT am.* FROM account_move as am
                                            LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                            LEFT JOIN account_account aa ON aa.id = aml.account_id
                                            LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                            WHERE am.date BETWEEN '""" + str(
                data.get('date_from')) + """' and '""" + str(
                data.get('date_to')) + """' AND aat.id='""" + str(
                account_type_id) + """' """ + state + """) am
                                                                LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                                                LEFT JOIN account_account aa ON aa.id = aml.account_id
                                                                LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                                                GROUP BY aa.name, aa.code,aa.id"""
            cr = self._cr
            cr.execute(sql)
            fetched_data = cr.dictfetchall()
        elif data.get('date_from') is False and data.get('date_from') != False:
            account_type_id = self.env.ref(
                'account.data_account_type_liquidity').id
            state = """AND am.state = 'posted' """ if data.get(
                'level') == 'posted' else ''
            sql = """SELECT DISTINCT aa.id, aa.name,aa.code, sum(aml.debit) AS total_debit,
                                                       sum(aml.credit) AS total_credit,sum(aml.balance) AS total_balance
                                                        FROM (SELECT am.* FROM account_move as am
                                                       LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                                       LEFT JOIN account_account aa ON aa.id = aml.account_id
                                                       LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                                       WHERE am.date BETWEEN '""" + str(
                data.get('date_from')) + """' and '""" + str(
                data.get('date_to')) + """' AND aat.id='""" + str(
                account_type_id) + """' """ + state + """) am
                                                                           LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                                                           LEFT JOIN account_account aa ON aa.id = aml.account_id
                                                                           LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                                                           GROUP BY aa.name, aa.code,aa.id"""
            cr = self._cr
            cr.execute(sql)
            fetched_data = cr.dictfetchall()
        elif data.get('date_from') is False and data.get('date_from') != False:
            account_type_id = self.env.ref(
                'account.data_account_type_liquidity').id
            state = """AND am.state = 'posted' """ if data.get(
                'level') == 'posted' else ''
            sql = """SELECT DISTINCT aa.id, aa.name,aa.code, sum(aml.debit) AS total_debit,
                                                       sum(aml.credit) AS total_credit,sum(aml.balance) AS total_balance
                                                        FROM (SELECT am.* FROM account_move as am
                                                       LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                                       LEFT JOIN account_account aa ON aa.id = aml.account_id
                                                       LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                                       WHERE am.date BETWEEN '""" + str(
                data.get('date_from')) + """' and '""" + str(
                data.get('date_to')) + """' AND aat.id='""" + str(
                account_type_id) + """' """ + state + """) am
                                                                           LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                                                           LEFT JOIN account_account aa ON aa.id = aml.account_id
                                                                           LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                                                           GROUP BY aa.name, aa.code,aa.id"""
            cr = self._cr
            cr.execute(sql)
            fetched_data = cr.dictfetchall()

        elif data.get('date_to') == " ":
            account_type_id = self.env.ref(
                'account.data_account_type_liquidity').id
            state = """AND am.state = 'posted' """ if data.get(
                'level') == 'posted' else ''
            sql = """SELECT DISTINCT aa.id, aa.name,aa.code, sum(aml.debit) AS total_debit,
                                            sum(aml.credit) AS total_credit,sum(aml.balance) AS total_balance
                                             FROM (SELECT am.* FROM account_move as am
                                            LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                            LEFT JOIN account_account aa ON aa.id = aml.account_id
                                            LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                            WHERE am.date BETWEEN '""" + str(
                data.get('date_from')) + """' and '""" + str(
                data.get('date_to')) + """' AND aat.id='""" + str(
                account_type_id) + """' """ + state + """) am
                                                                LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                                                LEFT JOIN account_account aa ON aa.id = aml.account_id
                                                                LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                                                GROUP BY aa.name, aa.code,aa.id"""
            cr = self._cr
            cr.execute(sql)
            fetched_data = cr.dictfetchall()

        elif data.get('level') == 'consolidated':
            state = """ WHERE am.state = 'posted' """ if data.get('level') == 'posted' else ''
            query2 = """SELECT aat.name, sum(aml.debit) AS total_debit, sum(aml.credit) AS total_credit,
                     sum(aml.balance) AS total_balance FROM (  SELECT am.id, am.state FROM account_move as am
                     LEFT JOIN account_move_line aml ON aml.move_id = am.id
                     LEFT JOIN account_account aa ON aa.id = aml.account_id
                     LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                     WHERE am.date BETWEEN '""" + str(data.get('date_from')) + """' and '""" + str(
                data.get('date_to')) + """' AND aat.id='""" + str(
                account_type_id) + """' ) am
                                 LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                 LEFT JOIN account_account aa ON aa.id = aml.account_id
                                 LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                 """ + state + """GROUP BY aat.name"""
            cr = self._cr
            cr.execute(query2)
            fetched_data = cr.dictfetchall()
        elif data.get('level') == 'detailed':
            state = """ WHERE am.state = 'posted' """ if data.get('level') == 'posted' else ''
            query1 = """SELECT aa.id,aa.name,aa.code, sum(aml.debit) AS total_debit, sum(aml.credit) AS total_credit,
                     sum(aml.balance) AS total_balance FROM (SELECT am.id, am.state FROM account_move as am
                     LEFT JOIN account_move_line aml ON aml.move_id = am.id
                     LEFT JOIN account_account aa ON aa.id = aml.account_id
                     LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                     WHERE am.date BETWEEN '""" + str(
                data.get('date_from')) + """' and '""" + str(
                data.get('date_to')) + """' AND aat.id='""" + str(
                account_type_id) + """' ) am
                                 LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                 LEFT JOIN account_account aa ON aa.id = aml.account_id
                                 LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                 """ + state + """GROUP BY aa.name, aa.code, aa.id"""
            cr = self._cr
            cr.execute(query1)
            fetched_data = cr.dictfetchall()
            for account in self.env['account.account'].search([]):
                child_lines = self.get_journal_lines(account, data)
                if child_lines:
                    journal_res.append(child_lines)

        else:
            account_type_id = self.env.ref(
                'account.data_account_type_liquidity').id
            state = """AND am.state = 'posted' """ if data.get('level') == 'posted' else ''
            sql = """SELECT DISTINCT aa.id, aa.name,aa.code, sum(aml.debit) AS total_debit,
                                         sum(aml.credit) AS total_credit,sum(aml.balance) AS total_balance
                                          FROM (SELECT am.* FROM account_move as am
                                         LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                         LEFT JOIN account_account aa ON aa.id = aml.account_id
                                         LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                         WHERE am.date BETWEEN '""" + str(
                data.get('date_from')) + """' and '""" + str(
                data.get('date_to')) + """' AND aat.id='""" + str(
                account_type_id) + """' """ + state + """) am
                                                             LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                                             LEFT JOIN account_account aa ON aa.id = aml.account_id
                                                             LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                                             GROUP BY aa.name, aa.code,aa.id"""
            cr = self._cr
            cr.execute(sql)
            fetched_data = cr.dictfetchall()
            for account in self.env['account.account'].search([]):
                child_lines = self._get_lines(account, data)
                if child_lines:
                    account_res.append(child_lines)
                journals = self.get_journal_lines(account, data)
                if journals:
                    journal_res.append(journals)

        return {
            'date_from': data.get('date_from'),
            'date_to': data.get('date_to'),
            'levels': data.get('level'),
            'doc_ids': self.ids,
            'doc_model': model,
            'fetched_data': fetched_data,
            'account_res': account_res,
            'journal_res': journal_res,
            'fetched': fetched,
            'company_currency_id': currency,
            'company_currency_symbol': symbol,
            'company_currency_position': position,
        }

    def _get_lines(self, account, data):
        account_type_id = self.env.ref(
            'account.data_account_type_liquidity').id
        state = """AND am.state = 'posted' """ if data.get('target_moves') == 'posted' else ''
        query = """SELECT aml.account_id,aj.id as j_id,aj.name,am.id, am.name as move_name, sum(aml.debit) AS total_debit, 
                sum(aml.credit) AS total_credit, COALESCE(SUM(aml.debit - aml.credit),0) AS balance FROM (SELECT am.* FROM account_move as am
                LEFT JOIN account_move_line aml ON aml.move_id = am.id
                LEFT JOIN account_account aa ON aa.id = aml.account_id
                LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                WHERE am.date BETWEEN '""" + str(
            data.get('date_from')) + """' and '""" + str(
            data.get('date_to')) + """' AND aat.id='""" + str(
            account_type_id) + """' """ + state + """) am
                                    LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                    LEFT JOIN account_account aa ON aa.id = aml.account_id
                                    LEFT JOIN account_journal aj ON aj.id = am.journal_id
                                    WHERE aa.id = """ + str(account.id) + """
                                    GROUP BY am.name, aml.account_id, aj.id, aj.name, am.id"""

        cr = self._cr
        cr.execute(query)
        fetched_data = cr.dictfetchall()

        sql2 = """SELECT aa.name as account_name,aa.id as account_id, aj.id, aj.name, sum(aml.debit) AS total_debit,
                    sum(aml.credit) AS total_credit, sum(aml.balance) AS total_balance FROM (SELECT am.* FROM account_move as am
                        LEFT JOIN account_move_line aml ON aml.move_id = am.id
                        LEFT JOIN account_account aa ON aa.id = aml.account_id
                        LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                        WHERE am.date BETWEEN '""" + str(
            data.get('date_from')) + """' and '""" + str(
            data.get('date_to')) + """' AND aat.id='""" + str(
            account_type_id) + """' """ + state + """) am
                                            LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                            LEFT JOIN account_account aa ON aa.id = aml.account_id
                                            LEFT JOIN account_journal aj ON aj.id = am.journal_id
                                            WHERE aa.id = """ + str(
            account.id) + """
                                            GROUP BY aa.name, aj.name, aj.id,aa.id"""

        cr = self._cr
        cr.execute(sql2)
        fetch_data = cr.dictfetchall()
        if fetched_data:
            return {
                'account': account.name,
                'id': account.id,
                'code': account.code,
                'move_lines': fetched_data,
                'journal_lines': fetch_data,
            }

    def get_xlsx_report(self, data, response, report_data, dfr_data):
        report_data = json.loads(report_data)
        data = json.loads(data)
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        fetched_data = []
        account_res = []
        journal_res = []
        fetched = []
        account_type_id = self.env.ref('account.data_account_type_liquidity').id
        currency_symbol = self.env.user.company_id.currency_id.symbol

        if data['levels'] == 'summary':
            state = """ WHERE am.state = 'posted' """ if data.get('target_move') == 'posted' else ''
            query3 = """SELECT to_char(am.date, 'Month') as month_part, extract(YEAR from am.date) as year_part, sum(aml.debit) AS total_debit, sum(aml.credit) AS total_credit,
                                 sum(aml.balance) AS total_balance FROM (SELECT am.date, am.id, am.state FROM account_move as am
                                 LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                 LEFT JOIN account_account aa ON aa.id = aml.account_id
                                 LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                 WHERE am.date BETWEEN '""" + str(data.get('date_from')) + """' and '""" + str(
                data.get('date_to')) + """' AND aat.id='""" + str(account_type_id) + """' ) am
                                             LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                             LEFT JOIN account_account aa ON aa.id = aml.account_id
                                             LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                             """ + state + """GROUP BY month_part,year_part"""
            cr = self._cr
            cr.execute(query3)
            fetched_data = cr.dictfetchall()

        elif data['levels'] == 'consolidated':
            state = """ WHERE am.state = 'posted' """ if data.get('target_move') == 'posted' else ''
            query2 = """SELECT aat.name, sum(aml.debit) AS total_debit, sum(aml.credit) AS total_credit,
                         sum(aml.balance) AS total_balance FROM (  SELECT am.id, am.state FROM account_move as am
                         LEFT JOIN account_move_line aml ON aml.move_id = am.id
                         LEFT JOIN account_account aa ON aa.id = aml.account_id
                         LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                         WHERE am.date BETWEEN '""" + str(data['date_from']) + """' and '""" + str(
                data.get('date_to')) + """' AND aat.id='""" + str(account_type_id) + """' ) am
                                     LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                     LEFT JOIN account_account aa ON aa.id = aml.account_id
                                     LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                     """ + state + """GROUP BY aat.name"""
            cr = self._cr
            cr.execute(query2)
            fetched_data = cr.dictfetchall()
        elif data['levels'] == 'detailed':
            state = """ WHERE am.state = 'posted' """ if data.get('target_move') == 'posted' else ''
            query1 = """SELECT aa.name,aa.code, sum(aml.debit) AS total_debit, sum(aml.credit) AS total_credit,
                 sum(aml.balance) AS total_balance FROM (SELECT am.id, am.state FROM account_move as am
                 LEFT JOIN account_move_line aml ON aml.move_id = am.id
                 LEFT JOIN account_account aa ON aa.id = aml.account_id
                 LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                 WHERE am.date BETWEEN '""" + str(data['date_from']) + """' and '""" + str(
                data['date_to']) + """' AND aat.id='""" + str(account_type_id) + """' ) am
                             LEFT JOIN account_move_line aml ON aml.move_id = am.id
                             LEFT JOIN account_account aa ON aa.id = aml.account_id
                             LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                             """ + state + """GROUP BY aa.name, aa.code"""
            cr = self._cr
            cr.execute(query1)
            fetched_data = cr.dictfetchall()
            for account in self.env['account.account'].search([]):
                child_lines = self.get_journal_lines(account, data)
                if child_lines:
                    journal_res.append(child_lines)

        else:

            account_type_id = self.env.ref('account.data_account_type_liquidity').id
            state = """AND am.state = 'posted' """ if data.get('target_move') == 'posted' else ''
            sql = """SELECT DISTINCT aa.name,aa.code, sum(aml.debit) AS total_debit,
                                                 sum(aml.credit) AS total_credit FROM (SELECT am.* FROM account_move as am
                                                 LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                                 LEFT JOIN account_account aa ON aa.id = aml.account_id
                                                 LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                                 WHERE am.date BETWEEN '""" + str(data['date_from']) + """' and '""" + str(
                data.get('date_to')) + """' AND aat.id='""" + str(account_type_id) + """' """ + state + """) am
                                                         LEFT JOIN account_move_line aml ON aml.move_id = am.id
                                                         LEFT JOIN account_account aa ON aa.id = aml.account_id
                                                         LEFT JOIN account_account_type aat ON aat.id = aa.user_type_id
                                                         GROUP BY aa.name, aa.code"""

            cr = self._cr
            cr.execute(sql)
            fetched = cr.dictfetchall()
            for account in self.env['account.account'].search([]):
                child_lines = self._get_lines(account, data)
                if child_lines:
                    account_res.append(child_lines)
        logged_users = self.env['res.company']._company_default_get('account.account')
        sheet = workbook.add_worksheet()
        bold = workbook.add_format({'align': 'center',
                                    'bold': True,
                                    'font_size': '10px',
                                    'border': 1})
        date = workbook.add_format({'font_size': '10px'})
        cell_format = workbook.add_format({'bold': True,
                                           'font_size': '10px'})
        head = workbook.add_format({'align': 'center',
                                    'bold': True,
                                    'bg_color': '#D3D3D3',
                                    'font_size': '15px'})
        txt = workbook.add_format({'align': 'left',
                                   'font_size': '10px'})
        txt_left = workbook.add_format({'align': 'left',
                                        'font_size': '10px',
                                        'border': 1})
        txt_center = workbook.add_format({'align': 'center',
                                          'font_size': '10px',
                                          'border': 1})
        amount = workbook.add_format({'align': 'right',
                                      'font_size': '10px',
                                      'border': 1})
        amount_bold = workbook.add_format({'align': 'right',
                                           'bold': True,
                                           'font_size': '10px',
                                           'border': 1})
        txt_bold = workbook.add_format({'align': 'left',
                                        'bold': True,
                                        'font_size': '10px',
                                        'border': 1})

        sheet.set_column('C:C', 30, cell_format)
        sheet.set_column('D:E', 20, cell_format)
        sheet.set_column('F:F', 20, cell_format)
        sheet.merge_range('C3:F5', '')
        sheet.merge_range('C3:F4', 'CASH FLOW STATEMENTS', head)
        sheet.merge_range('C4:F4', '')

        sheet.write('D6', "Date From", cell_format)
        sheet.write('E6', str(data['date_from']), date)
        sheet.write('D7', "Date To", cell_format)
        sheet.write('E7', str(data['date_to']), date)
        if data['levels']:
            sheet.write('D9', "Level", cell_format)
            sheet.write('E9', data.get("levels"), date)
        sheet.write('D8', "Target Moves", cell_format)
        sheet.write('E8', report_data.get("target_moves"), date)
        sheet.write('C11', 'NAME', bold)
        sheet.write('D11', 'CASH IN', bold)
        sheet.write('E11', 'CASH OUT', bold)
        sheet.write('F11', 'BALANCE', bold)

        row_num = 8
        col_num = 2
        fetched_data_list = fetched_data.copy()
        account_res_list = account_res.copy()
        journal_res_list = journal_res.copy()
        fetched_list = fetched.copy()

        for i_rec in fetched_data_list:
            if data['levels'] == 'summary':
                sheet.write(row_num + 1, col_num, str(i_rec['month_part']) + str(int(i_rec['year_part'])), txt_left)
                sheet.write(row_num + 1, col_num + 1, str(i_rec['total_debit']) + str(currency_symbol), amount)
                sheet.write(row_num + 1, col_num + 2, str(i_rec['total_credit']) + str(currency_symbol), amount)
                sheet.write(row_num + 1, col_num + 3, str(i_rec['total_debit'] - i_rec['total_credit']) + str(currency_symbol),
                            amount)
                row_num = row_num + 1
            elif data['levels'] == 'consolidated':
                sheet.write(row_num + 1, col_num, i_rec['name'], txt_left)
                sheet.write(row_num + 1, col_num + 1, str(i_rec['total_debit']) + str(currency_symbol), amount)
                sheet.write(row_num + 1, col_num + 2, str(i_rec['total_credit']) + str(currency_symbol), amount)
                sheet.write(row_num + 1, col_num + 3, str(i_rec['total_debit'] - i_rec['total_credit']) + str(currency_symbol),
                            amount)
                row_num = row_num + 1

        for j_rec in journal_res_list:
            for k in fetched_data_list:
                if k['name'] == j_rec['account']:
                    sheet.write(row_num + 1, col_num, str(k['code']) + str(k['name']), txt_bold)
                    sheet.write(row_num + 1, col_num + 1, str(k['total_debit']) + str(currency_symbol), amount_bold)
                    sheet.write(row_num + 1, col_num + 2, str(k['total_credit']) + str(currency_symbol), amount_bold)
                    sheet.write(row_num + 1, col_num + 3,
                                str(k['total_debit'] - k['total_credit']) + str(currency_symbol), amount_bold)
                    row_num = row_num + 1
            for l_jrec in j_rec['journal_lines']:
                sheet.write(row_num + 1, col_num, l_jrec['name'], txt_left)
                sheet.write(row_num + 1, col_num + 1, str(l_jrec['total_debit']) + str(currency_symbol), amount)
                sheet.write(row_num + 1, col_num + 2, str(l_jrec['total_credit']) + str(currency_symbol), amount)
                sheet.write(row_num + 1, col_num + 3, str(l_jrec['total_debit'] - l_jrec['total_credit']) + str(currency_symbol),
                            amount)
                row_num = row_num + 1

        for j_rec in account_res_list:
            for k in fetched_list:
                if k['name'] == j_rec['account']:
                    sheet.write(row_num + 1, col_num, str(k['code']) + str(k['name']), txt_bold)
                    sheet.write(row_num + 1, col_num + 1, str(k['total_debit']) + str(currency_symbol), amount_bold)
                    sheet.write(row_num + 1, col_num + 2, str(k['total_credit']) + str(currency_symbol), amount_bold)
                    sheet.write(row_num + 1, col_num + 3,
                                str(k['total_debit'] - k['total_credit']) + str(currency_symbol), amount_bold)
                    row_num = row_num + 1
            for l_jrec in j_rec['journal_lines']:
                if l_jrec['account_name'] == j_rec['account']:
                    sheet.write(row_num + 1, col_num, l_jrec['name'], txt_left)
                    sheet.write(row_num + 1, col_num + 1, str(l_jrec['total_debit']) + str(currency_symbol), amount)
                    sheet.write(row_num + 1, col_num + 2, str(l_jrec['total_credit']) + str(currency_symbol), amount)
                    sheet.write(row_num + 1, col_num + 3,
                                str(l_jrec['total_debit'] - l_jrec['total_credit']) + str(currency_symbol),
                                amount)
                    row_num = row_num + 1
                for m_rec in j_rec['move_lines']:
                    if m_rec['name'] == l_jrec['name']:
                        sheet.write(row_num + 1, col_num, m_rec['move_name'], txt_center)
                        sheet.write(row_num + 1, col_num + 1, str(m_rec['total_debit']) + str(currency_symbol), amount)
                        sheet.write(row_num + 1, col_num + 2, str(m_rec['total_credit']) + str(currency_symbol), amount)
                        sheet.write(row_num + 1, col_num + 3,
                                    str(m_rec['total_debit'] - m_rec['total_credit']) + str(currency_symbol),
                                    amount)
                        row_num = row_num + 1

        workbook.close()
        output.seek(0)
        response.stream.write(output.read())
        output.close()