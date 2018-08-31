# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class BankStatement(models.Model):
    _name = 'bank.statement'

    @api.onchange('journal_id', 'date_from', 'date_to')
    def _get_lines(self):
        self.account_id = self.journal_id.default_debit_account_id.id or self.journal_id.default_credit_account_id.id
        self.currency_id = self.journal_id.currency_id or self.journal_id.company_id.currency_id or \
                           self.env.user.company_id.currency_id
        domain = [('account_id', '=', self.account_id.id), ('statement_date', '=', False)]
        if self.date_from:
            domain += [('date', '>=', self.date_from)]
        if self.date_to:
            domain += [('date', '<=', self.date_to)]
        s_lines = []
        lines = self.env['account.move.line'].search(domain)
        for line in self.statement_lines:
            line.bank_statement_id = self.id
        self.statement_lines = lines


    @api.one
    @api.depends('statement_lines.statement_date')
    def _compute_amount(self):
        print("_compute_amount")
        gl_balance = 0
        bank_balance = 0
        current_update = 0
        domain = [('account_id', '=', self.account_id.id)]
        lines = self.env['account.move.line'].search(domain)
        gl_balance += sum([line.debit - line.credit for line in lines])
        domain += [('id', 'not in', self.statement_lines.ids), ('statement_date', '!=', False)]
        lines = self.env['account.move.line'].search(domain)
        bank_balance += sum([line.balance for line in lines])
        current_update += sum([line.debit - line.credit if line.statement_date else 0 for line in self.statement_lines])

        self.gl_balance = gl_balance
        self.bank_balance = bank_balance + current_update
        self.balance_difference = self.gl_balance - self.bank_balance

    journal_id = fields.Many2one('account.journal', 'Bank', domain=[('type', '=', 'bank')])
    account_id = fields.Many2one('account.account', 'Bank Account')
    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    statement_lines = fields.One2many('account.move.line', 'bank_statement_id')
    # statement_lines = fields.One2many('bank.statement.line', 'bank_statement_id')
    gl_balance = fields.Monetary('Balance as per Company Books', readonly=True, compute='_compute_amount')
    bank_balance = fields.Monetary('Balance as per Bank', readonly=True, compute='_compute_amount')
    balance_difference = fields.Monetary('Amounts not Reflected in Bank', readonly=True, compute='_compute_amount')
    current_update = fields.Monetary('Balance of entries updated now')
    currency_id = fields.Many2one('res.currency', string='Currency')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get('bank.statement'))


# class BankStatementLine(models.Model):
#     _name = 'bank.statement.line'
#
#     bank_statement_id = fields.Many2one('bank.statement', 'Bank Statement')
#     move_id = fields.Many2one('account.move.line', 'Journal Item')
#     date = fields.Date(related='move_id.date', string='Date')
#     name = fields.Char(string="Label", related='move_id.name')
#     ref = fields.Char(related='move_id.ref', string='Reference')
#     partner_id = fields.Many2one('res.partner', string='Partner', related='move_id.partner_id')
#     account_id = fields.Many2one('account.account', 'Account', related='move_id.account_id')
#     debit = fields.Monetary(currency_field='company_currency_id', related='move_id.debit')
#     credit = fields.Monetary(currency_field='company_currency_id', related='move_id.credit')
#     amount_currency = fields.Monetary(related='move_id.amount_currency')
#     currency_id = fields.Many2one('res.currency', string='Currency', related='move_id.currency_id')
#     company_currency_id = fields.Many2one('res.currency', string="Company Currency", readonly=True,
#                                           related='move_id.currency_id')
#     date_maturity = fields.Date(string='Due date', related='move_id.date_maturity')
#     statement_date = fields.Date('Bank.St Date', related='move_id.statement_date')
