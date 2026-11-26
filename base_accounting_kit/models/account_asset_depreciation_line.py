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
from markupsafe import Markup

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AccountAssetDepreciationLine(models.Model):
    """Model for managing asset depreciation lines in the accounting system."""
    _name = 'account.asset.depreciation.line'
    _description = 'Asset depreciation line'

    name = fields.Char(string='Depreciation Name', required=True, index=True)
    sequence = fields.Integer(required=True)
    asset_id = fields.Many2one('account.asset.asset', string='Asset',
                               required=True, ondelete='cascade')
    parent_state = fields.Selection(related='asset_id.state',
                                    string='State of Asset')
    amount = fields.Float(string='Current Depreciation',
                          required=True)
    remaining_value = fields.Float(string='Next Period Depreciation',
                                   required=True)
    depreciated_value = fields.Float(string='Cumulative Depreciation',
                                     required=True)
    depreciation_date = fields.Date('Depreciation Date', index=True)
    move_id = fields.Many2one('account.move', string='Depreciation Entry')
    move_check = fields.Boolean(compute='_get_move_check', string='Linked',
                                store=True)
    move_posted_check = fields.Boolean(compute='_get_move_posted_check',
                                       string='Posted', store=True)

    @api.depends('move_id')
    def _get_move_check(self):
        """Compute the 'move_check' field based on the presence of 'move_id'
        for each record in the 'AccountAssetDepreciationLine' class."""
        for line in self:
            line.move_check = bool(line.move_id)

    @api.depends('move_id.state')
    def _get_move_posted_check(self):
        """Compute the 'move_posted_check' field based on the state of 'move_id'
        for each record in the 'AccountAssetDepreciationLine' class."""
        for line in self:
            line.move_posted_check = True if line.move_id and line.move_id.state == 'posted' else False

    @api.model
    def _analytic_distribution(self, record, side):
        """Analytic distribution of a depreciation move line.

        The analytic account of the asset (or category) goes on the expense
        line of an asset and on the revenue line of a deferred revenue.

        :param record: the asset or the asset category
        :param side: ``'purchase'`` for the expense line, ``'sale'`` for the
            revenue line
        """
        if record.account_analytic_id and record.type == side:
            return {str(record.account_analytic_id.id): 100}
        return False

    def create_move(self, post_move=True):
        """Create and post the entries of depreciation lines that are due."""
        created_moves = self.env['account.move']
        if self.mapped('move_id'):
            raise UserError(_(
                'This depreciation is already linked to a journal entry! Please post or delete it.'))
        for line in self:
            asset_id = line.asset_id
            depreciation_date = self.env.context.get(
                'depreciation_date') or line.depreciation_date or fields.Date.context_today(
                self)
            company_currency = asset_id.company_id.currency_id
            current_currency = asset_id.currency_id
            amount = current_currency._convert(line.amount, company_currency,
                                      line.asset_id.company_id,
                                      depreciation_date)
            asset_name = line.asset_id.name + ' (%s/%s)' % (line.sequence, len(line.asset_id.depreciation_line_ids))
            partner = self.env['res.partner']._find_accounting_partner(line.asset_id.partner_id)
            # As in core, the amount goes in ``balance``; ``currency_id`` and
            # ``amount_currency`` only for a foreign currency (with the
            # company currency, core sets ``balance`` from
            # ``amount_currency``, so passing 0 there zeroed the entry).
            foreign = company_currency != current_currency

            def _line(account, balance, amount_currency, side):
                vals = {
                    'name': asset_name,
                    'account_id': account.id,
                    'balance': balance,
                    'partner_id': partner.id,
                    'analytic_distribution': self._analytic_distribution(
                        asset_id, side),
                }
                if foreign:
                    vals.update(currency_id=current_currency.id,
                                amount_currency=amount_currency)
                return vals
            move_line_1 = _line(asset_id.account_depreciation_id, -amount,
                                -line.amount, 'sale')
            move_line_2 = _line(asset_id.account_depreciation_expense_id,
                                amount, line.amount, 'purchase')
            # Build a balanced two-line entry directly (no create-then-rewrite
            # and no "Automatic Balancing Line" removal — that hack is a no-op
            # for a tax-less JE in v19 and breaks under translation).
            move = self.env['account.move'].create({
                'ref': line.asset_id.code,
                'date': depreciation_date or False,
                'journal_id': asset_id.journal_id.id,
                'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
            })
            line.write({'move_id': move.id, 'move_check': True})
            created_moves |= move

        if post_move and created_moves:
            created_moves.action_post()
        return [x.id for x in created_moves]

    def create_grouped_move(self, post_move=True):
        """Create a grouped accounting move for asset depreciation lines."""
        if not self.exists():
            return []
        created_moves = self.env['account.move']
        category_id = self[
            0].asset_id.category_id  # we can suppose that all lines have the same category
        depreciation_date = self.env.context.get(
            'depreciation_date') or fields.Date.context_today(self)
        amount = 0.0
        for line in self:
            # Sum amount of all depreciation lines
            company_currency = line.asset_id.company_id.currency_id
            current_currency = line.asset_id.currency_id
            amount += current_currency._convert(
                line.amount, company_currency, line.asset_id.company_id,
                depreciation_date)

        name = category_id.name + _(' (grouped)')
        move_line_1 = {
            'name': name,
            'account_id': category_id.account_depreciation_id.id,
            'debit': 0.0,
            'credit': amount,
            'journal_id': category_id.journal_id.id,
            'analytic_distribution': self._analytic_distribution(
                category_id, 'sale'),
        }
        move_line_2 = {
            'name': name,
            'account_id': category_id.account_depreciation_expense_id.id,
            'credit': 0.0,
            'debit': amount,
            'journal_id': category_id.journal_id.id,
            'analytic_distribution': self._analytic_distribution(
                category_id, 'purchase'),
        }
        move_vals = {
            'ref': category_id.name,
            'date': depreciation_date or False,
            'journal_id': category_id.journal_id.id,
            'line_ids': [(0, 0, move_line_1), (0, 0, move_line_2)],
        }
        move = self.env['account.move'].create(move_vals)
        self.write({'move_id': move.id, 'move_check': True})
        created_moves |= move

        if post_move and created_moves:
            created_moves.action_post()
        return [x.id for x in created_moves]

    def post_lines_and_close_asset(self):
        # we re-evaluate the assets to determine whether we can close them
        # `message_post` invalidates the (whole) cache
        # preprocess the assets and lines in which a message should be posted,
        # and then post in batch will prevent the re-fetch of the same data over and over.
        assets_to_close = self.env['account.asset.asset']
        for line in self:
            asset = line.asset_id
            if asset.currency_id.is_zero(asset.value_residual):
                assets_to_close |= asset
        self.log_message_when_posted()
        assets_to_close.write({'state': 'close'})
        for asset in assets_to_close:
            asset.message_post(body=_("Document closed."))

    def log_message_when_posted(self):
        """Format and post messages for asset depreciation lines that are posted."""
        def _format_message(message_description, tracked_values):
            # Markup so the tags render in the chatter; the values are
            # escaped by the ``%`` operator (P1.15).
            message = Markup()
            if message_description:
                message = Markup('<span>%s</span>') % message_description
            for name, values in tracked_values.items():
                message += Markup('<div> &nbsp; &nbsp; &bull; <b>%s</b>: %s</div>') % (name, values)
            return message

        # `message_post` invalidates the (whole) cache
        # preprocess the assets in which messages should be posted,
        # and then post in batch will prevent the re-fetch of the same data over and over.
        assets_to_post = {}
        for line in self:
            if line.move_id:
                partner_name = line.asset_id.partner_id.name
                currency_name = line.asset_id.currency_id.name
                msg_values = {_('Currency'): currency_name,
                              _('Amount'): line.amount}
                if partner_name:
                    msg_values[_('Partner')] = partner_name
                msg = _format_message(_('Depreciation line posted.'),
                                      msg_values)
                assets_to_post.setdefault(line.asset_id, []).append(msg)
        for asset, messages in assets_to_post.items():
            for msg in messages:
                asset.message_post(body=msg)
