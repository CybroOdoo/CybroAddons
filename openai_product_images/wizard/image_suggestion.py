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
import requests
from requests.structures import CaseInsensitiveDict
import json
import base64
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ImageSuggestion(models.TransientModel):
    """image for product from dalle"""
    _name = 'image.suggestion'
    _rec_name = 'product_tmpl_id'
    _description = 'model for creation of dalle image '

    image_prompt = fields.Char(string="Prompt for image",
                               help="field to fill prompt", required=True)
    product_tmpl_id = fields.Many2one('product.template', string="Product",
                                      help="field to store product",
                                      required=True)
    num_image = fields.Integer(string="Number of image needed",
                               help="field to store  number of image",
                               required=True,
                               default=1)
    size_image = fields.Selection(
        [('256x256', '256x256'), ('512x512', '512x512')], string="Resolution",
        help="field to store image size", required=True)

    def action_search(self):
        """Summary:
              Function to search  image suggestion from dalle
           Returns:
               returns the created media image of corresponding product
        """
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'openai_api_key')
        if not api_key:
            raise ValidationError(
                _("Invalid API key provided. Please ensure that you have "
                  "entered the correct API key. "))
        headers = CaseInsensitiveDict()
        headers["Content-Type"] = "application/json"
        headers["Authorization"] = f"Bearer {api_key}"
        data = '{"model": "dall-e-2",' \
               ' "prompt": "' + self.image_prompt + '", "num_images": ' + \
               str(self.num_image) + ', "size": "' \
               + self.size_image + '", "response_format": "url"}'
        resp = requests.post("https://api.openai.com/v1/images/generations",
                             headers=headers, data=data)
        if resp.status_code != 200:
            raise ValidationError("Failed to generate image")
        response_text = json.loads(resp.text)
        for url in response_text['data']:
            image_url = url['url']
            # Get image data and encode it in base64
            image_resp = requests.get(image_url)
            if image_resp.status_code != 200:
                raise ValidationError("Failed to retrieve image")
            image_b64 = base64.b64encode(image_resp.content)
            # Store encoded image as binary field on model
            self.env['dalle.image.suggestion'].create(
                {'product_image': image_b64,
                 'product_tmpl_id': self.product_tmpl_id.id, })
        return {
            'name': self.product_tmpl_id.name,
            'view_mode': 'tree,form',
            'res_model': 'dalle.image.suggestion',
            'type': 'ir.actions.act_window',
            'domain': [('product_tmpl_id', '=', self.product_tmpl_id.id)],
            'target': 'current',
        }
