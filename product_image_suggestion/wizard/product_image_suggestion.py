# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: RAHUL CK (odoo@cybrosys.com)
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
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class ProductImageSuggestion(models.TransientModel):
    """Creates new model to store the searched image"""
    _name = "product.image.suggestion"
    _description = "Attach images and set image as the display image of product"

    image = fields.Binary(string='Image', attachment=True,
                          help="Image field to store the image")
    product_tmpl_id = fields.Many2one('product.template',
                                      string='Related Product',
                                      help="""Product field to store the id
                                      of product from which the image is
                                      searched""")

    def action_set_image(self):
        """Set product images from suggested images"""
        self.product_tmpl_id.image_1920 = self.image
