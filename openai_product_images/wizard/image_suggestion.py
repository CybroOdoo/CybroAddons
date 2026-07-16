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
from openai import OpenAI
from odoo import fields, models
from odoo.tools.translate import _
from odoo.exceptions import UserError


class ImageSuggestion(models.TransientModel):
    """Image generator for product from OpenAI"""
    _name = 'image.suggestion'
    _description = 'Model For Creation Of Product Images Using OpenAI'
    _rec_name = 'product_tmpl_id'

    image_prompt = fields.Char(
        string="Prompt for Image",
        help="Describe the image you want to generate",
        required=True
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        string="Product",
        help="Select the product for which image needs to be generated",
        required=True
    )
    num_image = fields.Integer(
        string="Number of Images",
        help="Number of images to generate",
        required=True,
        default=1
    )
    size_image = fields.Selection(
        [
            ('1024x1024', '1024x1024'),
            ('1024x1536', '1024x1536 (Portrait)'),
            ('1536x1024', '1536x1024 (Landscape)')
        ],
        string="Resolution",
        help="Resolution of generated images",
        required=True,
        default='1024x1024'
    )
    quality = fields.Selection(
        [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High')
        ],
        string="Quality",
        help="Image quality setting for OpenAI",
        required=True,
        default='medium'
    )

    def action_generate_images(self):
        """Generate product images from OpenAI"""
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'openai_api_key')

        if not api_key:
            raise UserError(_("OpenAI API key is not configured. Please set OpenAI API key in configuration settings."))

        client = OpenAI(api_key=api_key)

        total_images = self.num_image or 1

        try:
            last_image_b64 = False

            for i in range(total_images):
                response = client.images.generate(
                    model="gpt-image-2",
                    prompt=self.image_prompt,
                    size=self.size_image,
                    quality=self.quality,
                    n=1,
                )
                image_b64_encoded = response.data[0].b64_json.encode('utf-8')
                last_image_b64 = image_b64_encoded

                # Save each image to history table
                self.env['openai.image.suggestion'].create({
                    'product_image': image_b64_encoded,
                    'product_tmpl_id': self.product_tmpl_id.id,
                })

            # Optionally set last generated image as product main image
            if last_image_b64:
                self.product_tmpl_id.write({'image_1920': last_image_b64})

            return {'type': 'ir.actions.act_window_close'}

        except Exception as e:
            raise UserError(f"Error generating image: {str(e)}")
