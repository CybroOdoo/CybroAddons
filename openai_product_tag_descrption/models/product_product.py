"""Tag creation from description and description creation from tags"""
# -*- coding: utf-8 -*-
################################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>).
#    Author: LAJINA K V (odoo@cybrosys.com)
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


class ProductProduct(models.Model):
    """Inherit ProductProduct model """
    _inherit = 'product.product'

    product_tag_ids = fields.Many2many('product.tag', string="Product Tags",
                                       related='product_tmpl_id.product_tag_ids',
                                       readonly=False, help="Tags For Product")

    def action_create_tag_internal_note(self):
        """Summary:
                    Function to create tags from Internal notes
              """
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'openai_api_key')
        if not api_key:
            raise ValidationError("Please Enter  Valid Open AI Key")
        product_id = self._context['active_id']
        product = self.env['product.product'].browse(product_id)
        tags_list = []
        if product.description:
            prompt = "Generate tags for the following description: \n" + str(
                product.description) + "\n\nTags:"
            response = requests.post(
                "https://api.openai.com/v1/engines/text-davinci-002/completions",
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
                }
            )
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
            raise ValidationError(
                _("No description for this product"))

    def generate_internal_notes_from_tags(self):
        """Summary:
                           Function to create Internal notes from tags
                     """
        prompt = "Generate a description for a product based on " \
                 "the following tags: \n"
        api_key = self.env['ir.config_parameter'].sudo().get_param(
            'openai_api_key')
        product_id = self._context['active_id']
        product = self.env['product.product'].browse(product_id)
        if product.product_tag_ids:
            for tag in product.product_tag_ids:
                prompt += f"- {tag}\n"
            prompt += "\nDescription:"

            response = requests.post(
                "https://api.openai.com/v1/engines/text-davinci-002/completions"
                ,
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
                }
            )
            description = response.json()["choices"][0]["text"].split('\n')
            product.description = description[-1]
        else:
            raise ValidationError(
                _("No tags for this product"))
