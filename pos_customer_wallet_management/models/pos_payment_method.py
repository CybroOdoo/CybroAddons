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
from odoo import fields, models, api


class PosPaymentMethod(models.Model):
    """Adding fields to pos payment method"""
    _inherit = "pos.payment.method"

    wallet_journal = fields.Boolean(related="journal_id.wallet_journal",
                                    string="Wallet Journal",
                                    help="Journal for wallet")

    @api.model
    def _load_pos_data_fields(self, config_id):
        """The list of field to be loaded for POS data."""
        fields = super()._load_pos_data_fields(config_id)
        fields += ['wallet_journal']
        return fields
