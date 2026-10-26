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
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class IcecatConnector(http.Controller):
    """Controller for fetching Icecat product details via RPC."""

    @http.route('/get_icecat_product_details', type='jsonrpc', auth="public", website=True, readonly=True)
    def get_icecat_product_details(self, product_id):
        """Returns the details of a product"""
        if not product_id:
            return None
        try:
            product = request.env['product.product'].browse(int(product_id)).exists()
            if not product or not product.website_published:
                return {'status': False}
            website = getattr(request, 'website', None)
            company = (website and website.company_id) or product.company_id or request.env.company
            username = str(company.sudo().user_id_icecat or '')
            brand = product.brand or ''
            product_code = product.default_code or ''
            params = {
                'UserName': username,
                'Language': 'en',
                'Content': '',
                'Brand': brand,
                'ProductCode': product_code,
            }
            response = requests.get('https://live.icecat.biz/api', params=params, timeout=10)
            status = False
            if response.status_code == 200:
                res_data = response.json()
                if isinstance(res_data, dict) and 'data' in res_data:
                    status = True
            return {
                'brand': brand,
                'product_code': product_code,
                'username': username,
                'status': status
            }
        except Exception as e:
            _logger.debug("Failed to retrieve Icecat product details: %s", e)
            return {'status': False}
