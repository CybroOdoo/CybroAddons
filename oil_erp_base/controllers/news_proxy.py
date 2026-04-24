# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
#############################################################################
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
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
import logging

import requests

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

GNEWS_BASE = "https://gnews.io/api/v4"
MAX_NEWS_ARTICLES = 10


class NewsProxyController(http.Controller):
    """
    Proxy GNews API requests through Odoo to avoid exposing the API key
    in the browser and to bypass CORS limitations.
    """

    @http.route('/oil_erp/news_proxy', type='jsonrpc', auth='user')
    def news_proxy(self, endpoint, params=None):
        """Proxy GNews API calls from the dashboard."""
        config = request.env['ir.config_parameter'].sudo()
        api_key = config.get_param(
            'oil_erp_base.news_api_key')
        if not api_key:
            return {'error': 'News API key is not configured.'}

        try:
            url = f"{GNEWS_BASE}/{endpoint}"
            query_params = dict(params or {})
            query_params.setdefault(
                'q',
                config.get_param('oil_erp_base.news_search_query')
                or 'oil OR gas OR energy OR crude'
            )
            query_params.setdefault('lang', 'en')
            query_params.setdefault('country', 'us')
            query_params.setdefault('sortby', 'publishedAt')
            query_params.setdefault('in', 'title,description')
            query_params.setdefault(
                'max',
                config.get_param('oil_erp_base.news_article_limit') or '8'
            )
            query_params['max'] = min(max(int(query_params.get('max') or 1), 1), MAX_NEWS_ARTICLES)
            query_params['apikey'] = api_key
            response = requests.get(url, params=query_params, timeout=15)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as err:
            _logger.warning("News API request failed for %s: %s", endpoint, err)
            return {'error': str(err)}
