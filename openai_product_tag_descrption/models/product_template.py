# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: Mohammed Dilshad Tk (odoo@cybrosys.com)
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
from odoo import fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    """Inherit product template to add field of product tags and functions to
        create description and tags."""
    _inherit = 'product.template'

    product_tag_ids = fields.Many2many('product.tag', string="Product Tags",
                                       help="Tags For Product")

    def action_create_tag_description(self):
        """Summary:
                    Function to create tags from description
              """
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'openai_api_key')
        if not api_key:
            raise ValidationError(_("Provide an API key in the settings"))
        product = self.env['product.template'].browse(self._context['active_id'])
        tags_list = []
        if product.description:
            prompt = "Generate tags for the following description: \n" + str(
                product.description) + "\n\nTags:"
            try:
                response = requests.post \
                    ("https://api.openai.com/v1/engines/text-davinci-002"
                     "/completions",
                     headers={
                         "Content-Type": "application/json",
                         "Authorization": f"Bearer {api_key}"
                     },
                     json={
                         "prompt": prompt,
                         "max_tokens": 60,
                         "n": 1,
                         "stop": None,
                         "temperature": 0.5
                     })
            except Exception:
                raise ValidationError(
                    _("Connection Failed"))
            if str(response) == '<Response [401]>':
                raise ValidationError(
                    _("Access denied. Please ensure you have valid "
                      "credentials and try again."))
            elif str(response) == '<Response [429]>' and not \
                    response.json()['error']['message'] == ('You exceeded your '
                                'current quota, please check your plan and '
                                                            'billing details.'):
                raise ValidationError(
                    _("Sorry, Openai currently experiencing high traffic. "
                      "Please wait a moment and try again."))
            elif str(response) == '<Response [429]>' and \
                    response.json()['error'][
                        'message'] == ('You exceeded your current quota, '
                                       'please check your plan and billing '
                                       'details.'):
                raise ValidationError(_("'You exceeded your current quota, "
                        "please check your plan and billing details.'"))
            else:
                tags = response.json()["choices"][0]["text"].split(",")
                tags = [tag.strip() for tag in tags]
                tags_list.extend(tags)
                tags_exists = self.env['product.tag'].search([]).mapped('name')
                for tag in tags_list:
                    if tag not in tags_exists:
                        tag_created = self.env['product.tag'].create({
                            'name': tag})
                        product.write({
                            'product_tag_ids': [(4, tag_created.id)]
                        })
                    else:
                        tags_exist = self.env['product.tag'].search(
                            [('name', '=', tag)])
                        for tag_apply in tags_exist:
                            product.write({
                                'product_tag_ids': [(4, tag_apply.id)]
                            })
        else:
            raise ValidationError(_("No description for this product"))

    def generate_description_from_tags(self):
        """Summary:
            Function to create description from tags
        """
        prompt = "Generate a description for a product based on" \
                 " the following tags: \n"
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'openai_api_key')
        if not api_key:
            raise ValidationError(_("Provide an API key in the settings"))
        product = self.env['product.template'].browse(self._context['active_id'])
        if product.product_tag_ids:
            for tag in product.product_tag_ids:
                prompt += f"- {tag}\n"
            prompt += "\nDescription:"
            try:
                response = requests.post(
                    "https://api.openai.com/v1/engines/text-davinci-002"
                    "/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}"
                    },
                    json={
                        "prompt": prompt,
                        "max_tokens": 200,
                        "n": 1,
                        "stop": None,
                        "temperature": 0.5
                    })
            except Exception:
                raise ValidationError(_("Connection Failed"))
            if str(response) == '<Response [401]>':
                raise ValidationError(_("Access denied. Please ensure you "
                                "have valid credentials and try again."))
            elif str(response) == '<Response [429]>' and not \
                    response.json()['error']['message'] == ('You exceeded your '
                            'current quota, please check your plan and billing '
                                                            'details.'):
                raise ValidationError(_("Sorry, Openai currently experiencing "
                        "high traffic. Please wait a moment and try again."))
            elif str(response) == '<Response [429]>' and \
                    response.json()['error'][
                        'message'] == ('You exceeded your current quota, '
                                       'please check your plan and billing '
                                       'details.'):
                raise ValidationError(_("'You exceeded your current quota, "
                            "please check your plan and billing details.'"))
            else:
                description = response.json()["choices"][0]["text"].split('\n')
                product.description = description[-1]
        else:
            raise ValidationError(_("No tags for this product"))
