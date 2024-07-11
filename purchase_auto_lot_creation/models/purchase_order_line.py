# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ranjith R(odoo@cybrosys.com)
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


class PurchaseOrderLine(models.Model):
    """
    Inherits Purchase Order Line to add extra fields and functionalities related
    to the creation of the automatic stock lot creation.
    """
    _inherit = "purchase.order.line"

    lot_ids = fields.One2many(
        'custom.stock.lot', 'line_id', string="Lot",
        domain="[('id', '=', 0)]",
        help="Lot name to create for this order line")

    def _create_stock_moves(self, picking):
        """This is the method _create_stock_moves which is the method to create
        the stock.move when the purchase order is confirmed, here we super this
        method and we will create record in the stock.move.line corresponding to
        this stock.move for creating the lots"""
        res = super(PurchaseOrderLine, self)._create_stock_moves(picking)
        for items in self.lot_ids:
            self.env['stock.move.line'].create({
                'company_id': self.env.company.id,
                'picking_id': res.picking_id.id,
                'product_id': self.product_id.id,
                'location_id': res.location_id.id,
                'location_dest_id': res.location_dest_id.id,
                'lot_name': items.name,
                'quantity': self.product_uom_qty,
                'description_picking': self.product_id.display_name,
                'move_id': res.id
            })
        return res
