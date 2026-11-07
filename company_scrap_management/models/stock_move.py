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


class StockMove(models.Model):
    """ Inherit the model stock.move for scrap management fields. """
    _inherit = "stock.move"

    bill_of_material_id = fields.Many2one(
        'mrp.bom',
        domain="[('product_tmpl_id', '=', product_tmpl_id)]",
        string="Bill of Material",
        help="Field to specify sequence bill of material")
    typ_of_reuse = fields.Selection(
        [('none', 'None'), ('dismantle', 'Dismantle')],
        default="none", help="Field to specify type of scrap",
        string="Type of Operation")
    state_management = fields.Selection(
        [('none', 'None'), ('dismantled', 'Dismantled')],
        string="State", default="none",
        help="Field to specify type of scrap management")
    scrap_qty = fields.Float(
        string="Scrap Quantity", related='quantity',
        help="Quantity scrapped")
    scrap_location_id = fields.Many2one(
        'stock.location', string="Scrap Location",
        related='location_dest_id',
        help="Location where the scrap product is moved to")

    @api.depends('is_scrap', 'reference')
    def _compute_display_name(self):
        super()._compute_display_name()
        for move in self:
            if move.is_scrap and move.reference:
                move.display_name = move.reference

    def do_scrap(self):
        """Perform scrap for scrap move."""
        return self.action_scrap()
