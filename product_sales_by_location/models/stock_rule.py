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
#    This program is distributed in the hope it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import models


class StockRule(models.Model):
    """Inherit stock rule to set stock move source location from sale order line."""
    _inherit = 'stock.rule'

    def _get_stock_move_values(self, product_id, product_qty, uom_id,
                               location_dest_id, name, origin, company_id, values):
        """Retrieve stock move values for a given product and apply line location."""
        res = super()._get_stock_move_values(
            product_id, product_qty, uom_id, location_dest_id, name, origin, company_id, values
        )
        if values.get('sale_line_id'):
            sale_line = self.env['sale.order.line'].sudo().browse(values['sale_line_id'])
            if sale_line.line_location_id:
                res['location_id'] = sale_line.line_location_id.id
        return res
