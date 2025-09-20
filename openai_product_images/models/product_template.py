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
from odoo import models


class ProductTemplate(models.Model):
    """To write function for product template buttons """

    _inherit = 'product.template'

    def action_open_image_prompt_wizard(self):
        """Summary:
              Function to view  image suggestion
           Returns:
               returns the  image of corresponding product
        """
        return {
            'name': self.name,
            'view_mode': 'form',
            'res_model': 'image.suggestion',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_product_tmpl_id': self.id},
        }

    def get_dall_e_image(self):
        """Summary:
              Function to view  dalle  image suggestion
           Returns:
               returns the created  image of corresponding product
        """
        return {
            'name': self.name,
            'view_mode': 'tree,form',
            'res_model': 'dalle.image.suggestion',
            'type': 'ir.actions.act_window',
            'domain': [('product_tmpl_id', '=', self.id)],
        }
