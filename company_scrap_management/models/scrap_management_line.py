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
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ScrapManagementLine(models.Model):
    """ This class define a new model for manage scrap components """
    _name = "scrap.management.line"
    _description = "Scrap Management Line"

    product_id = fields.Many2one('product.product',
                                 string="Product", readonly=True,
                                 help="Field to specify product")
    scrap_management_id = fields.Many2one('scrap.management',
                                          string="Scrap Management Order", readonly=True,
                                          help="Field to specify "
                                               "scrap management order")
    dismantle_qty = fields.Float(string="Available quantity", readonly=True,
                                 help="Field to specify total quantity")
    useful_qty = fields.Float(string="Useful Product Quantity",
                              help="Field to specify useful quantity")

    @api.constrains('useful_qty', 'dismantle_qty')
    def _check_useful_qty(self):
        """Validate useful_qty does not exceed dismantle_qty and is non-negative."""
        for line in self:
            if line.useful_qty < 0:
                raise ValidationError(_("Useful quantity cannot be negative."))
            if line.useful_qty > line.dismantle_qty:
                raise ValidationError(
                    _("Useful quantity cannot exceed the available dismantle quantity.")
                )
