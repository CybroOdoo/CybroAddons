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
import requests
from odoo import fields, models
from odoo.tools.binary import BinaryBytes

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    """Inheriting the product template for adding the field for icecat
    product brand and fetching product image"""
    _inherit = 'product.template'

    brand = fields.Char(help="The brand name of product in the icecat")

    def _set_image_from_icecat_data(self, data, timeout=10):
        """Extract and assign product image from Icecat payload data."""
        self.ensure_one()
        if not data or not isinstance(data, dict):
            return
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
            try:
                img_resp = requests.get(image_url, timeout=timeout)
                if img_resp.status_code == 200 and img_resp.content:
                    self.image_1920 = BinaryBytes(img_resp.content)
            except Exception as e:
                _logger.debug("Failed to download or assign Icecat image: %s", e)

    def _fetch_icecat_image(self):
        """Fetch high-res product image from Icecat API and assign to image_1920."""
        for product in self:
            if not product.brand or not product.default_code:
                continue
            company = product.company_id or self.env.company
            username = company.sudo().user_id_icecat
            if not username:
                continue
            params = {
                'UserName': username,
                'Language': 'en',
                'Content': '',
                'Brand': product.brand,
                'ProductCode': product.default_code,
            }
            try:
                response = requests.get('https://live.icecat.biz/api', params=params, timeout=10)
                if response.status_code == 200:
                    res_data = response.json()
                    data = res_data.get('data') if isinstance(res_data, dict) else None
                    if data and isinstance(data, dict):
                        product._set_image_from_icecat_data(data, timeout=10)
            except Exception as e:
                _logger.debug("Failed to fetch product data from Icecat: %s", e)

    def action_fetch_icecat_image(self):
        """Action method to manually trigger fetching Icecat product image."""
        self._fetch_icecat_image()
