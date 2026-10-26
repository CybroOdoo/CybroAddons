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
from odoo import models
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    """
    Extend the Product Template model to add actions for
    generating and viewing AI-generated product images.
    """
    _inherit = 'product.template'

    def action_open_image_prompt_wizard(self):
        """Open wizard to generate an AI image for the product."""
        if len(self) != 1:
            raise UserError(self.env._(
                "Please select exactly one product to generate an image."))
        return {
            'name': self.env._("Generate AI Image"),
            'view_mode': 'form',
            'res_model': 'image.suggestion',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_product_tmpl_id': self.id},
        }

    def action_view_ai_images(self):
        """Open AI generated images related to the product."""
        self.ensure_one()
        return {
            'name': self.env._("AI Images"),
            'view_mode': 'list,form',
            'res_model': 'openai.image.suggestion',
            'type': 'ir.actions.act_window',
            'domain': [('product_tmpl_id', '=', self.id)],
            'context': {'default_product_tmpl_id': self.id},
        }
