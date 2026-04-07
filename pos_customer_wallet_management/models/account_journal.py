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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models

class AccountJournal(models.Model):
    """Adding fields to account journal"""
    _inherit = 'account.journal'


    is_wallet_journal = fields.Boolean(string="Wallet Journal",
                                    help="Journal for wallet")

    def write(self, vals):
        """Override write to avoid restricted field update errors if values are unchanged."""
        for record in self:
            filtered_vals = vals.copy()
            for field, value in vals.items():
                if field in record._fields:
                    field_obj = record._fields[field]
                    current_value = record[field]
                    if field_obj.type == 'many2one':
                        if current_value.id == value:
                            filtered_vals.pop(field)
                    elif current_value == value:
                        filtered_vals.pop(field)
            if filtered_vals:
                super(AccountJournal, record).write(filtered_vals)
        return True
