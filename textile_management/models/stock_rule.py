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
from odoo import models


class StockRule(models.Model):
    """Flag the manufacturing orders of textile sale orders as textile."""
    _inherit = 'stock.rule'

    def _prepare_mo_vals(self, product_id, product_qty, product_uom,  # pylint: disable=too-many-arguments
                         location_dest_id, name, origin, company_id, values,
                         bom):
        """Flag the manufacturing order as textile when it is created for a
        textile sale order (Replenish on Order)."""
        res = super()._prepare_mo_vals(
            product_id, product_qty, product_uom, location_dest_id, name,
            origin, company_id, values, bom)
        sale_orders = values.get(
            'reference_ids', self.env['stock.reference']).sale_ids
        if values.get('sale_line_id'):
            sale_orders |= self.env['sale.order.line'].browse(
                values['sale_line_id']).order_id
        if any(sale_orders.mapped('is_textile_sale_order')):
            res['is_textile_mrp_order'] = True
        return res
