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

from odoo import models, api


class PosOrder(models.Model):
    """Set remaining balance from POS order to the Loyalty"""
    _inherit = 'pos.order'

    @api.model
    def set_remaining_balance(self, data):
        """
        Update coupon balance based on points used in the order
        :param data: List of dictionaries containing order line data
        """
        for line_data in data:
            if line_data.get('coupon_id'):
                coupon = self.env['loyalty.card'].search([('id', '=', line_data.get('coupon_id'))])
                if coupon:
                    coupon.balance_limit_amount -= line_data.get('point_cost')
        return True