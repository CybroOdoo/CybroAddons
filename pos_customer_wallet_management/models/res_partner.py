# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
from odoo import api, fields, models


class ResPartner(models.Model):
    """Add wallet fields to res.partner"""
    _inherit = 'res.partner'


    wallet_balance = fields.Float(help="Wallet balance of the customer")
    wallet_count = fields.Integer(string="Wallet",
                                  compute='_compute_wallet_count',
                                  help="Number of wallet transactions of the customer")

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields = super()._load_pos_data_fields(config_id)
        fields.append('wallet_balance')
        return fields

    def action_recharge(self):
        """Open the wizard used to recharge the customer's wallet."""
        return {
            'name': 'Wallet Recharge',
            'type': 'ir.actions.act_window',
            'res_model': 'recharge.wallet',
            'view_mode': 'form',
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
        """Compute the number of wallet transactions of each partner."""
        for record in self:
            record.wallet_count = self.env['wallet.transaction'].search_count(
                [('customer', '=', self.name)])

    @api.model
    def write_value(self, wallet_balance, partner_id, session, price, currency_id, order_ref=False):
        """Update wallet balance from POS with robust handling and sudo permissions."""
        partner = self.env['res.partner'].sudo().browse(partner_id)
        if not partner.exists():
            return False

        pos_order_ref = str(order_ref or "")

        # Prevent duplicate: if a Debit already exists for this partner + exact order ref, skip
        if pos_order_ref:
            existing_transaction = self.env['wallet.transaction'].sudo().search([
                ('customer', '=', partner.name),
                ('pos_order', '=', pos_order_ref),
                ('type', '=', 'Debit')
            ], limit=1)
            if existing_transaction:
                return partner.wallet_balance

        # Persist balance change
        partner.write({'wallet_balance': wallet_balance})

        current_session = self.env['pos.session'].sudo().search([('state', '=', 'opened')], limit=1)
        session_name = current_session.name if current_session else f"Session-{session}"

        self.env['wallet.transaction'].sudo().create({
            'type': "Debit",
            'customer': partner.name,
            'amount': price,
            'pos_order': pos_order_ref or session_name,
            'currency': currency_id,
        })

        # Mark the corresponding POS order as wallet-deducted so the backend hook skips it
        if pos_order_ref:
            pos_order = self.env['pos.order'].sudo().search([
                '|',
                ('name', '=', pos_order_ref),
                ('uuid', '=', pos_order_ref),
            ], limit=1)
            if pos_order and not pos_order.is_wallet_deducted:
                pos_order.is_wallet_deducted = True

        return partner.wallet_balance
