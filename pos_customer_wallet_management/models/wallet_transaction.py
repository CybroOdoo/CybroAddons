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


class WalletTransaction(models.Model):
    """Wallet transaction records"""
    _name = 'wallet.transaction'
    _description = "Wallet Transaction"


    name = fields.Char(help="Sequence number of the wallet transaction")
    type = fields.Char(help="Type of the wallet transaction")
    customer = fields.Char(help="Customer of the wallet transaction")
    pos_order = fields.Char(string="POS Order",
                            help="Order reference of the wallet transaction")
    amount = fields.Float(help="Amount of the wallet transaction")
    currency = fields.Char(help="Currency of the wallet transaction")

    @api.model
    def create(self, vals_list):
        """Create sequence for wallet transaction"""
        for vals in vals_list:
            vals['name'] = self.env['ir.sequence'].next_by_code('wallet.transaction')
        return super(WalletTransaction, self).create(vals_list)
