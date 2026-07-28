# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (Contact : odoo@cybrosys.com)
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
###############################################################################
from odoo import fields, models
from odoo.tools import float_compare


class SaleOrderLine(models.Model):
    """
        Extension of 'sale.order.line' with an additional
        field 'product_warehouse_id'.
        """
    _inherit = 'sale.order.line'

    product_warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse', help='Warehouse where product taken from')

    def _action_launch_stock_rule(self, previous_product_uom_qty=False):
        """
             Overwriting the function for adding functionalities of multiple
             warehouses in the sale order line.
             param previous_product_uom_qty(str): Uom quantity of previous
             product
             boolean: Returns True, if the picking created.
            """
        if self._context.get("skip_procurement"):
            return True
        precision = self.env['decimal.precision'].precision_get(
            'Product Unit of Measure')
        procurements = []
        for line in self:
            line = line.with_company(line.company_id)
            if line.state != 'sale' or not line.product_id.type in (
                    'consu', 'product'):
                continue
            qty = line._get_qty_procurement(previous_product_uom_qty)
            if float_compare(qty, line.product_uom_qty,
                             precision_digits=precision) == 0:
                continue
            group_id = line.order_id.stock_reference_ids
            if not group_id:
                group_id = self.env['stock.reference'].create(
                    line._prepare_reference_vals())
                line.order_id.stock_reference_ids = group_id
            else:
                updated_vals = {}
                if updated_vals:
                    group_id.write(updated_vals)
            values = line._prepare_procurement_values()
            if line.product_warehouse_id:
                values['warehouse_id'] = line.product_warehouse_id
            product_qty = line.product_uom_qty - qty
            line_uom = line.product_uom_id
            quant_uom = line.product_id.uom_id
            product_qty, procurement_uom = line_uom._adjust_uom_quantities(
                product_qty, quant_uom)
            procurements.append(self.env['stock.rule'].Procurement(
                line.product_id, product_qty, procurement_uom,
                line.order_id.partner_shipping_id.property_stock_customer,
                line.product_id.display_name, line.order_id.name,
                line.order_id.company_id, values))

        # procurements.append(procurements)
        if procurements:
            self.env['stock.rule'].run(procurements)
        orders = self.mapped('order_id')
        for order in orders:
            pickings_to_confirm = order.picking_ids.filtered(
                lambda p: p.state not in ['cancel', 'done'])
            if pickings_to_confirm:
                pickings_to_confirm.action_confirm()
        return True
