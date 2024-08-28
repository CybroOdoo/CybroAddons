# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Ayana KP (Contact : odoo@cybrosys.com)
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
import re
import requests
from odoo import api, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    """Inherited the module for to add function for create new product."""
    _inherit = "product.template"

    @api.onchange('barcode')
    def _onchange_barcode(self):
        """Onchange function for create new product by passing UPC code given
        in barcode field, the given barcode pass to url and get the response
        at the endpoint. Using the response we create new product details.."""
        if self.barcode and ((len(str(self.barcode)) == 13) or (
                len(str(self.barcode)) == 12)):
            product = self.search([('barcode', '=', self.barcode)], limit=1)
            if product:
                raise ValidationError(
                    _("Barcode already exist"))
            else:
                url = f'https://api.upcitemdb.com/prod/trial/lookup?upc=' \
                      f'{self.barcode}'
                response = requests.get(url)
                if "code" in response.json():
                    if response.json()['code'] == 'OK' and \
                            "items" in response.json():
                        self.name = response.json()['items'][0].get('title')
                        self.description_sale = response.json()['items'][0]. \
                            get('description')
                        self.list_price = response.json()['items'][0]. \
                            get('highest_recorded_price')
                        self.default_code = response.json()['items'][0]. \
                            get('model')
                        if "category" in response.json()['items'][0]:
                            if not response.json()['items'][0]['category']:
                                self.categ_id = self.env[
                                    'product.category'].search(
                                    [('name', '=', 'All')], limit=1).id
                            else:
                                last_elements = [categ.name for categ in
                                                 self.env['product.category'].
                                                 search([])]
                                categories = []
                                category = 'category'
                                for categ in response.json()['items'][0][
                                    'category'].split(">"):
                                    if categ not in last_elements:
                                        category = self.env[
                                            'product.category'].create({
                                            'name': categ,
                                            'parent_id': categories[
                                                -1].id if categories else False,
                                        })
                                        categories.append(category)
                                        category = categories[-1]
                                    else:
                                        category = self.env[
                                            'product.category'].search(
                                            [('name', '=', categ)], limit=1).id
                                self.categ_id = category
                        if "weight" in response.json()['items'][0]:
                            if not response.json()['items'][0]['weight']:
                                self.weight = 0
                            else:
                                matches = re.findall(r"(\d+(?:\.\d+)?)\s*(\w+)",
                                                     response.json()['items'][
                                                         0]['weight'])
                                conversion_factors = {
                                    'kg': 1, 'g': 0.001, 'mg': 0.000001,
                                    'lb': 0.453592, 'lbs': 0.453592,
                                    'pound': 0.453592, 'pounds': 0.453592,
                                    'oz': 0.0283495, 'ounce': 0.0283495,
                                }
                                product_weight_in_lbs_param = self.env[
                                    'ir.config_parameter'].sudo().get_param(
                                    'product.weight_in_lbs')
                                if product_weight_in_lbs_param == '1':
                                    conversion_factors.update({
                                        'lb': 1, 'lbs': 1, 'pound': 1,
                                        'pounds': 1, 'oz': 16, 'ounce': 16,
                                        'kg': 0.45359237, 'g': 453.59237,
                                        'mg': 453592.37,
                                    })
                                if matches[0][1].lower() in conversion_factors:
                                    self.weight = float(matches[0][0]) * \
                                                  conversion_factors[
                                                      matches[0][1].lower()]
                                else:
                                    raise ValidationError(
                                        _("Invalid Unit"))
                        if "currency" in response.json()['items'][0]:
                            if not response.json()['items'][0]['currency']:
                                self.currency_id = self.env[
                                    'res.currency'].search(
                                    [('name', '=', 'USD')], limit=1).id
                            else:
                                self.currency_id = self.env[
                                    'res.currency'].search([('name', '=',
                                                             response.json()[
                                                                 'items'][0][
                                                                 'currency'])],
                                                           limit=1).id
                        if "images" in response.json()['items'][0]:
                            if response.json()['items'][0]['images']:
                                url = response.json()['items'][0]['images'][0]
                                response = requests.get(url)
                                image_content = base64.b64encode(
                                    response.content)
                                self.image_1920 = image_content.decode(
                                    'utf-8')
                    else:
                        raise ValidationError(
                            _("Invalid UPC"))
