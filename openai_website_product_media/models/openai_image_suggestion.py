# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Technologies (odoo@cybrosys.com)
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
################################################################################
from odoo import models


class OpenAIImageSuggestion(models.Model):
    """Extend OpenAI Image Suggestion to create product media images."""
    _inherit = 'openai.image.suggestion'

    def action_make_as_media_image(self):
        """Create product media images from generated OpenAI images."""
        created = 0
        for record in self:
            if not record.product_tmpl_id or not record.product_image:
                continue
            record.env['product.image'].create({
                'name': record.product_tmpl_id.name,
                'image_1920': record.product_image,
                'product_tmpl_id': record.product_tmpl_id.id,
            })
            created += 1
        if not created:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': self.env._('Nothing to create'),
                    'message': self.env._('Select an image linked to a product.'),
                    'type': 'warning',
                    'sticky': False,
                },
            }
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': self.env._('Success'),
                'message': self.env._('Product media image created successfully.'),
                'type': 'success',
                'sticky': False,
            },
        }
