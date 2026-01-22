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
from odoo import fields, models, _
from odoo.exceptions import UserError, ValidationError
from urllib.request import urlopen
from openai import OpenAI
import base64


class ImageSuggestion(models.TransientModel):
    """Image generator for product from OpenAI DALL·E 3"""
    _name = 'image.suggestion'
    _rec_name = 'product_tmpl_id'
    _description = 'Model for creation of product images using DALL·E'

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
            ('1024x1792', '1024x1792 (Portrait)'),
            ('1792x1024', '1792x1024 (Landscape)')
        ],
        string="Resolution",
        help="Resolution of generated images",
        required=True,
        default='1024x1024'
    )
    quality = fields.Selection(
        [
            ('standard', 'Standard'),
            ('hd', 'High Definition')
        ],
        string="Quality",
        help="Image quality setting for DALL·E 3",
        required=True,
        default='standard'
    )

    def action_search(self):
        """Generate product images from OpenAI DALL·E 3"""
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'openai_api_key')
        client = OpenAI(api_key=api_key)

        # Safety — default to 1
        total_images = self.num_image or 1

        try:
            last_image_b64 = False

            for i in range(total_images):
                response = client.images.generate(
                    model="dall-e-3",
                    prompt=self.image_prompt,
                    size=self.size_image,
                    quality=self.quality,
                    n=1,  # DALL·E 3 rule
                )

                # Get image URL
                image_url = response.data[0].url
                image_content = urlopen(image_url).read()
                image_b64_encoded = base64.b64encode(image_content)

                last_image_b64 = image_b64_encoded

                # Save each image to history table
                self.env['dalle.image.suggestion'].create({
                    'product_image': image_b64_encoded,
                    'product_tmpl_id': self.product_tmpl_id.id,
                })

            # Optionally set last generated image as product main image
            if last_image_b64:
                self.product_tmpl_id.write({'image_1920': last_image_b64})

            return {'type': 'ir.actions.act_window_close'}

        except Exception as e:
            raise UserError(f"Error generating image: {str(e)}")
