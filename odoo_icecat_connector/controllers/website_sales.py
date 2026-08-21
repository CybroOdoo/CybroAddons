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
from odoo.addons.website_sale.controllers.main import WebsiteSale
from odoo.http import request


class Icecat(WebsiteSale):

    def _prepare_product_values(self, product, category, **kwargs):
        """Extend Odoo 19 product values with Icecat info."""

        values = super()._prepare_product_values(product, category, **kwargs)
        username = request.env.company.sudo().user_id_icecat
        if username:
            url = (
                "https://live.icecat.biz/api?"
                f"UserName={username}&Language=en&Content=&Brand={product.brand}&ProductCode={product.default_code}"
            )
            try:
                response = requests.get(url, timeout=5)
                icecat = response.json()

                if icecat.get("data"):
                    values["icecat"] = icecat["data"]
                    if not product.image_1920:
                        try:
                            data = icecat["data"]
                            image_data = data.get('Image') if isinstance(data, dict) else None
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
                                img_resp = requests.get(image_url, timeout=5)
                                if img_resp.status_code == 200 and img_resp.content:
                                    product.sudo().image_1920 = base64.b64encode(img_resp.content)
                        except Exception:
                            pass

            except Exception as e:
                # Avoid breaking website if API fails
                values["icecat_error"] = str(e)
        return values
