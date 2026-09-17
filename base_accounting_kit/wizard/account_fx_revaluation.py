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
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountFxRevaluation(models.TransientModel):
    """Wizard to revalue open foreign-currency balances at a closing rate and
    book the resulting unrealized gain/loss (with an optional reversal)."""
    _name = 'account.fx.revaluation'
    _description = 'Foreign Currency Revaluation'

    date = fields.Date(string='Revaluation Date', required=True,
                       default=fields.Date.context_today)
    account_ids = fields.Many2many(
        'account.account', string='Accounts',
        help="Accounts whose open foreign-currency lines are revalued.")
    journal_id = fields.Many2one('account.journal', string='Journal',
                                 required=True)
    gain_account_id = fields.Many2one('account.account',
                                      string='Unrealized Gain Account',
                                      required=True)
    loss_account_id = fields.Many2one('account.account',
                                      string='Unrealized Loss Account',
                                      required=True)
    auto_reverse = fields.Boolean(
        string='Reverse Automatically', default=True,
        help="Post a reversal entry the day after the revaluation date "
             "(unrealized amounts are reversed next period).")

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        company = self.env.company
        res.setdefault('journal_id', company.fx_reval_journal_id.id)
        res.setdefault('gain_account_id', company.fx_reval_gain_account_id.id)
        res.setdefault('loss_account_id', company.fx_reval_loss_account_id.id)
        if 'account_ids' in fields_list:
            accounts = self.env['account.account'].search([
                ('company_ids', 'in', company.id),
                ('account_type', 'in', ('asset_receivable', 'liability_payable',
                                        'asset_cash', 'liability_credit_card')),
            ])
            res['account_ids'] = [(6, 0, accounts.ids)]
        return res

    def _get_revaluation_lines(self):
        """Return the per-account unrealized adjustment (company currency)."""
        self.ensure_one()
        company = self.env.company
        comp_currency = company.currency_id
        result = {}
        for account in self.account_ids:
            move_lines = self.env['account.move.line'].search([
                ('account_id', '=', account.id),
                ('parent_state', '=', 'posted'),
                ('reconciled', '=', False),
                ('company_id', '=', company.id),
                ('currency_id', '!=', comp_currency.id),
                ('currency_id', '!=', False),
            ])
            adjustment = 0.0
            for line in move_lines:
                if not line.amount_residual_currency:
                    continue
                revalued = line.currency_id._convert(
                    line.amount_residual_currency, comp_currency, company,
                    self.date)
                adjustment += revalued - line.amount_residual
            if not comp_currency.is_zero(adjustment):
                result[account] = adjustment
        return result

    def action_revaluate(self):
        self.ensure_one()
        adjustments = self._get_revaluation_lines()
        if not adjustments:
            raise UserError(_(
                "No open foreign-currency balances to revalue on %s.")
                % self.date)
        line_cmds = []
        for account, adjustment in adjustments.items():
            if adjustment > 0:
                # Account balance increases on the debit side -> gain.
                line_cmds.append((0, 0, {
                    'name': _('FX revaluation'),
                    'account_id': account.id,
                    'debit': adjustment, 'credit': 0.0}))
                line_cmds.append((0, 0, {
                    'name': _('Unrealized FX gain'),
                    'account_id': self.gain_account_id.id,
                    'debit': 0.0, 'credit': adjustment}))
            else:
                line_cmds.append((0, 0, {
                    'name': _('FX revaluation'),
                    'account_id': account.id,
                    'debit': 0.0, 'credit': -adjustment}))
                line_cmds.append((0, 0, {
                    'name': _('Unrealized FX loss'),
                    'account_id': self.loss_account_id.id,
                    'debit': -adjustment, 'credit': 0.0}))
        move = self.env['account.move'].create({
            'journal_id': self.journal_id.id,
            'date': self.date,
            'ref': _('FX revaluation - %s') % self.date,
            'line_ids': line_cmds,
        })
        move.action_post()
        moves = move
        if self.auto_reverse:
            reversal = move._reverse_moves([{
                'date': self.date + relativedelta(days=1),
                'ref': _('Reversal of FX revaluation - %s') % self.date,
            }])
            reversal.action_post()
            moves |= reversal
        return {
            'name': _('FX Revaluation Entries'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', moves.ids)],
        }
