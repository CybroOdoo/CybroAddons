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


class ImageView(models.Model):
    """Stores the images of a product template, so that they can be shown
    in the 360 degree view."""
    _name = 'image.view'
    _description = 'Image View'

    image_130 = fields.Image(string="Image", attachment=True, required=True,
                             help="To add images of the product")
    name = fields.Char(string='Label', required=True,
                       help='To identify the order of the images')
    image_id = fields.Many2one('product.template',
                               string="Image view",
                               help='Product template these images belong to')
