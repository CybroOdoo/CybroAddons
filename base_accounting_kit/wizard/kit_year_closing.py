# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class KitYearClosing(models.TransientModel):
    """Year-end Closing (P2.3-c), opened by Close Year on a fiscal year:
    the kit's checks, then an entry moving the year's result from Current
    Year Earnings (core unaffected earnings account) to Retained Earnings,
    then the Global Lock Date (``kit.fiscal.year._close``).

    The profit and loss accounts are not cleared: the Profit and Loss of
    the year keeps its figures and the Balance Sheet's total equity does
    not change; Retained Earnings gets the result."""
    _name = 'kit.year.closing'
    _description = 'Year-end Closing'

    fiscal_year_id = fields.Many2one('kit.fiscal.year', required=True,
                                     readonly=True, ondelete='cascade')
    company_id = fields.Many2one(related='fiscal_year_id.company_id')
    currency_id = fields.Many2one(related='company_id.currency_id')
    date_from = fields.Date(related='fiscal_year_id.date_from')
    date_to = fields.Date(related='fiscal_year_id.date_to')

    # Checks (counts; the first two block the closing)
    open_year_count = fields.Integer(compute='_compute_checks')
    unreconciled_count = fields.Integer(compute='_compute_checks')
    draft_count = fields.Integer(compute='_compute_checks')
    depreciation_count = fields.Integer(compute='_compute_checks')
    recurring_count = fields.Integer(compute='_compute_checks')
    has_blocking = fields.Boolean(compute='_compute_checks')
    has_warnings = fields.Boolean(compute='_compute_checks')
    close_anyway = fields.Boolean(
        string="Close anyway",
        help="Close although some warnings are left (draft entries, "
             "depreciation or recurring invoices not generated).")

    # Result of the year
    income = fields.Monetary(compute='_compute_result', string="Income")
    expense = fields.Monetary(compute='_compute_result', string="Expenses")
    result = fields.Monetary(compute='_compute_result', string="Result",
                             help="Profit (positive) or loss (negative).")
    post_entry = fields.Boolean(string="Post closing entry", default=True)
    earnings_account_id = fields.Many2one(
        'account.account', string="Current Year Earnings",
        compute='_compute_earnings_account')
    retained_account_id = fields.Many2one(
        'account.account', string="Retained Earnings Account",
        domain="[('account_type', '=', 'equity'), ('company_ids', 'parent_of', company_id)]",
        help="Equity account receiving the result of the year.")
    journal_id = fields.Many2one(
        'account.journal', string="Journal",
        domain="[('type', '=', 'general'), ('company_id', '=', company_id)]")

    @api.model
    def default_get(self, field_list):
        res = super().default_get(field_list)
        year = self.env['kit.fiscal.year'].browse(
            res.get('fiscal_year_id') or self.env.context.get('active_id'))
        if year:
            company = year.company_id
            res['fiscal_year_id'] = year.id
            res.setdefault('retained_account_id',
                           company.kit_retained_earnings_account_id.id)
            res.setdefault('journal_id', self.env['account.journal'].search([
                ('type', '=', 'general'), ('company_id', '=', company.id)],
                limit=1).id)
        return res

    # ------------------------------------------------------------------
    def _companies(self):
        return self.env['res.company'].search(
            [('id', 'child_of', self.company_id.ids)])

    def _check_domains(self):
        """Domain and model of each check (used by the counts and by the
        Open buttons)."""
        self.ensure_one()
        companies = self._companies().ids
        return {
            'open_year': ('kit.fiscal.year', [
                ('company_id', '=', self.company_id.id), ('state', '=', 'open'),
                ('date_to', '<', self.date_from)]),
            'unreconciled': ('account.bank.statement.line',
                             self.company_id._get_unreconciled_statement_lines_domain(self.date_to)),
            'draft': ('account.move', [
                ('company_id', 'in', companies), ('state', '=', 'draft'),
                ('date', '>=', self.date_from), ('date', '<=', self.date_to)]),
            'depreciation': ('account.asset.depreciation.line', [
                ('asset_id.company_id', 'in', companies), ('asset_id.state', '=', 'open'),
                ('move_id', '=', False), ('depreciation_date', '<=', self.date_to)]),
            'recurring': ('account.recurring.invoice', [
                ('company_id', 'in', companies), ('state', '=', 'running'),
                ('date_next', '<=', self.date_to)]),
        }

    @api.depends('fiscal_year_id')
    def _compute_checks(self):
        for wizard in self:
            counts = {key: self.env[model].search_count(domain) if wizard.fiscal_year_id else 0
                      for key, (model, domain) in (wizard._check_domains().items()
                                                   if wizard.fiscal_year_id else [])}
            for key in ('open_year', 'unreconciled', 'draft', 'depreciation', 'recurring'):
                wizard['%s_count' % key] = counts.get(key, 0)
            wizard.has_blocking = bool(wizard.open_year_count or wizard.unreconciled_count)
            wizard.has_warnings = bool(wizard.draft_count or wizard.depreciation_count
                                       or wizard.recurring_count)

    def _result_by_account(self):
        """Balance of each profit and loss account over the year (posted
        entries of the company and its branches)."""
        self.ensure_one()
        groups = self.env['account.move.line']._read_group([
            ('company_id', 'in', self._companies().ids),
            ('parent_state', '=', 'posted'),
            ('date', '>=', self.date_from), ('date', '<=', self.date_to),
            ('account_id.internal_group', 'in', ['income', 'expense']),
        ], ['account_id'], ['balance:sum'])
        return {account: balance for account, balance in groups}

    @api.depends('fiscal_year_id')
    def _compute_result(self):
        for wizard in self:
            balances = wizard._result_by_account() if wizard.fiscal_year_id else {}
            income = -sum(b for a, b in balances.items() if a.internal_group == 'income')
            expense = sum(b for a, b in balances.items() if a.internal_group == 'expense')
            wizard.income, wizard.expense = income, expense
            wizard.result = income - expense

    @api.depends('company_id')
    def _compute_earnings_account(self):
        for wizard in self:
            wizard.earnings_account_id = wizard.company_id \
                and wizard.company_id.get_unaffected_earnings_account()

    def action_open_check(self):
        """Open button of a check (``check`` in the context)."""
        self.ensure_one()
        model, domain = self._check_domains()[self.env.context['check']]
        return {'type': 'ir.actions.act_window', 'res_model': model,
                'name': self.env[model]._description,
                'views': [(False, 'list'), (False, 'form')],
                'domain': domain, 'target': 'current'}

    # ------------------------------------------------------------------
    def _closing_entry(self):
        """Current Year Earnings -> Retained Earnings for the result,
        dated the last day of the year."""
        self.ensure_one()
        result = self.currency_id.round(self.result)
        if self.currency_id.is_zero(result):
            return self.env['account.move']
        label = _("Year-end closing %s", self.fiscal_year_id.name)
        move = self.env['account.move'].with_company(self.company_id).create({
            'move_type': 'entry',
            'date': self.date_to,
            'journal_id': self.journal_id.id,
            'ref': label,
            'line_ids': [
                Command.create({'account_id': self.earnings_account_id.id, 'name': label,
                                'debit': max(result, 0.0), 'credit': max(-result, 0.0)}),
                Command.create({'account_id': self.retained_account_id.id, 'name': label,
                                'debit': max(-result, 0.0), 'credit': max(result, 0.0)}),
            ],
        })
        move.action_post()
        return move

    def action_close(self):
        self.ensure_one()
        year = self.fiscal_year_id
        year._check_chief()
        if self.has_blocking:
            raise UserError(_("Solve the blocking checks first (earlier fiscal "
                              "year still open, bank transactions to reconcile)."))
        if self.has_warnings and not self.close_anyway:
            raise UserError(_("Some checks are not passed. Solve them or tick "
                              "\"Close anyway\"."))
        move = self.env['account.move']
        if self.post_entry and not self.currency_id.is_zero(self.result):
            if not (self.retained_account_id and self.journal_id):
                raise UserError(_("Set the Retained Earnings account and the "
                                  "journal of the closing entry."))
            move = self._closing_entry()
            self.company_id.sudo().kit_retained_earnings_account_id = self.retained_account_id
        year._close(move)
        return {'type': 'ir.actions.act_window_close'}
