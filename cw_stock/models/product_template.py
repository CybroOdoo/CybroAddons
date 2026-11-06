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


class ProductTemplate(models.Model):
    """Inherits the Product template model for adding new fields
    and functions"""
    _inherit = 'product.template'

    apply_cw = fields.Boolean(string="Apply CW",
                              help="Whether to apply catch weight")
    cw_uom_id = fields.Many2one(
        'uom.uom', string='CW-Uom',
        help="Catch weight unit of measure")
    catch_weigth_ok = fields.Boolean(
        default=False, string="Catch Weight Product",
        help="Whether this is a catch weight product")
    average_cw_qty = fields.Float(string='Catch Weight', digits=(16, 4),
                                  help="Catch weight quantity")

    @api.onchange('cw_uom_id', 'uom_id')
    def _onchange_cw_uom_id(self):
        """Calculate the average CW quantity when the UoM and CW UoM match"""
        if self.uom_id == self.cw_uom_id:
            self.average_cw_qty = self.cw_uom_id.factor / self.uom_id.factor
        else:
            self.average_cw_qty = 1.00
