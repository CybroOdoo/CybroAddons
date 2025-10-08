# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
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
#############################################################################
import base64
import requests
from openai import OpenAI
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_create_image = fields.Boolean(string='Generate Image',
                                     default=True,
                                     help='Check this box if you want to automatically generate an image for this product')

    is_update_image = fields.Boolean(string='Update Image',
                                     help='Check this box if you want to automatically update an image for this product while changing the name.')

    @api.model
    def create(self, vals):
        """ Method for generating images for product """
        res = super(ProductTemplate, self).create(vals)
        if not res.image_1920 and res.is_create_image:
            image_base64 = self.generate_image(res.name)
            if image_base64:
                res.write({
                    'image_1920': image_base64,
                })
            else:
                res.message_post(
                    body="Failed to generate image for product: '%s' due to 'Incorrect API key provided or Other issues. You can find your API key at https://platform.openai.com/account/api-keys." % res.name,
                    message_type='notification')
        return res

    def write(self, vals):
        """ Method for updating image if name of the product updates"""
        if 'name' in vals and 'image_1920' not in vals:
            is_update_image = vals.get('is_update_image', self.is_update_image)
            if is_update_image:
                image_base64 = self.generate_image(vals['name'])
                if image_base64:
                    vals['image_1920'] = image_base64
                else:
                    self.message_post(
                        body="Failed to update image for product: '%s' due to 'Incorrect API key provided or Other issues. You can find your API key at https://platform.openai.com/account/api-keys." %
                             vals['name'],
                        message_type='notification')
        return super(ProductTemplate, self).write(vals)

    def generate_image(self, name):
        """ Function for generating images with the help of AI based on the name
        of the product"""
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'chatgpt_odoo_connector.api_key')
        client = OpenAI(api_key=api_key)
        try:
            response = client.images.generate(
                model="dall-e-3",
                prompt=name,
                size="1024x1024",
                quality="standard",
                n=1,
            )
            image_url = response.data[0].url
            response = requests.get(image_url)
            image_base64 = base64.b64encode(response.content)
        except:
            return None
        return image_base64
