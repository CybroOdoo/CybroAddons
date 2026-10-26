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
#############################################################################
from odoo import api, fields, models


class OpenAIImageSuggestion(models.Model):
    """Store AI-generated images for product templates."""
    _name = 'openai.image.suggestion'
    _description = 'AI Generated Product Image'

    product_image = fields.Binary(
        string="Image", attachment=True,
        help="Field to store the generated image.")
    product_tmpl_id = fields.Many2one(
        'product.template', string="Related Product",
        required=True, ondelete='cascade', index=True,
        help="Product associated with this AI-generated image.")

    @api.depends('product_tmpl_id.display_name', 'create_date')
    def _compute_display_name(self):
        for suggestion in self:
            name = (suggestion.product_tmpl_id.display_name
                    or self.env._("AI Image"))
            if suggestion.create_date:
                name = f"{name} ({fields.Datetime.to_string(suggestion.create_date)})"
            suggestion.display_name = name

    def action_set_as_product_image(self):
        """Set the generated image as the product's main image."""
        self.ensure_one()
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

    def action_make_as_product_image(self):
        """Backward compatibility alias for action_set_as_product_image."""
        return self.action_set_as_product_image()
