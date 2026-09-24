# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
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
###############################################################################

from odoo import api, models


class PosOrder(models.Model):
    """Inherit POS Order to handle e-wallet credit limit deduction."""
    _inherit = 'pos.order'

    @api.model
    def set_remaining_balance(self, data):
        """
        Update coupon balance based on points used in the order.
        :param data: List of dictionaries containing order line data
        """
        for line_data in data:
            if line_data.get('coupon_id'):
                coupon = self.env['loyalty.card'].search([('id', '=', line_data.get('coupon_id'))])
                if coupon:
                    coupon.used_limit += line_data.get('point_cost', 0.0)
        return True
