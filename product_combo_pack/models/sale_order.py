# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Gayathri v (odoo@cybrosys.com)
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
from odoo import api, fields, models
from odoo.fields import Command


class SaleOrder(models.Model):
    """Model for extending the sale order to include a selection of packs."""
    _inherit = 'sale.order'

    product_pack_ids = fields.Many2many(
        'product.product',
        'sale_order_product_pack_rel',
        string='Select Pack',
        domain=[('is_pack', '=', True)],
        help='The selected pack product for the sale order.'
    )

    @api.onchange('product_pack_ids')
    def onchange_product_pack_ids(self):
        """Perform actions when the selected pack product changes."""
        if self.product_pack_ids:
            new_order_lines = []
            for rec in self.product_pack_ids:
                product_already_added = any(
                    line.product_id.id == rec._origin.id for line in
                    self.order_line)
                if not product_already_added:
                    new_order_lines.append((0, 0, {
                        'product_id': rec.id,
                        'name': rec.name,
                        'product_uom_qty': 1,
                        'price_unit': rec.pack_price,
                    }))
                    self.order_line = new_order_lines
        elif not self.product_pack_ids:
            self.order_line = [(5, 0, 0)]

    def action_confirm(self):
        """Override the action_confirm method to create stock moves
        for pack products."""
        super().action_confirm()
        for line in self.order_line:
            if line.product_id.is_pack:
                for record in line.product_id.pack_products_ids:
                    for rec in self.picking_ids:
                        move = rec.move_ids.create({
                            'name': record.product_id.name,
                            'product_id': record.product_id.id,
                            'product_uom_qty': record.quantity * line.product_uom_qty,
                            'product_uom': record.product_id.uom_id.id,
                            'picking_id': rec.id,
                            'location_id': rec.location_id.id,
                            'location_dest_id': rec.location_dest_id.id,
                        })
                        move._action_confirm()


class SaleOrderLine(models.Model):
    """Inherit the model sale.order.line to add extra functionality and
    fields"""
    _inherit = 'sale.order.line'

    def _prepare_invoice_line(self, **optional_values):
        """Prepare the values to create the new invoice line for a sales order line.

        :param optional_values: any parameter that should be added to the returned invoice line
        :rtype: dict
        """
        self.ensure_one()
        res = {
            'display_type': self.display_type or 'product',
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'discount': self.discount,
            'price_unit': 0 if self.product_id.is_pack == True else self.price_unit,
            'tax_ids': [Command.set(self.tax_id.ids)],
            'sale_line_ids': [Command.link(self.id)],
            'is_downpayment': self.is_downpayment,
        }
        analytic_account_id = self.order_id.analytic_account_id.id
        if self.analytic_distribution and not self.display_type:
            res['analytic_distribution'] = self.analytic_distribution
        if analytic_account_id and not self.display_type:
            analytic_account_id = str(analytic_account_id)
            if 'analytic_distribution' in res:
                res['analytic_distribution'][analytic_account_id] = res[
                                                                        'analytic_distribution'].get(
                    analytic_account_id, 0) + 100
            else:
                res['analytic_distribution'] = {analytic_account_id: 100}
        if optional_values:
            res.update(optional_values)
        if self.display_type:
            res['account_id'] = False
        return res
