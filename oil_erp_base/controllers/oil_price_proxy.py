# -*- coding: utf-8 -*-
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
import time

import requests

from odoo import http
from odoo.http import request

import concurrent.futures

_logger = logging.getLogger(__name__)

OIL_PRICE_BASE = "https://query1.finance.yahoo.com/v8/finance/chart"
PRICE_CACHE_TTL = 300
PRICE_CACHE = {}

# Standard benchmark symbol mapping
CODE_MAPPING = {
    "WTI_USD": "CL=F",
    "BRENT_CRUDE_USD": "BZ=F",
    "NATURAL_GAS_USD": "NG=F",
    "GASOLINE_USD": "RB=F",
    "DIESEL_USD": "HO=F",  # Heating Oil proxy
    "HEATING_OIL_USD": "HO=F",
    "JET_FUEL_USD": "HO=F", # Proxy
}


class OilPriceProxyController(http.Controller):
    """Proxy the live market data using high-performance parallel requests."""

    def _fetch_price_single(self, by_code):
        """Internal helper to fetch a single price, usually called in a thread pool."""
        cache_key = by_code.upper()
        symbol = CODE_MAPPING.get(cache_key, cache_key)
        
        cached = PRICE_CACHE.get(cache_key)
        now = time.time()
        if cached and now - cached["ts"] < PRICE_CACHE_TTL:
            return cached["payload"]

        # Use a high-quality User-Agent to ensure stable access
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36'
        }
        
        try:
            response = requests.get(
                f"{OIL_PRICE_BASE}/{symbol}",
                params={'interval': '1m', 'range': '1d'},
                headers=headers,
                timeout=12,
            )
            response.raise_for_status()
            data = response.json()
            
            result = data['chart']['result'][0]
            price = result['meta']['regularMarketPrice']
            ts = result['meta']['regularMarketTime']
            
            payload = {
                "data": {
                    "price": price,
                    "created_at": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime(ts)),
                    "symbol": symbol,
                    "source": "Global Market Feed"
                }
            }
            
            PRICE_CACHE[cache_key] = {
                "ts": now,
                "payload": payload,
            }
            return payload
        except Exception as e:
            _logger.warning("Market feed fetch failed for %s (%s): %s", by_code, symbol, e)
            raise requests.exceptions.RequestException(str(e))

    @http.route('/oil_erp/oil_price_proxy', type='jsonrpc', auth='user')
    def oil_price_proxy(self, by_code):
        """Fetch a single commodity price by code and return it as JSON."""
        config = request.env['ir.config_parameter'].sudo()
        enabled = config.get_param('oil_erp_base.enable_live_oil_api') == 'True'
        if not enabled:
            return {'error': 'Live oil price API is disabled.'}

        try:
            return self._fetch_price_single(by_code)
        except Exception as err:
            return {'error': str(err)}

    @http.route('/oil_erp/oil_price_batch', type='jsonrpc', auth='user')
    def oil_price_batch(self, codes):
        """Fetch all requested commodities in PARALLEL to fix dashboard loading delays."""
        config = request.env['ir.config_parameter'].sudo()
        enabled = config.get_param('oil_erp_base.enable_live_oil_api') == 'True'
        if not enabled:
            return {'error': 'Live oil price API is disabled.'}

        if not codes:
            return {}

        results = {}
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_code = {executor.submit(self._fetch_price_single, code): code for code in codes}
            for future in concurrent.futures.as_completed(future_to_code):
                code = future_to_code[future]
                try:
                    results[code] = future.result()
                except Exception as err:
                    results[code] = {'error': str(err)}
                    
        return results
