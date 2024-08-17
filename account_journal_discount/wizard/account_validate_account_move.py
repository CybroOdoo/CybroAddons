# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Afra MP (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models, _
from odoo.exceptions import UserError
from odoo.tools import float_round


class ValidateAccountMove(models.TransientModel):
    _inherit = "validate.account.move"

    def validate_move(self):
        if self._context.get('active_model') == 'account.move':
            domain = [('id', 'in', self._context.get('active_ids', [])), ('state', '=', 'draft')]
            moves = self.env['account.move'].search(domain).filtered('line_ids')
            if not moves:
                raise UserError(_('There are no journal items in the draft state to post.'))
            for move in moves:
                if move.move_type == 'out_invoice':
                    for line in move.invoice_line_ids:
                        if line.discount > 0 and line.product_id.categ_id.customer_account_discount_id:
                            lines_vals_list = []
                            debit_credit_value = abs(
                                float_round((line.price_subtotal - line.price_unit),
                                            precision_digits=
                                            move.currency_id.decimal_places))
                            lines_vals_list.append({
                                'name': line.name,
                                'move_id': move.id,
                                'currency_id': move.currency_id.id,
                                'account_id': line.product_id.categ_id.customer_account_discount_id.id,
                                'journal_id': move.journal_id.id,
                                'credit': 0,
                                'debit': debit_credit_value,
                            })
                            lines_vals_list.append({
                                'move_id': move.id,
                                'currency_id': move.currency_id.id,
                                'name': line.name,
                                'account_id': line.account_id.id,
                                'journal_id': move.journal_id.id,
                                'credit': debit_credit_value,
                                'debit': 0,
                            })
                            move.env['account.move.line'].create(lines_vals_list)
                elif move.move_type == 'in_invoice':
                    for line in move.invoice_line_ids:
                        if line.discount > 0 and \
                                line.product_id.categ_id.vendor_account_discount_id:
                            debit_credit_value = abs(
                                float_round((line.price_subtotal - line.price_unit),
                                            precision_digits=
                                            move.currency_id.decimal_places))
                            move.env['account.move.line'].with_context(
                                check_move_validity=False).create({
                                    'move_id': move.id,
                                    'name': line.name,
                                    'account_id': line.product_id.categ_id.vendor_account_discount_id.id,
                                    'journal_id': move.journal_id.id,
                                    'currency_id': move.currency_id.id,
                                    'credit': 0,
                                    'debit': debit_credit_value,
                                })
                            move.env['account.move.line'].with_context(
                                check_move_validity=False).create({
                                    'move_id': move.id,
                                    'name': line.name,
                                    'account_id': line.account_id.id,
                                    'journal_id': move.journal_id.id,
                                    'currency_id': move.currency_id.id,
                                    'credit': debit_credit_value,
                                    'debit': 0,
                                })
        return super(ValidateAccountMove,self).validate_move()
