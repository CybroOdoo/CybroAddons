# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
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
from odoo import models, fields


class ProductTemplate(models.Model):
    """Extend products with AI image generation metadata and actions."""
    _inherit = 'product.template'

    ai_last_generated_date = fields.Datetime(
        string='Last AI Image Generated',
        readonly=True,
        copy=False,
    )
    ai_generation_count = fields.Integer(
        string='AI Generation Count',
        default=0,
        readonly=True,
        copy=False,
    )

    def action_open_ai_image_wizard(self):
        """Open the AI image generation wizard for this product."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Generate Product Image with AI',
            'res_model': 'smart.product.image.generator',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_product_id': self.id,
            },
        }

    def action_bulk_generate_ai_images(self):
        """Bulk action: open wizard configured for bulk generation."""
        product_ids = self.env.context.get('active_ids', [])
        if not product_ids:
            return

        return {
            'type': 'ir.actions.act_window',
            'name': 'Bulk Generate AI Images',
            'res_model': 'smart.product.image.generator',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_bulk_mode': True,
                'default_bulk_product_ids': [(6, 0, product_ids)],
                'default_product_id': product_ids[0] if product_ids else False,
            },
        }
