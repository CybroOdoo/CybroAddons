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


class ProductPricelist(models.Model):
    """ Inherits from 'product.pricelist' to add a boolean field for displaying
    pricelist prices on the product form's Prices tab. """
    _inherit = 'product.pricelist'

    display_pricelist = fields.Boolean(
        string='Display Pricelist Price on Products',
        default=False,
        help='If checked, this pricelist will be displayed on the '
             'product form\'s Prices tab.',
    )
