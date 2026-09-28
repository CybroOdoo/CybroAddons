# -*- coding: utf-8 -*-
#############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2026-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
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

import base64
import logging
import time
import requests

from odoo import models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)
_session = None


class CSCartAPI(models.AbstractModel):
    """
    CS-Cart API Helper Model.

    This abstract model provides a centralized helper for communicating
    with the CS-Cart REST API. It is intended to be reused by all CS-Cart integration
    features such as product, customer, vendor, and order synchronization.
    """

    _name = "cs.cart.api"
    _description = "CS-Cart API Helper"

    def _get_config(self):
        """
        Retrieve CS-Cart API configuration from system parameters or active context.

        :return: Tuple containing (base_url, email, api_key)
        :rtype: tuple(str, str, str)
        :raises UserError: If CS-Cart instance credentials are not defined or incomplete.
        """
        config = False
        config_id = self.env.context.get('cs_cart_config_id') or self.env.context.get('active_id')
        if config_id:
            config = self.env['cs.cart.config'].browse(config_id)

        if not config or not config.exists():
            config = self.env['cs.cart.config'].search([('connected_status', '=', 'connected')], limit=1)

        if not config:
            config = self.env['cs.cart.config'].search([], limit=1)

        if config:
            base_url = config.store_url
            email = config.email
            api_key = config.api_key
        else:
            raise UserError("Please define your store credentials in the CS-Cart Instances menu.")

        if not all([base_url, email, api_key]):
            raise UserError("CS-Cart API is not configured properly.")

        return base_url.rstrip('/'), email, api_key

    def request(self, method, endpoint, params=None, data=None):
        """
        Send an HTTP request to a CS-Cart API endpoint.

        This method:
        - Builds the full API URL using the configured base URL
        - Applies HTTP Basic Authentication using email and API key
        - Sends the request using the specified HTTP method
        - Validates HTTP status codes
        - Parses and returns JSON responses

        :param method: HTTP method ('GET', 'POST', 'PUT', 'DELETE')
        :type method: str
        :param endpoint: CS-Cart API endpoint path
        :type endpoint: str
        :param params: Optional query parameters
        :type params: dict, optional
        :param data: Optional JSON payload data
        :type data: dict, optional
        :return: Response dictionary or empty dictionary
        :rtype: dict
        :raises UserError: If HTTP error status code is returned or response is invalid.
        """
        global _session
        if _session is None:
            _session = requests.Session()

        base_url, email, api_key = self._get_config()
        base_url = base_url.rstrip('/')

        auth_string = f"{email}:{api_key}"
        auth_header = base64.b64encode(auth_string.encode()).decode()

        url = f"{base_url}/api/{endpoint.lstrip('/')}"

        t0 = time.time()
        response = _session.request(
            method,
            url,
            headers={
                "Authorization": f"Basic {auth_header}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
            params=params,
            json=data,
            timeout=30,
        )

        if response.status_code >= 400:
            raise UserError(
                "CS-Cart API Error\n"
                f"URL: {url}\n"
                f"Status: {response.status_code}\n"
                f"Response:\n{response.text}"
            )

        if not response.text or not response.text.strip():
            return {}

        try:
            return response.json()
        except ValueError:
            raise UserError(
                "CS-Cart returned non-JSON response\n"
                f"URL: {url}\n"
                f"Response:\n{response.text[:500]}"
            )

    def get_or_create_company(self, partner):
        """
        Fetch an existing CS-Cart company by partner name or create a new one.

        This method checks whether a company already exists in CS-Cart
        with the given partner's name. If found, it returns the existing
        company ID. If not found, it creates a new company in CS-Cart
        using the partner's basic details and returns the newly created
        company ID.

        :param partner: res.partner record set
        :type partner: res.partner
        :return: CS-Cart company ID
        :rtype: int
        """
        res = self.request(
            "GET",
            "companies",
            params={"company": partner.name}
        )
        companies = res.get("companies", [])
        if companies:
            return companies[0]["company_id"]

        payload = {
            "company": partner.name,
            "email": partner.email,
            "status": "A",
        }

        res = self.request("POST", "companies", data=payload)
        return res["company_id"]
