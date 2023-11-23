# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Thasni CP (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models


class ProductProduct(models.Model):
    """If we check the display 360 image it will
    show a page to add images  in product .template """
    _inherit = 'product.product'

    product_image_view_ids = fields.One2many('product.image.view',
                                             'product_image_id',
                                             string="Image lines",
                                             help="To add different dimensions "
                                                  "of the product")
    is_boolean = fields.Boolean(string='Display 360° Image',
                                help='After enabling this field we can see a'
                                     ' tab for adding images for the product')
    is_stop = fields.Boolean(string='STOP',
                             help='To set the views to stop')


class ProductImageView(models.Model):
    """To add multiple images in product form, so
    this images can be seen in the form 360 degree view,
    orderline in product.product"""
    _name = 'product.image.view'
    _description = 'Product Image View'

    image_130 = fields.Image(string="Image", attachment=True, required=True,
                             help="To add images of the product")
    name = fields.Char(string='Label', required=True,
                       help='To identify the order of the images')
    product_image_id = fields.Many2one('product.product',
                                       string="Image view",
                                       help='To get the relation of '
                                            'product template')
