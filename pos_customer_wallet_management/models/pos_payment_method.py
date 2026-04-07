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
from odoo import fields, models, api


class PosPaymentMethod(models.Model):
    """Adding fields to pos payment method"""
    _inherit = "pos.payment.method"


    is_wallet_journal = fields.Boolean(related="journal_id.is_wallet_journal",
                                    string="Wallet Journal",
                                    help="Journal for wallet")

    @api.model
    def _load_pos_data_fields(self, config_id):
        """The list of field to be loaded for POS data."""
        fields = super()._load_pos_data_fields(config_id)
        fields += ['is_wallet_journal']
        return fields

    def write(self, vals):
        """Override write to avoid UserError for open sessions if values are unchanged."""
        if not self.env.context.get('ignore_pos_session_check') and self.filtered('open_session_ids'):
            for record in self:
                if not record.open_session_ids:
                    super(PosPaymentMethod, record).write(vals)
                    continue

                # Filter out unchanged values to avoid triggering _is_write_forbidden
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
                    super(PosPaymentMethod, record).write(filtered_vals)
            return True
        return super().write(vals)
