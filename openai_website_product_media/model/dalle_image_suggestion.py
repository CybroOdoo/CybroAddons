# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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
from odoo import models


class DalleImageSuggestion(models.Model):
    """image for product from dalle and save it as record"""
    _inherit = 'dalle.image.suggestion'

    def action_make_as_media_image(self):
        """Summary:
              Function to make this image as media image
           Returns:
               returns the created media image of corresponding product
        """
        dalle_media_image_suggestion_id = self.env['product.image'].create({
            'name': self.product_tmpl_id.name,
            'image_1920': self.product_image,
            'product_tmpl_id': self.product_tmpl_id.id,
        })
        return {
            'name': self.product_tmpl_id.name,
            'view_mode': 'form',
            'res_model': 'product.image',
            'type': 'ir.actions.act_window',
            'res_id': dalle_media_image_suggestion_id.id,
            'domain': [('id', '=', self.product_tmpl_id.id)],
            'target': 'current',
        }
