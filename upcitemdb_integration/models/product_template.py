# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL-3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL-3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL-3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
# pylint: disable=attribute-defined-outside-init
"""Product template extension for UPCitemdb integration."""
import base64
import logging
import re
import requests
from odoo import api, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    """Inherit product.template to populate product details from UPCitemdb."""
    _inherit = "product.template"

    def _set_upc_category(self, item):
        """Set product category hierarchy from UPC item data."""
        raw_category = item.get('category')
        if not raw_category:
            all_categ = self.env['product.category'].search([('name', '=', 'All')], limit=1)
            self.categ_id = all_categ or self.env['product.category'].search([], limit=1)
            return

        last_elements = [categ.name for categ in self.env['product.category'].search([])]
        categories = []
        category = self.env['product.category']
        for categ_name in raw_category.split(">"):
            categ_name = categ_name.strip()
            if categ_name not in last_elements:
                category = self.env['product.category'].create({
                    'name': categ_name,
                    'parent_id': categories[-1].id if categories else False,
                })
                categories.append(category)
                last_elements.append(categ_name)
            else:
                category = self.env['product.category'].search(
                    [('name', '=', categ_name)], limit=1
                )
                categories.append(category)
        if category:
            self.categ_id = category

    def _set_upc_weight(self, item):
        """Parse and convert weight from UPC item data."""
        raw_weight = item.get('weight')
        if not raw_weight:
            self.weight = 0
            return

        matches = re.findall(r"(\d+(?:\.\d+)?)\s*(\w+)", raw_weight)
        if not matches:
            raise ValidationError(self.env._("Invalid Unit"))

        conversion_factors = {
            'kg': 1, 'g': 0.001, 'mg': 0.000001,
            'lb': 0.453592, 'lbs': 0.453592,
            'pound': 0.453592, 'pounds': 0.453592,
            'oz': 0.0283495, 'ounce': 0.0283495,
        }
        icp = self.env['ir.config_parameter'].sudo()
        weight_in_lbs = (
            icp.get_str('product.weight_in_lbs')
            if hasattr(icp, 'get_str')
            else getattr(icp, 'get_param', lambda k: '')('product.weight_in_lbs')
        )
        if weight_in_lbs == '1':
            conversion_factors.update({
                'lb': 1, 'lbs': 1, 'pound': 1,
                'pounds': 1, 'oz': 16, 'ounce': 16,
                'kg': 0.45359237, 'g': 453.59237,
                'mg': 453592.37,
            })
        unit = matches[0][1].lower()
        if unit in conversion_factors:
            self.weight = float(matches[0][0]) * conversion_factors[unit]
        else:
            raise ValidationError(self.env._("Invalid Unit"))

    def _set_upc_image(self, item):
        """Fetch and set product image from UPC item data."""
        images = item.get('images', [])
        if images:
            image_url = images[0]
            try:
                response = requests.get(image_url, timeout=10)
                if response.status_code == 200 and response.content:
                    image_content = base64.b64encode(response.content)
                    self.image_1920 = image_content.decode('utf-8')
            except requests.RequestException as err:
                _logger.warning("Failed to download image from %s: %s", image_url, err)

    @api.onchange('barcode')
    def _onchange_barcode(self):
        """Create new product by fetching UPC details when scanning barcode."""
        if not self.barcode or len(str(self.barcode)) not in (12, 13):
            return

        product = self.search([('barcode', '=', self.barcode)], limit=1)
        if product:
            raise ValidationError(self.env._("Barcode already exist"))

        url = f'https://api.upcitemdb.com/prod/trial/lookup?upc={self.barcode}'
        try:
            response = requests.get(url, timeout=10)
            data = response.json()
        except (requests.RequestException, ValueError) as err:
            raise ValidationError(self.env._("Invalid UPC")) from err

        if data.get('code') != 'OK' or not data.get('items'):
            raise ValidationError(self.env._("Invalid UPC"))

        item = data['items'][0]
        self.name = item.get('title')
        self.description_sale = item.get('description')
        self.list_price = item.get('highest_recorded_price') or 0.0
        self.default_code = item.get('model')

        if "category" in item:
            self._set_upc_category(item)
        if "weight" in item:
            self._set_upc_weight(item)
        if "images" in item:
            self._set_upc_image(item)
