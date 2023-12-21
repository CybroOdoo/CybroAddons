# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: MOHAMMED DILSHAD TK (odoo@cybrosys.com)
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
################################################################################
from odoo import api, fields, models


class ProductProduct(models.Model):
    """ Multiple images in product form """
    _inherit = 'product.product'

    image_ids = fields.One2many('multi.image',
                                'product_id', string="Images",
                                help="Add Multiple Images to view in pos")
    is_img_added = fields.Boolean(string="Is image added",
                                  help="Does the images added")

    @api.onchange('image_ids')
    def _onchange_image_ids(self):
        """Set is_img_added to true while multiple images are added"""
        if self.image_ids:
            self.is_img_added = True
