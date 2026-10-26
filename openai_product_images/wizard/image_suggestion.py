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
import logging

try:
    import openai
    from openai import OpenAI
except ImportError:
    openai = None
    OpenAI = None

from odoo import api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

MAX_IMAGES = 4
OPENAI_TIMEOUT = 60
OPENAI_MAX_RETRIES = 2


class ImageSuggestion(models.TransientModel):
    """Image generator for product from OpenAI."""
    _name = 'image.suggestion'
    _description = 'Wizard to Generate Product Images Using OpenAI'
    _rec_name = 'product_tmpl_id'

    image_prompt = fields.Char(
        string="Prompt for Image",
        help="Describe the image you want to generate.",
        required=True,
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        string="Product",
        help="Select the product for which image needs to be generated.",
        required=True,
    )
    num_image = fields.Integer(
        string="Number of Images",
        help="Number of images to generate (1 to 4).",
        required=True,
        default=1,
    )
    size_image = fields.Selection(
        [
            ('1024x1024', '1024x1024'),
            ('1024x1536', '1024x1536 (Portrait)'),
            ('1536x1024', '1536x1024 (Landscape)'),
        ],
        string="Resolution",
        help="Resolution of generated images.",
        required=True,
        default='1024x1024',
    )
    quality = fields.Selection(
        [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
        ],
        help="Image quality setting for OpenAI.",
        required=True,
        default='medium',
    )

    @api.constrains('num_image')
    def _check_num_image(self):
        for wizard in self:
            if not 1 <= wizard.num_image <= MAX_IMAGES:
                raise ValidationError(self.env._(
                    "The number of images must be between 1 and %(max)s.",
                    max=MAX_IMAGES))

    def action_generate_images(self):
        """Generate product images from OpenAI and store them in history."""
        self.ensure_one()
        if not OpenAI:
            raise UserError(self.env._(
                "The 'openai' Python library is not installed. "
                "Please install it with 'pip install openai'."))
        # Protected API key is read from system parameters with sudo
        api_key = self.env['ir.config_parameter'].sudo().get_str(
            'openai_api_key')
        if not api_key:
            raise UserError(self.env._(
                "OpenAI API key is not configured. Please set the OpenAI "
                "API key in the General Settings."))
        client = OpenAI(
            api_key=api_key,
            timeout=OPENAI_TIMEOUT,
            max_retries=OPENAI_MAX_RETRIES,
        )
        try:
            response = client.images.generate(
                model="gpt-image-2",
                prompt=self.image_prompt,
                size=self.size_image,
                quality=self.quality,
                n=self.num_image,
            )
        except openai.OpenAIError:
            _logger.exception("OpenAI image generation failed")
            raise UserError(self.env._(
                "The image could not be generated. Please try again later "
                "or contact your administrator."))
        images = [item.b64_json for item in response.data if item.b64_json]
        if not images:
            raise UserError(self.env._(
                "OpenAI did not return any image. Please try again."))
        # Save each image to the history table
        self.env['openai.image.suggestion'].create([{
            'product_image': image_b64,
            'product_tmpl_id': self.product_tmpl_id.id,
        } for image_b64 in images])
        # Set the last generated image as the product main image
        self.product_tmpl_id.write({'image_1920': images[-1]})
        return {'type': 'ir.actions.act_window_close'}
