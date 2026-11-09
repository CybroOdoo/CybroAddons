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


class ProductPricelistItem(models.Model):
    """ Inherits the Product Price list Item Class to compute the product uom
    and want to apply in the price list. """
    _inherit = "product.pricelist.item"

    product_uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string="Unit of Measure",
        compute='_compute_product_uom_id',
        store=True, readonly=False, precompute=True, ondelete='restrict',
        help="Defines the product uom of the product")

    @api.depends('product_tmpl_id')
    def _compute_product_uom_id(self):
        """ Computes the product uom, and it depends on the product template """
        for line in self:
            if line.product_tmpl_id:
                if not line.product_uom_id:
                    line.product_uom_id = line.product_tmpl_id.uom_id
            else:
                line.product_uom_id = False

    def _is_applicable_for(self, product, quantity, *args, uom=None, **kwargs):
        """ Check whether the current rule is valid for the given product & qty.
        Supports both positional uom (legacy/tests) and keyword uom (Odoo 20).
        """
        if args and not uom:
            uom = args[0]
        res = super()._is_applicable_for(product, quantity, uom=uom, **kwargs)
        if not res:
            return False
        if self.product_uom_id:
            target_uom = uom or product.uom_id
            if target_uom != self.product_uom_id:
                return False
        return True
