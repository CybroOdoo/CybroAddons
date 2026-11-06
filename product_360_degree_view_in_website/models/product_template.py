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


class ProductTemplate(models.Model):
    """Adds the 360° view images to the product template. When Display 360°
    Image is enabled, a tab is shown to add the images."""
    _inherit = 'product.template'

    image_view_ids = fields.One2many('image.view', 'image_id',
                                     string="Image lines",
                                     help="To add the different angle images "
                                          "of the product")
    is_boolean = fields.Boolean(string='Display 360° Image',
                                help='After enabling this field, a tab is '
                                     'shown for adding the images of the '
                                     'product')
