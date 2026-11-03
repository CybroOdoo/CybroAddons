# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class ProductImageSuggestion(models.TransientModel):
    # pylint: disable=no-wizard-in-models
    """Creates new model to store the searched image"""
    _name = "product.image.suggestion"
    _description = (
        "Attach images and set image as the display image of product"
    )

    image = fields.Binary(
        attachment=True,
        help="Image field to store the image",
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Related Product',
        help="Product field to store the id of product from which the image "
             "is searched",
    )

    def action_set_image(self):
        """Set product images from suggested images"""
        for rec in self:
            self_image = rec.image
            if self_image:
                rec.product_tmpl_id.image_1920 = self_image
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
