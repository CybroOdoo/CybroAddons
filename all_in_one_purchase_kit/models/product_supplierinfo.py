# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author:  Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import api, fields, models


class ProductSupplierInfo(models.Model):
    """Inherit the model to add fields and methods"""
    _inherit = "product.supplierinfo"

    discount = fields.Float(string="Discount (%)", help="Discount in %")
    _maximum_discount = models.Constraint(
        "CHECK (discount <= 100.0)",
        "Discount must be lower than 100%.",
    )

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """Add default discount to order line"""
        for supplier in self.filtered("partner_id"):
            supplier.write({'discount': supplier.partner_id.default_discount})
