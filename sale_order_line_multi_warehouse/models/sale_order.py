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
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    """Extension of 'sale.order.line' to allow setting a specific warehouse
    per order line, generating separate stock pickings per warehouse.
    """

    _inherit = 'sale.order.line'

    product_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Line Warehouse',
        help='Warehouse where product is taken from',
        check_company=True,
    )

    @api.depends('product_warehouse_id')
    def _compute_warehouse_id(self):
        """Override to update line warehouse when a specific warehouse
        is configured on the sale order line.
        """
        res = super()._compute_warehouse_id()
        for line in self:
            if line.product_warehouse_id:
                line.warehouse_id = line.product_warehouse_id
        return res

    def _prepare_procurement_values(self):
        """Prepare procurement values setting warehouse_id from the line
        when a custom line warehouse is specified.
        """
        values = super()._prepare_procurement_values()
        if self.product_warehouse_id:
            values['warehouse_id'] = self.product_warehouse_id
        return values
