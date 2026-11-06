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


class DiscountBasedSalesCommission(models.Model):
    """Creating a discount based sales commission model."""
    _name = "discount.based.sales.commission"
    _description = "Discount Based Sales Commission"

    sale_commission_id = fields.Many2one(
        "sales.commission",
        string='Sales Commission',
        help="Related sales commission configuration.",
    )
    discount = fields.Float(
        string='Discount %',
        help="Minimum discount percentage required to trigger this rule.",
    )
    commission = fields.Float(
        string='Commission %',
        help="Commission percentage awarded when the discount threshold is met.",
    )

    @api.constrains('discount', 'commission')
    def _check_percentages(self):
        """Validate discount and commission values are between 0 and 100."""
        for rec in self:
            if rec.discount < 0.0 or rec.discount > 100.0:
                raise ValidationError(
                    _("Discount percentage must be between 0 and 100.")
                )
            if rec.commission < 0.0 or rec.commission > 100.0:
                raise ValidationError(
                    _("Commission percentage must be between 0 and 100.")
                )
