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
from odoo import fields, models


class ProductAttributeCustomValue(models.Model):
    """
    Model for representing custom attribute values for a purchase order line.
    Inherits from 'product.attribute.custom.value' model.
    """
    _inherit = "product.attribute.custom.value"

    purchase_order_line_id = fields.Many2one(
        comodel_name='purchase.order.line',
        string="Purchase Order Line",
        required=False,
        ondelete='cascade',
        help="Purchase order lines.",
    )
