# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
from odoo import models, _


class DalleImageSuggestion(models.Model):
    """Extend Dalle Image Suggestion to create product media images from generated OpenAI images."""
    _inherit = 'dalle.image.suggestion'

    def action_make_as_media_image(self):
        """Create product media images from generated DALL·E images."""
        for record in self:
            if not record.product_tmpl_id or not record.product_image:
                continue
            record.env['product.image'].create({
                'name': record.product_tmpl_id.name,
                'image_1920': record.product_image,
                'product_tmpl_id': record.product_tmpl_id.id,
            })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title':  _('Success'),
                'message': _('Product media image created successfully.'),
                'type': 'success',
                'sticky': False,
            }
        }
