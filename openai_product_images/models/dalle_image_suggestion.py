# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
################################################################################
from odoo import fields, models


class DalleImageSuggestion(models.Model):
    """image for product from dalle and save it as record"""
    _name = 'dalle.image.suggestion'
    _rec_name = 'product_tmpl_id'
    _description = 'model for save image'

    product_image = fields.Binary('Image', attachment=True,
                                  help="filed to store image")
    product_tmpl_id = fields.Many2one('product.template', 'Related Product',
                                      help="filed to store product")

    def action_make_as_product_image(self):
        """Summary:
              Function to make this image as product image
           Returns:
               returns the  product form view image of corresponding product
        """
        self.product_tmpl_id.image_1920 = self.product_image
        return {
            'name': self.product_tmpl_id.name,
            'view_mode': 'form',
            'res_model': 'product.template',
            'type': 'ir.actions.act_window',
            'res_id': self.product_tmpl_id.id,
            'domain': [('id', '=', self.product_tmpl_id.id)],
            'target': 'current',
        }
