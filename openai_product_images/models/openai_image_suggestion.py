# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
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


class OpenAIImageSuggestion(models.Model):
    """Store AI-generated images for product templates."""
    _name = 'openai.image.suggestion'
    _description = 'Model For Saving AI Generated Product Images'
    _rec_name = 'product_tmpl_id'

    product_image = fields.Binary('Image', attachment=True,
                                  help="Field to store the generated image")
    product_tmpl_id = fields.Many2one('product.template', 'Related Product',
                                      help="Product associated with this AI-generated image.")

    def action_make_as_product_image(self):
        """Set the generated image as the product's main image."""
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
