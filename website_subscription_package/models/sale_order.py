# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Sabeel B (odoo@cybrosys.com)
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
from odoo import models


class SaleOrder(models.Model):
    """Extends the Sale Order model to handle subscription orders."""
    _inherit = 'sale.order'

    def _cart_update(self, product_id=None, line_id=None, add_qty=0,
                     set_qty=0, **kwargs):
        """Supering the _cart_update function to write the interval_id"""
        res = super()._cart_update(product_id=product_id, line_id=line_id,
                                   add_qty=add_qty, set_qty=set_qty, **kwargs)
        order_line = self.env['sale.order.line'].sudo().browse(res['line_id'])
        if kwargs.get('period'):
            order_line.write({
                'subscription_interval_id': int(kwargs.get('period')),
            })
        return res
