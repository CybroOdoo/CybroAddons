# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#############################################################################
from odoo import models, fields


class SaleOrderLine(models.Model):
    """Inheriting sale order line for adding some fields"""
    _inherit = 'sale.order.line'

    order_line_image = fields.Binary(string="Image",
                                     related="product_id.image_1920",
                                     help='Corresponding image of product')
    contact_email = fields.Char(related="order_partner_id.email",
                                string='Email',
                                help='Email of the customer')
    contact_phone = fields.Char(related="order_partner_id.phone",
                                string='Phone',
                                help='Phone number of the customer')
