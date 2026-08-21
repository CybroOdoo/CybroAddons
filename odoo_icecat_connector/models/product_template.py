# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies (<https://www.cybrosys.com>).
#    Author: Cybrosys Techno Solutions (<https://www.cybrosys.com>)
#
#    This program is free software: you can modify it under the terms of the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful, but
#    WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

import base64
import requests
from odoo import api, fields, models


class ProductTemplate(models.Model):
    """Inheriting the product template for adding the field for icecat
    product brand and fetching product image"""
    _inherit = 'product.template'

    brand = fields.Char(string="Brand",
                        help="The brand name of product in the icecat")

    def _fetch_icecat_image(self):
        """Fetch high-res product image from Icecat API and assign to image_1920."""
        for product in self:
            if not product.brand or not product.default_code:
                continue
            username = self.env.company.sudo().user_id_icecat
            if not username:
                continue
            url = (
                "https://live.icecat.biz/api?"
                f"UserName={username}&Language=en&Content=&Brand={product.brand}&ProductCode={product.default_code}"
            )
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    res_data = response.json()
                    data = res_data.get('data') if isinstance(res_data, dict) else None
                    if not data or not isinstance(data, dict):
                        continue

                    image_data = data.get('Image')
                    image_url = None
                    if isinstance(image_data, dict):
                        image_url = (
                            image_data.get('HighPic')
                            or image_data.get('Pic500Url')
                            or image_data.get('LowPic')
                            or image_data.get('ThumbPic')
                        )
                    elif isinstance(image_data, str):
                        image_url = image_data

                    if not image_url and isinstance(data.get('GeneralInfo'), dict):
                        image_url = (
                            data['GeneralInfo'].get('HighPic')
                            or data['GeneralInfo'].get('Pic500Url')
                        )

                    if image_url:
                        img_resp = requests.get(image_url, timeout=10)
                        if img_resp.status_code == 200 and img_resp.content:
                            product.image_1920 = base64.b64encode(img_resp.content)
            except Exception:
                pass

    def action_fetch_icecat_image(self):
        """Action method to manually trigger fetching Icecat product image."""
        self._fetch_icecat_image()

    @api.model_create_multi
    def create(self, vals_list):
        templates = super().create(vals_list)
        for template, vals in zip(templates, vals_list):
            if template.brand and template.default_code and ('image_1920' not in vals or not template.image_1920):
                template._fetch_icecat_image()
        return templates

    def write(self, vals):
        res = super().write(vals)
        if 'brand' in vals or 'default_code' in vals:
            for template in self:
                if template.brand and template.default_code and ('image_1920' not in vals or not template.image_1920):
                    template._fetch_icecat_image()
        return res

