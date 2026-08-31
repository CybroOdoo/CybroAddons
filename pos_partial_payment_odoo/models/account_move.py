# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Athul Raj B S (odoo@cybrosys.info)
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
################################################################################
from odoo import models, fields


class AccountMove(models.Model):
    """
    Inherit account.move to track whether an invoice is linked to a partially
    paid POS order and pass context when registering payment.
    """
    _inherit = 'account.move'

    is_pos_order = fields.Boolean(
        string='Is POS Order',
        help='Indicates whether this account move is associated with a POS order.',
        compute='_compute_is_pos_order',
    )

    def _compute_is_pos_order(self):
        """
        Compute 'is_pos_order' field to determine if the account move is
        associated with an invoiced partially paid POS order.
        """
        for move in self:
            pos_order = self.env['pos.order'].search([
                ('account_move', '=', move.id),
                ('state', '=', 'invoiced'),
                ('is_partial_payment', '=', True)
            ], limit=1)
            move.is_pos_order = bool(pos_order)

    def action_register_payment(self):
        res = super(AccountMove, self).action_register_payment()
        if self.is_pos_order and isinstance(res, dict):
            res.setdefault('context', {}).update({
                'is_pos_order': True,
            })
        return res
