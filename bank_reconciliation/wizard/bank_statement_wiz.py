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
    gl_balance = fields.Monetary('Balance as per Company Books', readonly=True, compute='_compute_amount')
    bank_balance = fields.Monetary('Balance as per Bank', readonly=True, compute='_compute_amount')
    balance_difference = fields.Monetary('Amounts not Reflected in Bank', readonly=True, compute='_compute_amount')
    current_update = fields.Monetary('Balance of entries updated now')
    currency_id = fields.Many2one('res.currency', string='Currency')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env['res.company']._company_default_get('bank.statement'))


