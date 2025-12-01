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
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    """Add field into res partner"""
    _inherit = 'res.partner'

    wallet_balance = fields.Float(string="Wallet Balance",
                                  help="Wallet balance of each employee")
    wallet_count = fields.Integer(string="Wallet",
                                  compute='_compute_wallet_count',
                                  help="Count of each wallet recharge")

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields = super()._load_pos_data_fields(config_id)
        fields.append('wallet_balance')
        return fields

    def action_recharge(self):
        """Open wizard for wallet recharge and user
        can use this wizard to recharge the wallet balance."""
        return {
            'name': 'Wallet Recharge',
            'type': 'ir.actions.act_window',
            'res_model': 'recharge.wallet',
            'view_mode': 'form',
            'view_type': 'form',
            'target': 'new',
        }

    def action_number_of_wallet(self):
        """Wallet balance tree view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Wallet',
            'view_mode': 'list',
            'res_model': 'wallet.transaction',
            'domain': [('customer', '=', self.name)],
            'context': "{'create': False}"
        }

    def _compute_wallet_count(self):
        """This computed method calculates the number of wallet
        transactions associated with each partner and updates the `wallet_count` field accordingly."""
        for record in self:
            record.wallet_count = self.env['wallet.transaction'].search_count(
                [('customer', '=', self.name)])

    @api.model
    def write_value(self, wallet_balance, partner_id, session, price, currency_id):
        partner = self.env['res.partner'].browse(partner_id)
        if not partner.exists():
            raise ValidationError("Partner not found")

        existing_transaction = self.env['wallet.transaction'].search([
            ('customer', '=', partner.name),
            ('amount', '=', price),
            ('pos_order', '=', str(session)),
            ('type', '=', 'Debit')
        ], limit=1)

        if existing_transaction:
            return
        partner.wallet_balance = wallet_balance
        current_session = self.env['pos.session'].search([('state', '=', 'opened')], limit=1)
        session_name = current_session.name if current_session else f"Session-{session}"

        self.env['wallet.transaction'].create({
            'type': "Debit",
            'customer': partner.name,
            'amount': price,
            'pos_order': session_name,
            'currency': currency_id,
        })
