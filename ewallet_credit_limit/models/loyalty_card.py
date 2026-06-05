# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2025-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Swaraj R (odoo@cybrosys.com)
#
#    This program is free software: you can modify
#    it under the terms of the GNU Affero General Public License (AGPL) as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
################################################################################

import re
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class LoyaltyCard(models.Model):
    """Setting limit for the Loyality"""
    _inherit = 'loyalty.card'

    set_limit = fields.Boolean(string='Set Limit')
    limit = fields.Float(string='Spend only', store=True)
    balance_limit_amount = fields.Float(string='Balance limit Amount' , compute='_compute_balance_limit' , store=True)

    @api.depends('limit','set_limit')
    def _compute_balance_limit(self):
        """Computing balance limit for Loyality"""
        for rec in self:
            rec.balance_limit_amount = rec.limit

    @api.onchange('points_display', 'limit')
    def check_balance_points(self):
        """Checking balance points"""
        def clean_to_float(value):
            if isinstance(value, str):
                cleaned = re.sub(r'[^\d.]', '', value)
                return float(cleaned) if cleaned else 0.00
            return float(value)
        points_display_val = clean_to_float(self.points_display)
        limit_val = clean_to_float(self.limit)
        if points_display_val < limit_val:
            raise ValidationError(_("Your balance is less than your allowed limit. Please reset the limit"))

    @api.model
    def _load_pos_data_fields(self, config_id):
        """loading fields to POS"""
        data = super()._load_pos_data_fields(config_id)
        data += ['balance_limit_amount', 'set_limit']
        return data
