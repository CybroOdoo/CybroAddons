# -*- coding: utf-8 -*-
##############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Dhanya Babu (odoo@cybrosys.com)
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
##############################################################################
from odoo.exceptions import ValidationError
from odoo import fields, models


class WalletAmount(models.TransientModel):
    """We can add amount into the wallet."""
    _name = 'wallet.amount'
    _description = 'Wallet Amount'

    partner_id = fields.Many2one('res.partner', string='Partner',
                                 required=True,
                                 default=lambda
                                     self: self.env.user.partner_id.id,
                                 help="Partner details")
    amount = fields.Float(string='Wallet Amount', help='Amount to be added')

    def apply_wallet_amount(self):
        current_points = self.env['loyalty.card'].search(
            [('partner_id', '=', self.partner_id.id)]).points
        if current_points:
            self.env['loyalty.card'].search(
                [('partner_id', '=', self.partner_id.id)]).update(
                {'points': f'{current_points + self.amount}'})
        else:
            raise ValidationError("This person hasn't any E-wallet.")
