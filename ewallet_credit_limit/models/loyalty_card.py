# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies M  (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (AGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,

#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (AGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (AGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
############################################################################.
import re
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class LoyaltyCard(models.Model):
    _inherit = 'loyalty.card'

    set_limit = fields.Boolean(string='Set Limit' )
    limit = fields.Float(string='Spend only', store=True)
    balance_limit_amount = fields.Float(string='Balance limit Amount' , compute='_compute_balance_limit' , store=True)


    @api.depends('limit','set_limit')
    def _compute_balance_limit(self):
        for rec in self:
            rec.balance_limit_amount = rec.limit


    @api.onchange('points_display', 'limit')
    def check_balance_points(self):
        def clean_to_float(value):
            if isinstance(value, str):
                cleaned = re.sub(r'[^\d.]', '', value)
                return float(cleaned) if cleaned else 0.00
            return float(value)
        points_display_val = clean_to_float(self.points_display)
        limit_val = clean_to_float(self.limit)
        if points_display_val < limit_val:
            raise ValidationError(_("Your balance is less than your allowed limit. Please reset the limit"))