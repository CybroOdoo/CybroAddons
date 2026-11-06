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


class ProductBasedSalesCommission(models.Model):
    """Creating product based sales commission model."""
    _name = "product.based.sales.commission"
    _description = "Product Based Sales Commission"

    sale_commission_id = fields.Many2one(
        "sales.commission",
        string='Sale Commission',
        help="Related sales commission configuration.",
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        help="Product to which this commission applies.",
    )
    commission = fields.Float(
        string='Commission %',
        help="Commission percentage applied for this product.",
    )

    @api.constrains('commission')
    def _check_commission(self):
        """Ensure commission percentage is between 0 and 100."""
        for rec in self:
            if rec.commission < 0.0 or rec.commission > 100.0:
                raise ValidationError(
                    _("Product commission percentage must be between 0 and 100.")
                )
