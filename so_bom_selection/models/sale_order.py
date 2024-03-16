# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Jumana Haseen (odoo@cybrosys.com)
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
################################################################################
from odoo import models


class SaleOrder(models.Model):
    """Inherited model 'sale.order'"""
    _inherit = 'sale.order'

    def action_confirm(self):
        """ Create manufacturing order of components in selected BOM """
        for rec in self.order_line:
            if rec.bom_id:
                mo = self.env["mrp.production"].create(
                    {
                        "product_id": rec.product_id.id,
                        "product_uom_id": rec.product_id.uom_id.id,
                        "origin": self.name,
                        'company_id': self.env.user.company_id.id,
                        "product_qty": rec.product_uom_qty,
                        "qty_to_produce": rec.product_uom_qty,
                        "bom_id": rec.bom_id.id,
                        "sale_line_id": rec.id,
                    }
                )
                moves_raw_values = mo._get_moves_raw_values()
                list_move_raw = []
                for move_raw_values in moves_raw_values:
                    list_move_raw += [(0, 0, move_raw_values)]
        return super(SaleOrder, self).action_confirm()

    def write(self, values):
        """Super write method to change the manufacturing quantity
        based on sale order quantity"""
        res = super(SaleOrder, self).write(values)
        for order_line in self.order_line:
            if order_line.product_uom_qty:
                mo = self.env["mrp.production"].search(
                    [('sale_line_id', '=', order_line.id),
                     ('state', '=', 'draft')])
                if mo:
                    mo.write({'product_qty': order_line.product_uom_qty})
                    mo.write({'qty_to_produce': order_line.product_uom_qty})
        return res
