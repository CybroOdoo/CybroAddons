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
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#############################################################################
from odoo import api, fields, models


class CustomStockLot(models.Model):
    """
    Creates the model Custom Stock Lot, which contains the name of the lot
    to be created.
    """
    _name = 'custom.stock.lot'
    _description = 'Custom Stock Lot'

    name = fields.Char(
        string="Name", required=True,
        help="Name of the lot to purchase")
    line_id = fields.Many2one(
        'purchase.order.line', string="Order Line",
        domain="[('is_lot_product', '=', True)]",
        help="Purchase order line associated with this lot")

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record in records:
            if record.line_id and record.line_id.lot_id != record:
                record.line_id.lot_id = record.id
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'line_id' in vals:
            for record in self:
                if record.line_id and record.line_id.lot_id != record:
                    record.line_id.lot_id = record.id
        return res
