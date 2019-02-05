# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.misc import formatLang


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    bank_statements_source = fields.Selection([('manual', 'Record Manually'), ('undefined', 'Undefined')], string='Bank Feeds',
                                              default='undefined',
                                              help="Defines how the bank statements will be registered")

    @api.multi
    def create_bank_statement(self):
        """return action to create a bank statements. This button should be called only on journals with type =='bank'"""
        self.bank_statements_source = "manual"
        action = self.env.ref('bank_reconciliation.action_bank_statement_wiz').read()[0]
        action.update({
            'context': "{'default_journal_id': " + str(self.id) + "}",
        })
        return action

    @api.multi
    def get_journal_dashboard_datas(self):
        res = super(AccountJournal, self).get_journal_dashboard_datas()
        account_sum = 0.0
        bank_balance = 0.0
        currency = self.currency_id or self.company_id.currency_id
        account_ids = tuple(ac for ac in [self.default_debit_account_id.id, self.default_credit_account_id.id] if ac)
        if account_ids:
            amount_field = 'balance' if (
            not self.currency_id or self.currency_id == self.company_id.currency_id) else 'amount_currency'
            query = """SELECT sum(%s) FROM account_move_line WHERE account_id in %%s AND date <= %%s;""" % (
            amount_field,)
            self.env.cr.execute(query, (account_ids, fields.Date.today(),))
            query_results = self.env.cr.dictfetchall()
            if query_results and query_results[0].get('sum') != None:
                account_sum = query_results[0].get('sum')
            query = """SELECT sum(%s) FROM account_move_line WHERE account_id in %%s AND date <= %%s AND
                        statement_date is not NULL;""" % (amount_field,)
            self.env.cr.execute(query, (account_ids, fields.Date.today(),))
            query_results = self.env.cr.dictfetchall()
            if query_results and query_results[0].get('sum') != None:
                bank_balance = query_results[0].get('sum')
        difference = currency.round(account_sum - bank_balance) + 0.0
        res.update({
            'last_balance': formatLang(self.env, currency.round(bank_balance) + 0.0, currency_obj=currency),
            'difference': formatLang(self.env, currency.round(difference) + 0.0, currency_obj=currency)
        })

        return res
